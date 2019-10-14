#!/usr/bin/env python
# -*- coding: utf_8 -*-
import os
import sys

'''
def isYuandianOS():
    os_release = "/etc/os-release"
    if os.path.exists(os_release):
        content = ""
        with open(os_release, "rb") as f:
            content = f.read()
        lines = content.split("\n")
        if lines[0].split("=")[1][1:-1] == "Origin" and lines[1].split("=")[1][1:-1] == "1.0.0 (pangu)":
            return True
    return False

print(isYuandianOS())
if sys.platform == "win32":
    if sys.version_info > (3, 0):
        path=sys.executable
        sys.path.insert(0, os.sep.join([path[0:path.rfind(os.sep)], 'Lib']))
        sys.path.insert(1, os.sep.join([os.getcwd(),'packages', "py3-win-site-packages"]))
    else:
        reload(sys)
        sys.setdefaultencoding("utf-8")
        sys.path.insert(0, os.sep.join([os.getcwd(),'packages',"py2-win-site-packages"]))
    pass
else:
    if sys.version_info < (3, 0):
        if isYuandianOS():
            package =  os.sep.join([os.getcwd(),'packages',"py2-yuandian-site-packages"])
            os.environ["MATPLOTLIBDATA"] = os.sep.join([package, 'matplotlib', "matplotlib", "mpl-data"])
            print(os.environ["MATPLOTLIBDATA"])
            print(os.path.exists(os.environ["MATPLOTLIBDATA"]))
            sys.path.insert(0, package)
        else:
            sys.path.insert(0, os.sep.join([os.getcwd(),'packages',"py2-site-packages"]))
    else:
        sys.path.insert(0, os.sep.join([os.getcwd(),'packages',"py3-site-packages"]))
print(sys.path)'''
import time
import datetime
import json
from threading import Thread
import signal
import requests

import base64
from reportbro import Report
from pdf2image import convert_from_path

import logging
from logging.handlers import RotatingFileHandler
import traceback
import copy
import subprocess
from app import signalManager

logPath  =  os.getcwd() + os.path.sep + "logs"
if not os.path.exists(logPath):
    os.makedirs(logPath)

