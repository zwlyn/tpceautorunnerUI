#!/usr/bin/python3

from PyQt5.QtCore import *
from controller import *
from view import TPCEAutoRunnerUI
from .signalmanager import signalManager
from log import logger

class TpceApp(object):

	def __init__(self):
		super(TpceApp, self).__init__()
		self.initView()
		self.initControllers()
		self.initConnect()

	def initView(self):
		self.tpceautorunnerUI = TPCEAutoRunnerUI()

	def initControllers(self):
		
		self.acontroller = AController()
		self.bcontroller = BController()
		self.ccontroller = CController()

		logger.info(self.acontroller)
		logger.info(self.bcontroller)
		logger.info(self.ccontroller)

	def initConnect(self):
		pass

	def show(self):
		self.tpceautorunnerUI.show()