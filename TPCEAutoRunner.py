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
    
def load_json(fpath):
    with open(fpath,'r', encoding='utf-8') as f:
        dict_data = json.loads(f.read())
    return dict_data

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




class WorkThread(QThread):
    #trigger = pyqtSignal()
    def __int__(self):
        super(WorkThread, self).__init__()

    def run(self):
        logger.info('进入TPCEAutoRunner启动的糟函数')
        d = TPCEAutoRunner()
        d.run()

        # 循环完毕后发出信号
        #self.trigger.emit()
    def test(self):
        logger.info('入TPCEAutoRunner启动的糟函数')
        print('Hello')

class TPCEAutoRunnerUI(QDialog):
    signal_start = pyqtSignal()
    def test(self):
        logger.info('test')
    def __init__(self):
        super(TPCEAutoRunnerUI, self).__init__()
        workThread = WorkThread()
        self.signal_start.connect(self.test)

        self.start_map = load_json('start.json')
        self.config_map = load_json('config.json')

        self.setGeometry(200,100,1280,780)
        self.setWindowTitle('TPCEAutoRunnerUI')
        
        self.leftlist = QListWidget()

        #调整初始大小
        self.leftlist.resize(60, 700)
        #设置调整宽和高
        self.leftlist.setFixedSize(60, 700)
        self.leftlist.insertItem(0,'设置')
        self.leftlist.insertItem(1,'绘图')
        self.leftlist.insertItem(2,'报告')
        self.leftlist.insertItem(3,'启动')

        #单机出发绑定的糟函数
        self.leftlist.itemClicked.connect(self.start_clicked)

        self.leftlist.setStyleSheet("QListWidget{color:rgb(0,0,0); background:rgb(255,255,255);border:0px solid gray;}"
                                     "QListWidget::Item{height:40px;border:0px solid gray;padding-left:0;color:rgb(0,0,0);}"
                                     "QListWidget::Item:hover{color:rgb(0,200,200);border:0px solid gray;}"
                                     "QListWidget::Item:{color:rgb(0,0,0);border:0px solid gray;}"
                                     "QListWidget::Item:selected:active{background:rgb();color:rgb(0,0,0);border-width:0;}"
                                     "QListWidget::Item[0]{color:rgb(255,0,0);border:0px solid gray;}"
                                    )


        self.settingBox=QGroupBox()
        self.settingBox.resize(1220, 700)
        #设置调整宽和高
        self.settingBox.setFixedSize(1220, 700)
        self.reportBox=QGroupBox()
        self.plotBox=QGroupBox('测试图像')

        self.configBox_list = list()

        self.init_settingBox()
        self.init_reportBox()
        self.init_plotBox()

        self.stack=QStackedWidget(self)

        self.stack.addWidget(self.settingBox)
        self.stack.addWidget(self.plotBox)
        self.stack.addWidget(self.reportBox)

        mainLayout =QVBoxLayout()

        menuBar = QMenuBar()
        menu = menuBar.addMenu('logo')

        mid = QWidget()
        midLayout = QHBoxLayout()
        midLayout.addWidget(self.leftlist)
        midLayout.addWidget(self.stack)
        midLayout.spacing()
        midLayout.addStretch(100)            
        midLayout.setSpacing(5)
        mid.setLayout(midLayout)

        statusBar = QStatusBar()
        statusBar.showMessage('Hello man!')

        mainLayout.addWidget(menuBar)
        mainLayout.addWidget(mid)
        mainLayout.addWidget(statusBar)

        self.setLayout(mainLayout)

        self.leftlist.currentRowChanged.connect(self.display)

        self.show()

        # 每5秒存储一次结果
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.save_date)

        self.timer.start(3000)

    def save_date(self):
        with open('start.json', 'w') as f:
            f.write(json.dumps(self.start_map, indent=4))
        with open('config.json', 'w') as f:
            f.write(json.dumps(self.config_map, indent=4))

    # 关闭窗口时会执行累的close方法，并触发QCloseEvent信号，进而执行closeEvent(self,QCloseEvent)方法
    def closeEvent(self, event):
        # 退出前对内存中的改变进行存储
        with open('start.json', 'w') as f:
            f.write(json.dumps(self.start_map, indent=4))
        logger.info('改变已经保存')
        reply = QMessageBox.question(self, '本程序',
                                           "是否要退出程序？",
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def init_settingBox(self):

        mainLayout = QVBoxLayout()

        mainTab = QTabWidget()
        startTab = QWidget()
        configTab = QWidget()

        #--------------startBox----------------
        startBox = QHBoxLayout()

        layoutL = QFormLayout()

        self.startArgs = {
        'customer': QLineEdit(),
        'initialdays': QLineEdit(),
        'scalefactor': QLineEdit(),
        'uptime': QLineEdit(),
        'testtime': QLineEdit(),
        'dbconfig':{
            'ip': QLineEdit(),
            'dbname': QLineEdit(),
            'port': QLineEdit(),
            'username': QLineEdit(),
            'dbtype': QLineEdit(),
            'password': QLineEdit(),
            'instance': QLineEdit()
        }
        }

        self.startArgs['customer'].setText(str(self.start_map['customer']))
        self.startArgs['initialdays'].setText(str(self.start_map['initialdays']))
        self.startArgs['scalefactor'].setText(str(self.start_map['scalefactor']))
        self.startArgs['uptime'].setText(str(self.start_map['uptime']))
        self.startArgs['testtime'].setText(str(self.start_map['testtime']))

        self.startArgs['dbconfig']['ip'].setText(str(self.start_map['dbconfig']['ip']))
        self.startArgs['dbconfig']['port'].setText(str(self.start_map['dbconfig']['port']))
        self.startArgs['dbconfig']['username'].setText(str(self.start_map['dbconfig']['username']))
        self.startArgs['dbconfig']['password'].setText(str(self.start_map['dbconfig']['password']))
        self.startArgs['dbconfig']['dbname'].setText(str(self.start_map['dbconfig']['dbname']))
        self.startArgs['dbconfig']['dbtype'].setText(str(self.start_map['dbconfig']['dbtype']))

        layoutL.addRow(QLabel("用户数量:"), self.startArgs['customer'])
        layoutL.addRow(QLabel("初始天数:"), self.startArgs['initialdays'])
        layoutL.addRow(QLabel("比例因子:"), self.startArgs['scalefactor'])
        layoutL.addRow(QLabel("上升时长:"), self.startArgs['uptime'])
        layoutL.addRow(QLabel("测试时长:"), self.startArgs['testtime'])
        layoutL.addRow(QLabel("数据库配置:"))
        layoutL.addRow(QLabel("IP地址:"), self.startArgs['dbconfig']['ip'])
        layoutL.addRow(QLabel("端口号:"), self.startArgs['dbconfig']['port'])
        layoutL.addRow(QLabel("用户名:"), self.startArgs['dbconfig']['username'])
        layoutL.addRow(QLabel("密码:"), self.startArgs['dbconfig']['password'])
        layoutL.addRow(QLabel("数据库实例名:"), self.startArgs['dbconfig']['dbname'])
        layoutL.addRow(QLabel("数据库类别:"), self.startArgs['dbconfig']['dbtype'])

        # 设置信号糟，当行内容修改结束时进行修改
        self.startArgs['customer'].textEdited.connect(self.modify_startArgs)     
        self.startArgs['initialdays'].textEdited.connect(self.modify_startArgs)  
        self.startArgs['scalefactor'].textEdited.connect(self.modify_startArgs)  
        self.startArgs['uptime'].textEdited.connect(self.modify_startArgs)  
        self.startArgs['testtime'].textEdited.connect(self.modify_startArgs)  

        self.startArgs['dbconfig']['ip'].textEdited.connect(self.modify_startArgs)
        self.startArgs['dbconfig']['port'].textEdited.connect(self.modify_startArgs)
        self.startArgs['dbconfig']['username'].textEdited.connect(self.modify_startArgs)
        self.startArgs['dbconfig']['password'].textEdited.connect(self.modify_startArgs)
        self.startArgs['dbconfig']['dbname'].textEdited.connect(self.modify_startArgs)
        self.startArgs['dbconfig']['dbtype'].textEdited.connect(self.modify_startArgs)

        layoutR = QHBoxLayout()
        self.agent = {
        "ip": QLineEdit(),
        "port": QLineEdit(),
        "concurrency": QLineEdit(),
        "instance": QLineEdit(),
        "startid": QLineEdit(),
        "endid": QLineEdit(),
        "delay": QLineEdit()
        }

        agentBox = QWidget()
        agent_layout = QFormLayout()
        agent_layout.addRow(QLabel("TPCEAgent配置:"))
        agent_layout.addRow(QLabel("IP地址:"), self.agent['ip'])
        agent_layout.addRow(QLabel("端口号:"), self.agent['port'])
        agent_layout.addRow(QLabel("并发数:"), self.agent['concurrency'])
        agent_layout.addRow(QLabel("实例数:"), self.agent['instance'])
        agent_layout.addRow(QLabel("起始id:"), self.agent['startid'])
        agent_layout.addRow(QLabel("终止id:"), self.agent['endid'])
        agent_layout.addRow(QLabel("延迟:"), self.agent['delay'])
        agentBox.setLayout(agent_layout)


        self.listAgent = QListWidget()
        self.listAgent.resize(50, 300)
        self.listAgent.setStyleSheet("QListWidget{color:rgb(0,0,0); background:rgb(255,255,255);border:0px solid gray;}"
                                     "QListWidget::Item{height:40px;border:0px solid gray;padding-left:0;color:rgb(0,0,0);}"
                                     "QListWidget::Item:hover{color:rgb(0,200,200);border:0px solid gray;}"
                                     "QListWidget::Item:{color:rgb(0,0,0);border:0px solid gray;}"
                                     "QListWidget::Item:selected:active{background:rgb();color:rgb(0,0,0);border-width:0;}"
                                     "QListWidget::Item[0]{color:rgb(255,0,0);border:0px solid gray;}"
                                    )
        self.listAgent.addItem('新建TPCEAgent')
        self.listAgent.addItem('删除TPCEAgent')
        #self.listAgent.setCurrentItem(self.listAgent.item(1))

        self.init_agent()

        self.listAgent.itemClicked.connect(self.remove_agent)
        self.listAgent.itemClicked.connect(self.add_agent)
        self.listAgent.itemClicked.connect(self.select_agent)
        
        layoutR.addWidget(self.listAgent)
        layoutR.addWidget(agentBox)
                     
        startBox.addLayout(layoutL)
        startBox.addLayout(layoutR)

        # 将startBox放入标签中
        startTab.setLayout(startBox)

        #------------configBox-------------
        configBox = QHBoxLayout()

        config_layout = QFormLayout()
        self.configArgs = {
        'ip': QLineEdit(),
        'port': QLineEdit(),
        'mapBedUrl': QLineEdit(),
        'dingdingUrl': QLineEdit(),
        'dingdingTime': QLineEdit(),
        'resultTime': QLineEdit(),
        'errorTime': QLineEdit(),
        'reportLanguage': QLineEdit()
        }
        self.configArgs['ip'].setText(str(self.config_map['ip']))
        self.configArgs['port'].setText(str(self.config_map['port']))
        self.configArgs['mapBedUrl'].setText(str(self.config_map['mapBedUrl']))
        self.configArgs['dingdingTime'].setText(str(self.config_map['dingdingTime']))
        self.configArgs['resultTime'].setText(str(self.config_map['resultTime']))
        self.configArgs['errorTime'].setText(str(self.config_map['errorTime']))
        self.configArgs['reportLanguage'].setText(str(self.config_map['reportLanguage']))
        self.configArgs['dingdingUrl'].setText(str(self.config_map['dingdingUrl'][0]))

        config_layout.addRow(QLabel("工具所在IP"), self.configArgs['ip'])
        config_layout.addRow(QLabel("工具所在端口号"), self.configArgs['port'])
        config_layout.addRow(QLabel("图床地址"), self.configArgs['mapBedUrl'])
        config_layout.addRow(QLabel("钉钉消息间隔时间"), self.configArgs['dingdingTime'])
        config_layout.addRow(QLabel("获取结果间隔时间"), self.configArgs['resultTime'])
        config_layout.addRow(QLabel("测试异常兼容时间"), self.configArgs['errorTime'])
        config_layout.addRow(QLabel("报告语言"), self.configArgs['reportLanguage'])
        config_layout.addRow(QLabel("钉钉地址"), self.configArgs['dingdingUrl'])

        # 设置信号糟，当行内容修改结束时进行修改
        self.configArgs['ip'].textEdited.connect(self.modify_configArgs)     
        self.configArgs['port'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['mapBedUrl'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['dingdingTime'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['resultTime'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['errorTime'].textEdited.connect(self.modify_configArgs)     
        self.configArgs['reportLanguage'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['dingdingUrl'].textEdited.connect(self.modify_configArgs)  

        configBox.addLayout(config_layout)

        #将configBox放入标签中
        configTab.setLayout(configBox)

        mainTab.addTab(startTab, '启动参数')
        mainTab.addTab(configTab, '配置参数')

        mainLayout.addWidget(mainTab)

        self.settingBox.setLayout(mainLayout)

    def modify_startArgs(self):
        logger.info('modify_startArgs!!')

        self.start_map['customer'] = int(self.startArgs['customer'].text())
        self.start_map['testtime'] = int(self.startArgs['testtime'].text())
        self.start_map['initialdays'] = int(self.startArgs['initialdays'].text())
        self.start_map['scalefactor'] = int(self.startArgs['scalefactor'].text())
        self.start_map['uptime'] = int(self.startArgs['uptime'].text())

        self.start_map['dbconfig']['ip'] = self.startArgs['dbconfig']['ip'].text()
        self.start_map['dbconfig']['port'] = int(self.startArgs['dbconfig']['port'].text())
        self.start_map['dbconfig']['dbname'] = self.startArgs['dbconfig']['dbname'].text()
        self.start_map['dbconfig']['username'] = self.startArgs['dbconfig']['username'].text()
        self.start_map['dbconfig']['dbtype'] = self.startArgs['dbconfig']['dbtype'].text()
        self.start_map['dbconfig']['password'] = self.startArgs['dbconfig']['password'].text()

    def init_agent(self):
        for agent in self.start_map['agents']:
            self.listAgent.addItem('Agent%d' % (len(self.listAgent) - 1))

    def add_agent(self, item):
        if item.text() == '新建TPCEAgent':
            self.listAgent.addItem('Agent%d' % len(self.listAgent))
            new_agent = {
                "ip": "",
                "port": "",
                "concurrency": "",
                "instance": "",
                "startid": "",
                "endid": "",
                "delay": ""
            }
            self.start_map['agents'].append(new_agent)

    def select_agent(self, item):

        if not item.text() == '新建TPCEAgent' and not item.text() == '删除TPCEAgent':
            agentid = int(item.text()[5:]) - 1 

            self.agent['ip'].setText(str(self.start_map['agents'][agentid]['ip']))
            self.agent['port'].setText(str(self.start_map['agents'][agentid]['port']))
            self.agent['concurrency'].setText(str(self.start_map['agents'][agentid]['concurrency']))
            self.agent['instance'].setText(str(self.start_map['agents'][agentid]['instance']))
            self.agent['startid'].setText(str(self.start_map['agents'][agentid]['startid']))
            self.agent['endid'].setText(str(self.start_map['agents'][agentid]['endid']))
            self.agent['delay'].setText(str(self.start_map['agents'][agentid]['delay']))

        # 当输入数据后，且切换行和退出时进行存储
        self.agent['ip'].textEdited.connect(self.modify_agent)
        self.agent['port'].textEdited.connect(self.modify_agent)
        self.agent['concurrency'].textEdited.connect(self.modify_agent)
        self.agent['instance'].textEdited.connect(self.modify_agent)
        self.agent['startid'].textEdited.connect(self.modify_agent)
        self.agent['endid'].textEdited.connect(self.modify_agent)
        self.agent['delay'].textEdited.connect(self.modify_agent)

    def modify_agent(self):
        logger.info(self.listAgent.currentItem().text())
        currentItem = self.listAgent.currentItem()
        if not currentItem.text() == '新建TPCEAgent':
            agentid = int(currentItem.text()[5:]) - 1 
        
            self.start_map['agents'][agentid]['ip'] = self.agent['ip'].text()
            self.start_map['agents'][agentid]['port'] = int(self.agent['port'].text())
            self.start_map['agents'][agentid]['concurrency'] = int(self.agent['concurrency'].text())
            self.start_map['agents'][agentid]['instance'] = int(self.agent['instance'].text())
            self.start_map['agents'][agentid]['startid'] = int(self.agent['startid'].text())
            self.start_map['agents'][agentid]['endid'] = int(self.agent['endid'].text())
            self.start_map['agents'][agentid]['delay'] = int(self.agent['delay'].text())

    def modify_configArgs(self):
        logger.info('modify_configArgs!!')

        self.config_map['ip'] = self.configArgs['ip'].text()
        self.config_map['port'] = int(self.configArgs['port'].text())
        self.config_map['mapBedUrl'] = self.configArgs['mapBedUrl'].text()
        self.config_map['dingdingTime'] = int(self.configArgs['dingdingTime'].text())
        self.config_map['resultTime'] = int(self.configArgs['resultTime'].text())
        self.config_map['errorTime'] = int(self.configArgs['errorTime'].text())
        self.config_map['reportLanguage'] = self.configArgs['dingdingTime'].text()
        self.config_map['dingdingUrl'][0] = self.configArgs['dingdingUrl'].text()

    def remove_agent(self):
        '''
        每次删除最后一个agent
        '''
        currentItem = self.listAgent.currentItem()
        if currentItem.text() == '删除TPCEAgent':
            agentid = len(self.listAgent) - 1
            self.listAgent.takeItem(agentid)
            self.start_map['agents'].pop()

    def init_reportBox(self):
        layout = QHBoxLayout()
        tab_list = QTabWidget()

        pixmap_mid = QPixmap("img/ball.png")
        midreport = QLabel()
        midreport.setPixmap(pixmap_mid)

        pixmap_best = QPixmap("img/background.png")
        bestreport = QLabel()
        bestreport.setPixmap(pixmap_best)


        tab_list.addTab(midreport, '中间报告') 
        tab_list.addTab(bestreport, '最佳报告')

        layout.addWidget(tab_list)
        self.reportBox.setLayout(layout)
        

    def init_plotBox(self):
        layout = QVBoxLayout()

        m = TPSEPlot(self)

        layout.addWidget(m)

        self.plotBox.setLayout(layout)

    def start_clicked(self,item):
        if item.text() == '启动':
            logger.info('点击了启动item，开始启动 ～～')
            # self.signal_start.emit()
            d = TPCEAutoRunner()
            d.run()
            # 当获得循环完毕的信号时，停止计数
            # work.trigger.connect(timeStop)
    

    def display(self,i):
        #设置当前可见的选项卡的索引
        self.stack.setCurrentIndex(i)


class TPSEPlot(FigureCanvas):

    def __init__(self, parent=None):
        super(TPSEPlot).__init__()
        fig = Figure(figsize=(5, 4), dpi=100)
        self.plt = fig.add_subplot(111) 
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        #self.plt = plt

    def drawLine(self, linePoint, textPoint , text, color="Blue"):
        '''
        linePoint: 线顶点坐标 (x, y)
        textPoint: 文本坐标 (x, y)
        text: 文本标注
        color: 线颜色
        '''
        plt.annotate("",
        xy = linePoint,
        xytext = (linePoint[0], 0),
        arrowprops = dict( arrowstyle = '-', color = color)
        )
        bbox_props = dict(boxstyle = "round", fc = "w", ec = "0.5", alpha = 0)
        plt.text(textPoint[0], textPoint[1], "%s" % text, ha = "center", va = "center", size = 10,
            bbox = bbox_props)

    def drawArrow(self, arrowPoint, text, height, color="black"):
        '''
        arrowPoint: arrow顶点坐标 (x, y)
        text: 文本标注
        height: 箭头高度
        color: 线颜色
        '''
        plt.annotate("",
        xy = arrowPoint,
        xytext = (arrowPoint[0], arrowPoint[1] - height),
        arrowprops = dict( arrowstyle = 'simple, head_width = 1, head_length = 1', color = color)
        )
        bbox_props = dict(boxstyle = "round", fc = "w", ec = "0.5", alpha = 0)
        plt.text(arrowPoint[0], arrowPoint[1] - height - 0.2, "%s" % text, ha = "center", va = "center", size = 10,
        bbox = bbox_props)


    def plot(self, xData, yData):
        #self.plt.clf()
        self.plt.cla()   # 清除plt
        # self.plt.title("Test Run Graph")
        self.plt.xlabel("Elapsed Time in Minutes")
        self.plt.ylabel("Trade-Result Transcations Per Second")
        self.plt.plot(xData, yData)
        self.plt.axis([min(xData), max(xData), min(yData), max(yData) + 2])
        self.plt.ioff()


    def drawMIStartEnd(self, job):
        self.drawLine((job.rampuptime(), job.tpsE() + 1), (job.rampuptime(), job.tpsE() + 1.5), "Begin Steady State")
        self.drawLine((job.MIEnd() + 10, job.tpsE() + 1), (job.MIEnd() + 10, job.tpsE() + 1.5), "End Steady State")
        self.drawArrow((job.MIStart(), job.tpsE() - 0.1), "MI Start", 3)
        self.drawArrow((job.MIEnd(), job.tpsE() - 0.1), "MI End", 3)

    def show(self):
        self.plt.show()

    def close(self):
        self.plt.close()

    def savefig(self, path):
        self.plt.savefig(path)


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

    def handlePlot(self):
        def actionShot():
            self.lastPng = os.sep.join([self.paths["screenshots"], self.resultName(int(self.lastResultTime), "jpg")])
            plt.savefig(self.lastPng)
            logger.info(u'截图%s保存成功！' % self.lastPng)

        while not is_exit:
            try:
                if self.isStarted and self.isGetResultSuccessed:
                    _minCount = min(len(self.times),len(self.tpsEs))
                    minCount  =  _minCount
                    self.tpsePlot.plot(self.times[0:minCount], self.tpsEs[0:minCount])
                    job = TwoHouerTradeResultJob.BestJob
                    if job:
                        self.tpsePlot.drawMIStartEnd(job)

                    plt.pause(self.config["resultTime"])  #暂停一秒
                    plt.ioff()
                    logger.info(u'绘图更新成功！')
                    if  len(self.tpsEs) > 0:
                        actionShot()

                    if is_exit:
                        actionShot()

            except Exception as e:
                logger.error(traceback.format_exc(e))
                logger.error(u'绘图更新失败')
                logger.error(repr(e))

        if self.isStarted:
            actionShot()

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
        #self.startTest()
        poltThread = Thread(target = self.handlePlot)
        poltThread.start()
        resultThread = Thread(target = self.handleResult)
        reportThread = Thread(target = self.handleReport)
        resultThread.start()
        reportThread.start()
        poltThread.join()
        resultThread.join()
        reportThread.join()
        self.handleFinished()


def handler(signum, frame):
    global is_exit
    is_exit = True
    logger.info(u"receive a signal %d, is_exit = %d"%(signum, is_exit))

if __name__  ==  '__main__':
    app=QApplication(sys.argv)
    demo=TPCEAutoRunnerUI()
    sys.exit(app.exec_())

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    d = TPCEAutoRunner()
    d.run()


