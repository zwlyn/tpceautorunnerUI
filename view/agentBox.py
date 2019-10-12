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

class AgentBox(QWidget):

	def __init__(self, parent=None):
		super(AgentBox, self).__init__(parent)
		self.initData()
		self.initUI()
		self.initConnect()

	def initData(self):
		self.start_map = load_json('start.json')
		self.agentArgs = {
		"ip": QLineEdit(),
		"port": QLineEdit(),
		"concurrency": QLineEdit(),
		"instance": QLineEdit(),
		"startid": QLineEdit(),
		"endid": QLineEdit(),
		"delay": QLineEdit()
		}

	def initUI(self):
		layout = QHBoxLayout()

		argsBox = QWidget()
		argsLayout = QFormLayout()
		argsLayout.addRow(QLabel("TPCEAgent配置:"))
		argsLayout.addRow(QLabel("IP地址:"), self.agentArgs['ip'])
		argsLayout.addRow(QLabel("端口号:"), self.agentArgs['port'])
		argsLayout.addRow(QLabel("并发数:"), self.agentArgs['concurrency'])
		argsLayout.addRow(QLabel("实例数:"), self.agentArgs['instance'])
		argsLayout.addRow(QLabel("起始id:"), self.agentArgs['startid'])
		argsLayout.addRow(QLabel("终止id:"), self.agentArgs['endid'])
		argsLayout.addRow(QLabel("延迟:"), self.agentArgs['delay'])
		argsBox.setLayout(argsLayout)

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

		layout.addWidget(self.listAgent)
		layout.addWidget(argsBox)

		self.setLayout(layout)

	def initConnect(self):
		self.init_agent()
		self.agentArgs['ip'].textEdited.connect(self.modify_agent)
		self.agentArgs['port'].textEdited.connect(self.modify_agent)
		self.agentArgs['concurrency'].textEdited.connect(self.modify_agent)
		self.agentArgs['instance'].textEdited.connect(self.modify_agent)
		self.agentArgs['startid'].textEdited.connect(self.modify_agent)
		self.agentArgs['endid'].textEdited.connect(self.modify_agent)
		self.agentArgs['delay'].textEdited.connect(self.modify_agent)

		self.listAgent.itemClicked.connect(self.remove_agent)
		self.listAgent.itemClicked.connect(self.add_agent)
		self.listAgent.itemClicked.connect(self.select_agent)

	def init_agent(self):
		for agent in self.start_map['agents']:
			self.listAgent.addItem('Agent%d' % (len(self.listAgent) - 1))

	def add_agent(self, item):
		if item.text() == '新建TPCEAgent':
			self.listAgent.addItem('Agent%d' % (len(self.listAgent) - 1))
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

			signalManager.startArgsChanged.emit(self.start_map)

	def remove_agent(self):
		'''
		每次删除最后一个agent
		'''
		currentItem = self.listAgent.currentItem()
		if currentItem.text() == '删除TPCEAgent':
			agentid = len(self.listAgent) - 1
			self.listAgent.takeItem(agentid)
			self.start_map['agents'].pop()

	def modify_agent(self):
		logger.info('self.sender().text():  ' + self.sender().text())
		currentItem = self.listAgent.currentItem()
		agentid = int(currentItem.text()[5:]) -1
		self.start_map['agents'][agentid]['ip'] = self.agentArgs['ip'].text()

		if self.agentArgs['port'].text() != "":
			self.start_map['agents'][agentid]['port'] = int(self.agentArgs['port'].text())
		if self.agentArgs['concurrency'].text() != "":
			self.start_map['agents'][agentid]['concurrency'] = int(self.agentArgs['concurrency'].text())
		if self.agentArgs['instance'].text() != "":
			self.start_map['agents'][agentid]['instance'] = int(self.agentArgs['instance'].text())
		if self.agentArgs['startid'].text() != "":
			self.start_map['agents'][agentid]['startid'] = int(self.agentArgs['startid'].text())
		if self.agentArgs['endid'].text() != "":
			self.start_map['agents'][agentid]['endid'] = int(self.agentArgs['endid'].text())
		if self.agentArgs['delay'].text() != "":
			self.start_map['agents'][agentid]['delay'] = int(self.agentArgs['delay'].text())

			signalManager.startArgsChanged.emit(self.start_map)

	def select_agent(self, item):

		if not item.text() == '新建TPCEAgent' and not item.text() == '删除TPCEAgent':
			agentid = int(item.text()[5:]) - 1 

			self.agentArgs['ip'].setText(str(self.start_map['agents'][agentid]['ip']))
			self.agentArgs['port'].setText(str(self.start_map['agents'][agentid]['port']))
			self.agentArgs['concurrency'].setText(str(self.start_map['agents'][agentid]['concurrency']))
			self.agentArgs['instance'].setText(str(self.start_map['agents'][agentid]['instance']))
			self.agentArgs['startid'].setText(str(self.start_map['agents'][agentid]['startid']))
			self.agentArgs['endid'].setText(str(self.start_map['agents'][agentid]['endid']))
			self.agentArgs['delay'].setText(str(self.start_map['agents'][agentid]['delay']))



