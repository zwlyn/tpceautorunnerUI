#!/usr/bin/python3
# -*- coding-utf_8 -*-
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FC
from log import logger
from app import signalManager

class PlotBox(QWidget):
# 为什么__init__里面有parent=None，super()里要放自己和self，__init__(parent)
	def __init__(self, parent=None):
		super(PlotBox,self).__init__(parent)
		self.initData()
		self.initUI()
		self.initConnect()

	def initData(self):
		pass

	def initUI(self):
		self.plotBox = QGroupBox('测试图像')
        layout = QVBoxLayout()

        self.plt = plt
        self.fig = plt.figure(num=1, figsize=(15, 8),dpi=80)  
        self.canvas = FC(self.fig)
        layout.addWidget(self.canvas)


        self.plotBox.setLayout(layout)

	def initConnect(self):
		pass

plotBox = PlotBox()

    def handlePlot(self):
        logger.info('handlePlot')
        self.times = [1,2,3]
        self.tpsEs = [1,2,3]
        i = 1
        while True: # ------------

            _minCount = min(len(self.times), len(self.tpsEs))
            minCount  =  _minCount
            self.plot(self.times[0:minCount], self.tpsEs[0:minCount])

            #plt.pause(3)  #暂停一秒
            plt.ioff()
            logger.info(u'绘图更新成功！')
            time.sleep(3)
            self.times.append(i)
            self.tpsEs.append(i*i + 2)
            i += 1


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
        self.plt.clf()
        self.plt.title("Test Run Graph")
        self.plt.xlabel("Elapsed Time in Minutes")
        self.plt.ylabel("Trade-Result Transcations Per Second")
        self.plt.plot(xData, yData)
        self.canvas.draw()  # 在pyqt上的图像:从这里开始绘制
        self.plt.axis([min(xData), max(xData), min(yData), max(yData) + 2])
        self.plt.ioff()


    def drawMIStartEnd(self, job):
        self.drawLine((job.rampuptime(), job.tpsE() + 1), (job.rampuptime(), job.tpsE() + 1.5), "Begin Steady State")
        self.drawLine((job.MIEnd() + 10, job.tpsE() + 1), (job.MIEnd() + 10, job.tpsE() + 1.5), "End Steady State")
        self.drawArrow((job.MIStart(), job.tpsE() - 0.1), "MI Start", 3)
        self.drawArrow((job.MIEnd(), job.tpsE() - 0.1), "MI End", 3)

    def close(self):
        self.plt.close()

    def savefig(self, path):
        self.plt.savefig(path)