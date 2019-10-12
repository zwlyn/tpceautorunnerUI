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
import matplotlib.pyplot as plt
import matplotlib
#matplotlib.use('Agg')
import base64
from log import logger
from reportbro import Report
from pdf2image import convert_from_path

import logging
from logging.handlers import RotatingFileHandler
import traceback
import copy
import subprocess

import PyQt5.QtGui as QtGui

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import random



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

def load_json(fpath):
    with open(fpath,'r', encoding='utf-8') as f:
        dict_data = json.loads(f.read())
    return dict_data

is_exit = False
MeasureInterval = 120



class TPCEAutoRunner(object):

    def __init__(self):
        super(TPCEAutoRunner, self).__init__()
        self.taskInfos = []
        self.isStarted = False
        self.tpsePlot = TPSEPlot()
        self.tpseReport = TPSEReport()
        self.dingding = Dingding()

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
                            isFinished = self.isTestFininshed()
                            if isFinished:
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






    def run(self):
        global is_exit
        self.initData()
        self.handleStart()
        self.startTest()
        resultThread = Thread(target = self.handleResult)
        reportThread = Thread(target = self.handleReport)
        resultThread.start()
        reportThread.start()

def handler(signum, frame):
    global is_exit
    is_exit = True
    logger.info(u"receive a signal %d, is_exit = %d"%(signum, is_exit))

if __name__  ==  '__main__':
    app=QApplication(sys.argv)
    demo=TPCEAutoRunnerUI()
    sys.exit(app.exec_())



