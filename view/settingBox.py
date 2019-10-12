#!/usr/bin/python3
# -*- coding-utf_8 -*-
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from log import logger
from app import signalManager
from .startBox import StartBox
from .configBox import ConfigBox

class SettingBox(QWidget):

    def __init__(self, parent=None):
        super(SettingBox,self).__init__(parent)
        self.initData()
        self.initUI()
        self.initConnect()

    def initData(self):
        pass

    def initUI(self):


        self.mainLayout = QVBoxLayout()
        self.mainTab = QTabWidget()

        startTab = StartBox()
        configTab = ConfigBox()
        
        self.mainTab.addTab(startTab, '启动参数')
        self.mainTab.addTab(configTab, '配置参数')

        self.mainLayout.addWidget(self.mainTab)




        self.setLayout(self.mainLayout)

    def initConnect(self):
        pass

