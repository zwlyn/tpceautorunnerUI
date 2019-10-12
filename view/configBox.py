#!/usr/bin/python3
# -*- coding-utf_8 -*-
import json
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from log import logger
from app import signalManager

def load_json(fpath):
    with open(fpath,'r', encoding='utf-8') as f:
        dict_data = json.loads(f.read())
    return dict_data
    
class ConfigBox(QWidget):

    def __init__(self, parent=None):
        super(ConfigBox,self).__init__(parent)
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

        self.setLayout(configBox)

    def initConnect(self):
        self.configArgs['ip'].textEdited.connect(self.modify_configArgs)     
        self.configArgs['port'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['mapBedUrl'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['dingdingTime'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['resultTime'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['errorTime'].textEdited.connect(self.modify_configArgs)     
        self.configArgs['reportLanguage'].textEdited.connect(self.modify_configArgs)  
        self.configArgs['dingdingUrl'].textEdited.connect(self.modify_configArgs) 

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

        signalManager.configArgsChanged.emit(self.config_map)