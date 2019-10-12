
class bestReportController(object):

    def __init__(self):
        self.initData()
        self.initConnect()
    
    def initData(self):
        pass

    def initConnect(self):
        pass 
        
    def actionBestReport(self, reportDir , job):
        writeFile(os.sep.join([reportDir, '%s.json' % job.reportName()]), json.dumps(job.json(), indent = 4))
        BestPDF = self.tpseReport.makeSimpleReport(job.result(), reportDir , "%s.pdf" % job.reportName())
        if BestPDF:
            logger.info(u"最好结果标准报告【%s】生成成功！" % BestPDF)
            BestPDFPng = TPSEReport.pdf2Png(BestPDF, self.paths["BestReport"], job.reportName())
            logger.info(u"最好结果标准报告转换图片【%s】成功！" % BestPDFPng)
            self.dingding.sendmsg(self.config["dingdingUrl"],toPicbed(self.config['mapBedUrl'], BestPDFPng))
            logger.info(u"最好结果标准报告【%s】发送钉钉成功！" % BestPDFPng)

class TwoHouerTradeResultJob(object):

    Jobs = []

    ValidRules = {
        "BrokerVolume": 3,
        "CustomerPosition": 3,
        "MarketFeed": 2,
        "MarketWatch": 3,
        "SecurityDetail": 3,
        "TradeLookup": 3,
        "TradeOrder": 2,
        "TradeResult": 2,
        "TradeStatus": 1,
        "TradeUpdate": 3
    }

    BestJob = None

    def __init__(self, index):
        super(TwoHouerTradeResultJob, self).__init__()
        self._id = index
        self._result = {}
        self._isResultValid = False
        self._tpsE = 0
        self._stdTpsE = 0
        self._rampuptime = 0
        self._rampdowntime = 0


    @classmethod
    def addJob(cls, job):
        cls.Jobs.append(job)

    @classmethod
    def getBestResult(cls):
        bestJob = None
        maxTpSE = 0
        logger.info(cls.Jobs)
        for job in cls.Jobs:

            logger.info(job)
            logger.info(job.isResultValid())
            logger.info(job.isTpsEValid())
            logger.info("job.MIStart() = %d" % job.MIStart())
            logger.info("job.rampuptime() = %d" % job.rampuptime())
            if job.isResultValid() and job.isTpsEValid() and job.MIStart() > job.rampuptime():
                logger.info(job)
                if job.tpsE() > maxTpSE:
                    maxTpSE = job.tpsE()
                    bestJob = job

        return bestJob

    def __str__(self):
        return "MIStart = %d, MIEnd = %d, tpsE=%s" % (self.id() - MeasureInterval, self.id(), self.tpsE())

    def MIStart(self):
        return self.id() - MeasureInterval

    def MIEnd(self):
        return self.id()

    def rampuptime(self):
        return self._rampuptime

    def rampdowntime(self):
        return self._rampdowntime

    def reportName(self):
        return "%d-%d(%s)" % (self.MIStart(), self.MIEnd(), str(self.tpsE()))

    def json(self):
        return {
            "MIStart": self.MIStart(),
            "MIEnd": self.MIEnd(),
            "tpsE": self.tpsE(),
            "RAMPUPTIME": self.rampuptime(),
            "RAMPDOWNTIME": self.rampdowntime(),
            "result": self.result()
        }

    def loadResult(self, path):
        with open(path, "r") as f:
            self._result  = json.load(f)

    def getResult(self, ip, port, startTpceArgs, resultDir):
        logger.info(u"获取【MeasureInterval = %d】结果" % self._id)

        url = "http://%s:%d/api/v1/tpce/result"  % (ip, port)

        args = copy.deepcopy(startTpceArgs)


        self._stdTpsE = float(args["customer"] / args["scalefactor"])

        args["MIStart"] = self._id - MeasureInterval
        args["MIEnd"] = self._id

        # args["MIStart"] = 0
        # args["MIEnd"] = 0

        r = requests.post(url,json.dumps(args))
        logger.info(json.dumps(r.json(),indent = 4))

        self._result = r.json()

        with open(os.sep.join([resultDir, '%d.json' % self._id]), 'w') as f:
            f.write(json.dumps(r.json(),indent = 4))

        self.handleResult()
        self.computerBestJob()

    def handleResult(self):
        self._isResultValid = self.validResult()
        self._tpsE = self.computerTpsE()

        if self._isResultValid:
            self._result["result"]["tpsE"] = self._tpsE

            self._rampuptime, self._rampdowntime = self.computerRampuptime()
            self._result["result"]["RAMPUPTIME"] = secondsToTime(self._rampuptime * 60)
            self._result["result"]["RAMPDownTIME"] = secondsToTime(self._rampdowntime * 60)
            self._result["result"]["MEASUREMENTINTERVAL"] = secondsToTime(MeasureInterval * 60)

        logger.info(u"[%d]分钟结果[%f]有效：[%s]" % (self._id, self.tpsE(), str(self.isResultValid())))

    def computerBestJob(self):
        if len(self.Jobs) > 1:
            TwoHouerTradeResultJob.BestJob = self.getBestResult()
            if TwoHouerTradeResultJob.BestJob:
                logger.info("===========================")
                logger.info(TwoHouerTradeResultJob.BestJob)
                logger.info([job.tpsE() for job in TwoHouerTradeResultJob.Jobs])
                logger.info([job.isTpsEValid() for job in TwoHouerTradeResultJob.Jobs])
                logger.info([job.isResultValid() for job in TwoHouerTradeResultJob.Jobs])

    def id(self):
        return self._id

    def result(self):
        return self._result

    def tpsE(self):
        return self._tpsE

    def isResultValid(self):
        return self._isResultValid

    def stdTpsE(self):
        return self._stdTpsE

    def validResult(self):
        ret = False
        if "retcode" in self._result and self._result["retcode"] == 0:
            TEST_DATA = self._result["result"]["TEST_DATA"]
            isValid = True
            for item in TEST_DATA:
                if item["T_NAME"] != "DataMaintenance":
                    isValid = isValid and (float(item["T_90"]) < self.ValidRules[item["T_NAME"]])
            ret = isValid
        return ret

    def isTpsEValid(self):
        if self.tpsE() > 0.8 * self.stdTpsE() and self.tpsE() < self.stdTpsE() * 1.02:
            return True
        return False

    def computerTpsE(self):
        if "retcode" in self._result and self._result["retcode"] == 0:
            TEST_DATA = self._result["result"]["TEST_DATA"]
            tpsE = float(TEST_DATA[7]["T_COUNT"]) / (MeasureInterval * 60)
            return tpsE
        return 0

    @classmethod
    def getTradeResultsPerMintue(cls, tradeResults):
        tpsEs = []
        tpsEs.append(0)
        for i in range(0, len(tradeResults)):
            if i == 0:
                tpsEs.append(tradeResults[i] / 60.0)
            else:
                tpsEs.append((tradeResults[i] - tradeResults[i-1]) / 60.0)
        return tpsEs

    def computerRampuptime(self, window=10, step=1):
        # tradeResults = self._result["result"]["TradeResult"]
        # startIndex = 0
        # endIndex = 0
        # if len(tradeResults) > MeasureInterval:

        #     window = 60
        #     step = 10
        #     tpsEs_6010 = []
        #     tpsEs_1001 = []
        #     for i in range(0, len(tradeResults) - 1, step):
        #         if (i+window + 1) < len(tradeResults):
        #             tpsEs_6010.append((tradeResults[i+window + 1] - tradeResults[i + 1]) / (60.0 * window))

        #     valid6010 = [ (t >= 0.98 * self.stdTpsE() and t <= 1.02 * self.stdTpsE())  for t in tpsEs_6010 ]

        #     best6010StartIndex, best6010EndIndex = self.getBestStartEnd(valid6010)
        #     logger.info(best6010StartIndex)
        #     logger.info(best6010EndIndex)

        #     best6010StartIndex = best6010StartIndex *  step + 1
        #     best6010EndIndex = best6010EndIndex *  step + 1

        #     logger.info(tpsEs_6010)
        #     logger.info(valid6010)
        #     logger.info(best6010StartIndex)

        #     window = 10
        #     step = 1
        #     for i in range(0, len(tradeResults) - 1, 1):
        #         if (i+window + 1) < len(tradeResults):
        #             tpsEs_1001.append((tradeResults[i+window + 1] - tradeResults[i + 1]) / (60.0 * window))

        #     valid1001 = [ (t >= 0.8 * self.stdTpsE() and t <= 1.20 * self.stdTpsE())  for t in tpsEs_1001 ]

        #     best1001StartIndex, best1001EndIndex = self.getBestStartEnd(valid1001)
        #     logger.info(tpsEs_1001)
        #     logger.info(valid1001)
        #     logger.info(best1001StartIndex)

        #     startIndex = max([best6010StartIndex, best1001StartIndex])
        #     endIndex = min([best6010EndIndex, best1001EndIndex])

        #         ret1 = ((sum(tpsEs[i+1: i+window+1]) / window) >  0.98 * self.stdTpsE()  and (sum(tpsEs[i+1: i+window+1]) / window) <  1.02 * self.stdTpsE())
        #         ret2 = ((sum(tpsEs[i+window+1: i+2*window+1]) / window) >  0.98 * self.stdTpsE()  and (sum(tpsEs[i+window+1: i+2*window+1]) / window) <  1.02 * self.stdTpsE())
        #         ret3 = ((sum(tpsEs[i+2*window+1: i+3*window+1]) / window) >  0.98 * self.stdTpsE()  and (sum(tpsEs[i+2*window+1: i+3*window+1]) / window) <  1.02 * self.stdTpsE())
        #         if ret1 and ret2 and ret3:
        #             tindex = i + 3 * window
        #             break
        # return startIndex, endIndex

        tpsEs = self.getTradeResultsPerMintue(self._result["result"]["TradeResult"])
        startIndex = 0
        endIndex = 0
        if len(tpsEs) > MeasureInterval:
            for i in range(0, len(tpsEs)):
                ret1 = ((sum(tpsEs[i+1: i+window+1]) / window) >  0.8 * self.stdTpsE()  and (sum(tpsEs[i+1: i+window+1]) / window) <  1.02 * self.stdTpsE())
                if ((i+1) < len(tpsEs)) and tpsEs[i] < 0.8 * self.stdTpsE() and tpsEs[i+1] > 0.8 * self.stdTpsE() and ret1:
                    startIndex = i + window
                    break
        return startIndex, startIndex + MeasureInterval + 10

    @classmethod
    def getBestStartEnd(cls, rets):
        bestStartIndex = 0
        bestEndIndex = 0
        startIndex = 0
        endIndex = 0
        count = 0

        if rets.count(False) == 0:
            bestStartIndex = 0
            bestEndIndex = len(rets)
        elif rets.count(False) == 1:
            index = rets.index(False)
            if len(rets[0: index]) > len(rets[index+1: -1]):
                bestStartIndex = 0
                bestEndIndex = index
            else:
                bestStartIndex = index+1
                bestEndIndex =  len(rets)
        else:

            bestEndIndex = rets[endIndex:-1].index(False) + 1
            count = len(rets[bestStartIndex:bestEndIndex])

            for i in range(0, len(rets)):
                if False in rets[endIndex:-1]:
                    startIndex = endIndex + rets[endIndex:-1].index(False) + 1
                    if False in  rets[startIndex: -1]:
                        endIndex = startIndex + rets[startIndex: -1].index(False)
                        if len(rets[startIndex:endIndex]) >= count:
                            count = len(rets[startIndex:endIndex])
                            bestStartIndex = startIndex
                            bestEndIndex = endIndex
        return bestStartIndex, bestEndIndex

    @classmethod
    def check6010window(cls, job):
        tpsEs = self.getTradeResultsPerMintue(job.result()["result"]["TradeResult"])


    @classmethod
    def check1001window(cls, job):
        pass