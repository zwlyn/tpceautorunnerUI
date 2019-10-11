#!/usr/bin/python3
# -*- coding-utf_8 -*-
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .agentLayout import agentLayout
from log import logger
from app import signalManager
from .startBox import startBox

class SettingBox(QWidget):
# 为什么__init__里面有parent=None，super()里要放自己和self，__init__(parent)
	def __init__(self, parent=None):
		super(SettingBox,self).__init__(parent)
		self.initData()
		self.initUI()
		self.initConnect()

	def initData(self):

        self.config_map = load_json('config.json')



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

	def initUI(self):
        self.settingBox=QGroupBox()
        self.settingBox.resize(1220, 700)
        #设置调整宽和高
        self.settingBox.setFixedSize(1220, 700)

        self.mainLayout = QVBoxLayout()
        self.mainTab = QTabWidget()

		startTab = QWidget()
		startTab.setLayout(startBox)
        self.mainTab.addTab(startTab, '启动参数')
        self.init_settingBox_configBox()

        self.mainLayout.addWidget(self.mainTab)
        self.settingBox.setLayout(self.mainLayout)




    def init_settingBox_configBox(self): 
        configTab = QWidget()
        configBox = QHBoxLayout()

        config_layout = QFormLayout()

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

        configBox.addLayout(config_layout)

        #将configBox放入标签中
        configTab.setLayout(configBox)

        self.mainTab.addTab(configTab, '配置参数')


	def initConnect(self):

        # 设置config的信号糟，当行内容修改结束时进行修改
        self.configArgs['ip'].textEdited.connect(self.modify_configArgs)     
        self.configArgs['port'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['mapBedUrl'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['dingdingTime'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['resultTime'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['errorTime'].textEdited.connect(self.modify_configArgs)     
        self.configArgs['reportLanguage'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['dingdingUrl'].textEdited.connect(self.modify_configArgs) 



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



    def modify_configArgs(self):
        logger.info('modify_configArgs!!')

        self.config_map['ip'] = self.configArgs['ip'].text()
        self.config_map['mapBedUrl'] = self.configArgs['mapBedUrl'].text()
        self.config_map['reportLanguage'] = self.configArgs['reportLanguage'].text()
        self.config_map['dingdingUrl'][0] = self.configArgs['dingdingUrl'].text()
        if self.sender().text() != '':
            self.config_map['port'] = int(self.configArgs['port'].text())      
            self.config_map['dingdingTime'] = int(self.configArgs['dingdingTime'].text())
            self.config_map['resultTime'] = int(self.configArgs['resultTime'].text())
            self.config_map['errorTime'] = int(self.configArgs['errorTime'].text())