fh  =  RotatingFileHandler("logs/TPCEAutoRunner.log", maxBytes = 10 * 1024 * 1024, backupCount = 100)
fh.setLevel(logging.DEBUG)
#log write in console
ch  =  logging.StreamHandler()
ch.setLevel(logging.DEBUG)
#log formatter
formatter  =  logging.Formatter(
    '%(asctime)s %(levelname)8s [%(filename)25s%(funcName)20s%(lineno)06s] %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger  =  logging.root
logger.setLevel(logging.INFO)
logger.addHandler(fh)
logger.addHandler(ch)


def timeToSeconds(t, sep=":"):
    if t == "":
        t = "0:0:0"
    ts =[int(i) for i in t.split(sep)]
    return ts[0] * 60 * 60 + ts[1] * 60 + ts[2]

def secondsToTime(seconds, sep=":"):
    logger.info(seconds)
    logger.info(type(seconds))
    h  = seconds / 3600
    m  = seconds % 3600 / 60
    s = (seconds - h * 3600 - m * 60) % 60

    return sep.join([str(i) for i in [h, m, s]])

def load(fname):
    filename = fname
    with open(filename, "r") as f:
        load_data = json.loads(f.read())
        return load_data

def toBase64(fpath):
    with open(fpath,'rb') as f:
        base64_data  =  base64.b64encode(f.read())
        s  =  base64_data.decode()
        logger.info('%s to base64 successed!'%fpath)
    return "data:image/jpeg;base64,"+str(s)

def writeFile(fpath, result):
    with open(fpath, 'w') as f:
        f.write(result)

def toPicbed(mapBedUrl,fpath):
    upload_url = mapBedUrl
    files =  {"image001":open(fpath, "rb")}
    ru  =  requests.post(upload_url, files = files)
    mapUrl = ru.text
    logger.info(mapUrl)
    return mapUrl


is_exit = False
MeasureInterval = 120

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


class  Dingding(object):
    def __init__(self):
        pass

    def sendmsg(self,dingdingUrl,mesgpath):
        try:
            for url in dingdingUrl:
                HEADERS  =  {
                    "Content-Type": "application/json;charset=utf-8"
                }
                message  =  mesgpath
                String_textMsg  = {
                     "msgtype": "markdown",
                     "markdown": {
                         "title":"tpce test",
                         "text": "\n" +
                                 "> \n\n" +
                                 "> ![screenshot](%s)\n" % mesgpath  +
                                 "> \n"
                     },
                    "at": {
                        "atMobiles": [
                            "156xxxx8827", 
                            "189xxxx8325"
                        ], 
                        "isAtAll": 1
                    }
                    }
                String_textMsg  =  json.dumps(String_textMsg)
                res  =  requests.post(url, data = String_textMsg, headers = HEADERS)
                logger.info(u"钉钉发送【%s】成功！" % url)
                logger.info(res.json())

        except Exception as e:
            logger.error(traceback.format_exc(e))
            logger.error(u'钉钉发送失败！')
            logger.error(repr(e))


class TPSEReport(object):
    def __init__(self):
        self.config = load('config.json')
        self.startTpceArgs = load('start.json')
        self.testData = load('data.json')

    def setStartTpceArgs(self, startTpceArgs):
        self.startTpceArgs = startTpceArgs

    @classmethod
    def json2Pdf(cls, jsonTemplate, data, output):
        if os.path.exists(jsonTemplate):
            with open(jsonTemplate, "rb") as f:
                report_definition = json.loads(f.read())
        else:
            report_definition = json.loads(jsonTemplate)

        additional_fonts = [dict(value='firefly',filename='fireflysung.ttf')]
        is_test_data = {}
        report = Report(report_definition, data, is_test_data, additional_fonts=additional_fonts)
        report_file = report.generate_pdf(filename=output, add_watermark=False)
        logger.info("%sjson to pdf successed!"%jsonTemplate)
        return output

    @classmethod
    def pdf2Png(cls, fpath, folder , filename):
        images_from_path  =  convert_from_path(fpath, output_folder = folder, output_file = filename, fmt = 'png',single_file = True,first_page = 1, last_page = 1)
        logger.info('%s to %s.png successed!'%(fpath,folder+filename))
        return os.sep.join([folder, "%s.png" % filename])

    def makeSimpleReport(self, result, fdir="", name=""):
        try:
            simpleData = copy.deepcopy(self.testData)
            simpleData["MEASUREMENTINTERVAL"] = result["result"]["MEASUREMENTINTERVAL"]
            simpleData["BUSINESSRECOVERYTIME"] = result["result"]["BUSINESSRECOVERYTIME"]
            simpleData["RAMPUPTIME"]=result["result"]["RAMPUPTIME"]
            logger.info(self.startTpceArgs)
            simpleData["CONFIGCUSTOMER"]=str(self.startTpceArgs["customer"])
            simpleData["REVISION_DATE"]=str(datetime.datetime.now().strftime('%Y-%m-%d'))
            simpleData["VERSION"]="1.14.0"
            simpleData["AVAILABILITY_DATE"]=str(datetime.datetime.now().year + 1)  + "-" + datetime.datetime.now().strftime('%m-%d')
            simpleData["DB_IMAGE"] = toBase64(os.sep.join([os.getcwd(),'logo',self.startTpceArgs['dbconfig']['dbtype']+'.jpg']))
            count=0
            for i in range(0,11):
                simpleData["TEST_DATA"][i]["T_NAME"]=result['result']['TEST_DATA'][i]['T_NAME']
                simpleData["TEST_DATA"][i]["T_90"]=result['result']['TEST_DATA'][i]['T_90']
                simpleData["TEST_DATA"][i]["T_MAX"]=result['result']['TEST_DATA'][i]['T_MAX']
                simpleData["TEST_DATA"][i]["T_COUNT"]=result['result']['TEST_DATA'][i]['T_COUNT']
                simpleData["TEST_DATA"][i]["T_MIN"]=result['result']['TEST_DATA'][i]['T_MIN']
                simpleData["TEST_DATA"][i]["T_AVG"]=result['result']['TEST_DATA'][i]['T_AVG']
                simpleData["TEST_DATA"][i]["T_PER"]=str(round(float(result['result']['TEST_DATA'][i]['T_PER'])*100,2))+'%'
                if(i!=10):
                    count+=float(simpleData["TEST_DATA"][i]["T_COUNT"])
            simpleData["TEST_DATA"][10]["T_PER"]='N/A'
            simpleData["INMEASUREMENTINTERVAL"]=str(int(count))
            simpleData["TPSE"]=str(round(result['result']['tpsE'],2))+'tpsE'
            if self.config['reportLanguage'] == "CH":
                pdfPath = self.json2Pdf("tpc-e-CH.json",simpleData, os.sep.join([fdir , name]))
            else:
                pdfPath = self.json2Pdf("tpc-e-EN.json",simpleData, os.sep.join([fdir , name]))

                return pdfPath
        except Exception as e:
            logger.info(u'标准报告生成失败！')
            logger.error(repr(e))
            return None

    def makeTestReport(self, folder, pdfname, result, lastPng):
        try:
            testData = copy.deepcopy(self.testData)
            testData["customer"] = str(self.startTpceArgs["customer"])
            testData["initialdays"] = str(self.startTpceArgs["initialdays"])
            testData["scalefactor"] = str(self.startTpceArgs["scalefactor"])
            testData["uptime"] = str(self.startTpceArgs["uptime"])
            testData["testtime"] = str(self.startTpceArgs["testtime"])
            testData["ip"] = self.startTpceArgs["dbconfig"]["ip"]
            testData["port"] = str(self.startTpceArgs["dbconfig"]["port"])
            testData["username"] = self.startTpceArgs["dbconfig"]["username"]
            testData["password"] = self.startTpceArgs["dbconfig"]["password"]
            testData["dbname"] = self.startTpceArgs["dbconfig"]["dbname"]
            testData["dbtype"] = self.startTpceArgs["dbconfig"]["dbtype"]
            for i in range(0, len(self.startTpceArgs['agents'])):
                testData["agent%dip"%(i+1)] = self.startTpceArgs["agents"][i]["ip"]
                testData["agent%dport"%(i+1)] = str(self.startTpceArgs["agents"][i]["port"])
                testData["agent%dconcurrency"%(i+1)] = str(self.startTpceArgs["agents"][i]["concurrency"])
                testData["agent%dstartid"%(i+1)] = str(self.startTpceArgs["agents"][i]["startid"])
                testData["agent%dendid"%(i+1)] = str(self.startTpceArgs["agents"][i]["endid"])
                testData["agent%ddelay"%(i+1)] = str(self.startTpceArgs["agents"][i]["delay"])
                testData['starttime']=str(datetime.datetime.now().strftime('%H-%M-%S'))

            names = ['bv','cp','mf','mw','sd','tl','to','tr','ts','tu','dm']
            for i in range(0, len(names)):
                name = names[i]
                testData[name+'min'] = result['result']['TEST_DATA'][i]['T_MIN']
                testData[name+'max'] = result['result']['TEST_DATA'][i]['T_MAX']
                testData[name+'90'] = result['result']['TEST_DATA'][i]['T_90']
                testData[name+'avg'] = result['result']['TEST_DATA'][i]['T_AVG']
                testData[name+'count'] = result['result']['TEST_DATA'][i]['T_COUNT']
                testData[name+'per'] = result['result']['TEST_DATA'][i]['T_PER']

            agents = self.startTpceArgs["agents"]

            for j in range(0,len(agents)):
                agent = agents[j]
                agentsResult=requests.get("http://%s:12345/api/v1/agents?type=tpce" % agent['ip']).json()
                testData['cpu%d'%j]=agentsResult['agents']['TPCEAgent-%d'% agent["port"]]['data']['cpu_percent']
                testData['thread%d'%j]=agentsResult['agents']['TPCEAgent-%d'% agent["port"]]['data']['num_threads']
                testData['memory%d'%j]=round(agentsResult['agents']['TPCEAgent-%d'% agent["port"]]['data']['memory_percent'],1)

            testData["tpsE"] = toBase64(lastPng)

            pdfPath = os.sep.join([folder, pdfname])
            pdfPath = self.json2Pdf("tpceTest.json", testData, pdfPath)
            if os.path.exists(pdfPath):
                logger.info(u"中间报告生成成功！")
                return pdfPath
            else:
                logger.info(u"中间测试报生成告失败！")
                return None
        except Exception as e:
            logger.error(traceback.format_exc(e))
            logger.error(u'中间测试报生成告失败！')
            logger.error(repr(e))
            return None


class TPCEAutoRunner(object):

    def __init__(self):
        super(TPCEAutoRunner, self).__init__()
        self.taskInfos = []
        self.isStarted = False
        self.isFinished = False
        self.tpseReport = TPSEReport()
        self.dingding = Dingding()
        self.initConnect()

    def initConnect(self):
        signalManager.startTest.connect(self.run)

    def initData(self, taskId=0):
        self.taskId = taskId
        self.times = []
        self.tpsEs = []
        self.startTime = time.time()
        self.now_time = datetime.datetime.now().strftime('%Y-%m-%d')
        self.now_timeNextY= str(datetime.datetime.now().year + 1)  + "-" + datetime.datetime.now().strftime('%m-%d')
        self.now_time_s = datetime.datetime.now().strftime('%H-%M-%S')
        self.paths = {}
        self.rootDir = os.sep.join([os.getcwd(), self.now_time])
        self.taskDir = os.sep.join([self.rootDir, "%s" % self.now_time_s])
        self.mkdirs()
        self.config  = load('config.json')
        self.useLastPng = "useLastPng"
        self.lastPng = "lastPng"
        self.lastResult = None
        self.lastResultTime = 0
        self.lastSimplePDF = ""
        self.lastTestPDF = ""
        self.lastProgress = 0
        self.lastResultPath=''
        self.task = {
            'status': "",
            'taskId': self.taskId,
            'starttime': self.now_time_s,
            'endTime': ''
        }
        self.currentTestMinute = 0
        self.twoHouerTradeResults = []

        self.isGetResultSuccessed = False

        self.setStartTpceArgs(load('start.json'))

    def setStartTpceArgs(self, startTpceArgs):
        self.startTpceArgs = startTpceArgs
        self.tpseReport.setStartTpceArgs(startTpceArgs)

    def mkdirs(self):
        if not os.path.exists(self.taskDir):
            os.makedirs(self.taskDir)

        pathDirs = ["results", "screenshots", "simplePDFs", "testPDFs", "lastResult", "reportResults", "BestReport"] 
        for f in pathDirs:
            p = os.sep.join([self.taskDir, f])
            if not os.path.exists(p):
                os.makedirs(p)
                self.paths[f] = p

    def startTest(self):
        while True:
            try:
                url  =  'http://%s:%d/api/v1/tpce/start' % (self.config["ip"],self.config["port"])
                r = requests.post(url,json.dumps(self.startTpceArgs))
                result = r.json()
                logger.info(json.dumps(r.json(),indent = 4))
                if result["retcode"] == 0:
                    break
                else:
                    time.sleep(5)
            except Exception as e:
                logger.error(traceback.format_exc(e))

    def getProgress(self):
        try:
            url  =  'http://%s:%d/api/v1/tpce/status' % (self.config["ip"],self.config["port"])
            r = requests.post(url,json.dumps(self.startTpceArgs))
            logger.info(json.dumps(r.json(), indent = 4))
            self.lastProgress = r.json()['result']['progress']['value']
            return self.lastProgress
        except Exception as e:
            logger.error(repr(e))
            return 0

    def getResult(self, MIStart=0, MIEnd=0):
        url = "http://%s:%d/api/v1/tpce/result"  % (self.config["ip"],self.config["port"])

        args = copy.deepcopy(self.startTpceArgs)

        args["MIStart"] = MIStart
        args["MIEnd"] = MIEnd

        r = requests.post(url,json.dumps(args))
        logger.info(json.dumps(r.json(),indent = 4))

        return r.json()

    def stop(self):
        url = "http://%s:%d/api/v1/tpce/stop"  % (self.config["ip"],self.config["port"])
        r = requests.post(url,json.dumps(self.startTpceArgs))
        logger.info(json.dumps(r.json(),indent = 4)) 

    def log(self):
        url = "http://%s:%d/api/v1/tpce/log"  % (self.config["ip"],self.config["port"])
        r = requests.post(url,json.dumps(self.startTpceArgs))
        logger.info(json.dumps(r.json(),indent = 4)) 

    def computeTpsE(self, result):
        try:
            tpsE=result['result']['tpsE']
            logger.info("tpse %f" % (tpsE))
            return tpsE
        except Exception as e:
            logger.error(repr(e))
            return 0

    def resultName(self, resultTime , suffix=""):
        if len(suffix) > 0:
            return "%s.%s" % (secondsToTime(resultTime, "-"), suffix)
        else:
            return secondsToTime(resultTime, "-")

    def getTradeResultsPerMintue(self, tradeResults):
        tpsEs = []
        tpsEs.append(0)
        for i in range(0, len(tradeResults)):
            if i == 0:
                tpsEs.append(tradeResults[i] / 60.0)
            else:
                tpsEs.append((tradeResults[i] - tradeResults[i-1]) / 60.0)
        return tpsEs

    def saveResult(self):
        lastResult = self.getResult()
        if self.lastResult["retcode"] == 0:
            self.lastResult = lastResult
            self.lastResultTime = time.time() - self.startTime
            result = self.lastResult["result"]
            logger.info(result)
            if "TradeResult" in result and len(result["TradeResult"]) > 0:
                logger.info(result["TradeResult"])
                self.times = range(0, len(result["TradeResult"]) + 1)
                self.tpsEs = self.getTradeResultsPerMintue(result["TradeResult"])
            else:
                self.times.append(self.lastResultTime)
                if  "tpsE" in result:
                    self.tpsEs.append(self.computeTpsE(self.lastResult))
                else:
                    self.tpsEs.append(0)

            resultJson = json.dumps(self.lastResult, indent = 4)
            nowTimes = datetime.datetime.now().strftime('%Y%m%d-%H-%M-%S')
            resultName = nowTimes + '-result.json'
            self.lastResultPath=os.sep.join([self.paths["results"], resultName])
            writeFile(self.lastResultPath, resultJson)

            logger.info(u'tpcE reslut 结果获取成功')
            return True
        else:
            logger.error(u'tpcE reslut 结果获取失败')
            return False

    def isTestFininshed(self):
        progress = self.getProgress()
        if progress == 100 :
            return True
        else:
            return False

    def isTestError(self):
        errorTime=int(self.config['errorTime']/self.config['resultTime'])
        if len(self.tpsEs) > errorTime and len(set(self.tpsEs[-errorTime: -1])) == 1 and sum((self.tpsEs[-errorTime: -1])) == 0:
            return True
        else:
            return False

    def isTestStarted(self):
        ret = False
        if self.lastResult["retcode"] == 0:
            ret = True

        return ret

    def handleStart(self):
        writeFile(os.sep.join([self.taskDir, 'config.json']), json.dumps(self.config, indent = 4))
        writeFile(os.sep.join([self.taskDir, 'start.json']), json.dumps(self.startTpceArgs, indent = 4))

    def handleFinished(self):
        resultTime = str(int(self.lastResultTime))
        for key in ["results", "screenshots", "simplePDFs", "testPDFs"]:
            for suffix in ["json", "png",  "jpg" , "pdf"]:
                path = os.sep.join([self.paths[key], ".".join([resultTime, suffix])])
                if suffix == 'json' and key == "results": 
                    path = self.lastResultPath
                logger.info(path)
                logger.info(os.path.exists(path))
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        logger.info(path)
                        content = f.read()
                        with open(os.sep.join([self.paths["lastResult"] , ".".join([key + resultTime, suffix])]),'wb') as lf:
                            lf.write(content)

        if TwoHouerTradeResultJob.BestJob:
            self.actionBestReport(self.paths["lastResult"], TwoHouerTradeResultJob.BestJob)
        logger.info(u'任务测试结束)！')

    def handleResult(self):
        global is_exit
        while not is_exit:
            try:
                t1 = time.time()
                self.lastResult = self.getResult()

                isTestError=self.isTestError()
                if isTestError:
                    is_exit=True
                    logger.error(u'tpcE reslut等待超时异常！')
                    break

                if self.lastResult["retcode"] == 0:
                    self.isStarted = True

                if self.isStarted:
                    self.isGetResultSuccessed = self.saveResult()
                    if self.isGetResultSuccessed:
                        TestMinute = int(self.lastResult["result"]["TIMESPAN"] / 60)
                        logger.info("TestMinute %d" % TestMinute)
                        logger.info("self.currentTestMinute %d" % self.currentTestMinute)
                        logger.info((TestMinute - self.currentTestMinute) == 1)
                        if (TestMinute > self.currentTestMinute) and TestMinute >= MeasureInterval:
                            self.currentTestMinute = TestMinute
                            job = TwoHouerTradeResultJob(self.currentTestMinute)
                            TwoHouerTradeResultJob.addJob(job)
                            t=Thread(target=job.getResult, args=(self.config["ip"], self.config["port"], self.startTpceArgs, self.paths["reportResults"]))
                            t.start()

                        if self.lastResultTime > self.startTpceArgs["testtime"] * 60:
                            self.isFinished = self.isTestFininshed()
                            if self.isFinished:
                                is_exit = True
                                break
                t2 = time.time()
                sleepTime = self.config['resultTime'] - (t2 - t1)
                if sleepTime  < 0:
                    sleepTime = 0
                time.sleep(sleepTime)

            except Exception as e:
                logger.error(traceback.format_exc(e))
                logger.error(u'tpcE reslut 调用异常')
                logger.error(repr(e))



    def actionBestReport(self, reportDir , job):
        writeFile(os.sep.join([reportDir, '%s.json' % job.reportName()]), json.dumps(job.json(), indent = 4))
        BestPDF = self.tpseReport.makeSimpleReport(job.result(), reportDir , "%s.pdf" % job.reportName())
        if BestPDF:
            logger.info(u"最好结果标准报告【%s】生成成功！" % BestPDF)
            BestPDFPng = TPSEReport.pdf2Png(BestPDF, self.paths["BestReport"], job.reportName())
            logger.info(u"最好结果标准报告转换图片【%s】成功！" % BestPDFPng)
            self.dingding.sendmsg(self.config["dingdingUrl"],toPicbed(self.config['mapBedUrl'], BestPDFPng))
            logger.info(u"最好结果标准报告【%s】发送钉钉成功！" % BestPDFPng)


    def handleReport(self):

        def actionReport(result, resultTime):
            simplePDF = self.tpseReport.makeSimpleReport(result, self.paths["simplePDFs"],  self.resultName(resultTime, "pdf"))
            if simplePDF:
                logger.info(u"标准报告【%s】生成成功！" % simplePDF)
                simplePDFPng = TPSEReport.pdf2Png(simplePDF, self.paths["simplePDFs"], self.resultName(resultTime))
                logger.info(u"标准报告转换图片【%s】成功！" % simplePDFPng)
                self.dingding.sendmsg(self.config['dingdingUrl'],toPicbed(self.config['mapBedUrl'], simplePDFPng))
                logger.info(u"标准报告【%s】发送钉钉成功！" % simplePDFPng)

            testPDF = self.tpseReport.makeTestReport(self.paths["testPDFs"], self.resultName(resultTime, "pdf"),result, self.lastPng)
            if testPDF:
                logger.info(u"中间测试报告【%s】生成成功！" % testPDF)
                testPDFPng = TPSEReport.pdf2Png(testPDF, self.paths["testPDFs"], self.resultName(resultTime))
                logger.info(u"中间测试报告转换图片【%s】成功！" % testPDFPng)
                self.dingding.sendmsg(self.config['dingdingUrl'],toPicbed(self.config['mapBedUrl'], testPDFPng))
                logger.info(u"中间测试报告【%s】发送钉钉成功！" % testPDFPng)

        bestJob = TwoHouerTradeResultJob.BestJob
        while not is_exit:
            try:
                if os.path.exists(self.lastPng) and self.useLastPng != self.lastPng:
                    self.useLastPng = self.lastPng
                    if self.isStarted:
                        actionReport(copy.deepcopy(self.lastResult), copy.deepcopy(int(self.lastResultTime)))

                logger.info("BestJob: %s" % TwoHouerTradeResultJob.BestJob)
                logger.info("last BestJob: %s" % bestJob)
                if TwoHouerTradeResultJob.BestJob != bestJob:
                    self.actionBestReport(self.paths["BestReport"], TwoHouerTradeResultJob.BestJob)
                    bestJob = TwoHouerTradeResultJob.BestJob

                time.sleep(self.config['dingdingTime'])

            except Exception as e:
                logger.error(traceback.format_exc(e))

        if self.isStarted:
            actionReport(copy.deepcopy(self.lastResult), copy.deepcopy(int(self.lastResultTime)))

    def run(self):
        global is_exit
        self.initData()
        self.handleStart()
        self.startTest()
        resultThread = Thread(target = self.handleResult)
        reportThread = Thread(target = self.handleReport)
        resultThread.start()
        reportThread.start()
        self.handleFinished()


def handler(signum, frame):
    global is_exit
    is_exit = True
    logger.info(u"receive a signal %d, is_exit = %d"%(signum, is_exit))

tpceautorunner = TPCEAutoRunner()
