

class ReportController(object):
    def __init__(self):
        self.initData()
        self.initConnect()

    def iniData(self):
        self.config = load('config.json')
        self.startTpceArgs = load('start.json')
        self.testData = load('data.json')

    def initConnect(self):
        pass
        
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
