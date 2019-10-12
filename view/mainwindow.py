#!/usr/bin/python3
# -*- coding-utf_8 -*-
import os
import re
import sys
import json
import time
from PyQt5.QtGui import QIcon
import PyQt5.QtGui as QtGui

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import random
from log import logger
#from TPCEAutoRunner import tpceautorunner, TwoHouerTradeResultJob
from threading import Thread
from .plotBox import PlotBox
from .settingBox import SettingBox
from log import logger
from app import signalManager


class TPCEAutoRunnerUI(QDialog):  # 需要研究example 之后使用QMainWindows

    def __init__(self):
        super(TPCEAutoRunnerUI, self).__init__()
        self.initData()
        self.initUI()
        self.initConnect()

    def initData(self):
        pass

    def initUI(self):
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

        self.leftlist.setStyleSheet("QListWidget{color:rgb(0,0,0); background:rgb(255,255,255);border:0px solid gray;}"
                                     "QListWidget::Item{height:40px;border:0px solid gray;padding-left:0;color:rgb(0,0,0);}"
                                     "QListWidget::Item:hover{color:rgb(0,200,200);border:0px solid gray;}"
                                     "QListWidget::Item:{color:rgb(0,0,0);border:0px solid gray;}"
                                     "QListWidget::Item:selected:active{background:rgb();color:rgb(0,0,0);border-width:0;}"
                                     "QListWidget::Item[0]{color:rgb(255,0,0);border:0px solid gray;}"
                                    )

        self.reportBox = QGroupBox()
        self.plotBox = PlotBox()
        
        self.settingBox = SettingBox()
        self.settingBox.resize(1220, 700)
        self.settingBox.setFixedSize(1220, 700)

        self.init_reportBox()

        self.stack = QStackedWidget(self)

        self.stack.addWidget(self.settingBox)
        self.stack.addWidget(self.plotBox)
        self.stack.addWidget(self.reportBox)

        mainLayout = QVBoxLayout()

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

    def initConnect(self):
        #单机出发绑定的糟函数
        self.leftlist.itemClicked.connect(self.start_clicked)
        self.leftlist.currentRowChanged.connect(self.display)

        # # 每3秒存储一次结果
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.save_date)
        # self.timer.start(3000)

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
        

    # 关闭窗口时会执行累的close方法，并触发QCloseEvent信号，进而执行closeEvent(self,QCloseEvent)方法
    def closeEvent(self, event):
        logger.info('正在关闭APP')
        reply = QMessageBox.question(self, '本程序',
                                           "是否要退出程序？",
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def start_clicked(self,item):
        if item.text() == '启动':
            logger.info('点击了启动item，开始启动 ～～')

            signalManager.startTest.emit()

    def display(self,i):
        #设置当前可见的选项卡的索引
        self.stack.setCurrentIndex(i)







