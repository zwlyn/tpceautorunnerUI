#!/usr/bin/python3
# -*- coding-utf_8 -*-
import json
from log import logger
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from app import signalManager
from .agentBox import AgentBox

def load_json(fpath):
    with open(fpath,'r', encoding='utf-8') as f:
        dict_data = json.loads(f.read())
    return dict_data

class StartBox(QWidget):

    def __init__(self, parent=None):
        super(StartBox,self).__init__(parent)
        self.initData()
        self.initUI()
        self.initConnect()

    def initData(self):
        self.start_map = load_json('start.json')
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

    def initUI(self): 
        layout = QHBoxLayout()
        layout_args = QFormLayout()


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

        layout_args.addRow(QLabel("用户数量:"), self.startArgs['customer'])
        layout_args.addRow(QLabel("初始天数:"), self.startArgs['initialdays'])
        layout_args.addRow(QLabel("比例因子:"), self.startArgs['scalefactor'])
        layout_args.addRow(QLabel("上升时长:"), self.startArgs['uptime'])
        layout_args.addRow(QLabel("测试时长:"), self.startArgs['testtime'])
        layout_args.addRow(QLabel("数据库配置:"))
        layout_args.addRow(QLabel("IP地址:"), self.startArgs['dbconfig']['ip'])
        layout_args.addRow(QLabel("端口号:"), self.startArgs['dbconfig']['port'])
        layout_args.addRow(QLabel("用户名:"), self.startArgs['dbconfig']['username'])
        layout_args.addRow(QLabel("密码:"), self.startArgs['dbconfig']['password'])
        layout_args.addRow(QLabel("数据库实例名:"), self.startArgs['dbconfig']['dbname'])
        layout_args.addRow(QLabel("数据库类别:"), self.startArgs['dbconfig']['dbtype'])

        agentBox = AgentBox()
               
        layout.addLayout(layout_args)
        layout.addWidget(agentBox)

        self.setLayout(layout)


        # 将startBox放入标签中

    def initConnect(self):
        # 设置start的信号糟，当行内容修改结束时进行修改
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