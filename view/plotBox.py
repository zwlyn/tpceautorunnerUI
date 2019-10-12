#!/usr/bin/python3
# -*- coding-utf_8 -*-
import time
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FC
from log import logger
from app import signalManager
from threading import Thread

class PlotBox(QWidget):

    def __init__(self, parent=None):
        super(PlotBox,self).__init__(parent)
        self.initData()
        self.initUI()
        self.initConnect()

    def initData(self):
        pass

    def initUI(self):

        layout = QVBoxLayout()

        self.plt = plt
        self.fig = plt.figure(num=1, figsize=(15, 8),dpi=80)  
        self.canvas = FC(self.fig)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def initConnect(self):
        signalManager.startTest.connect(self.plot_solt)

    def plot_solt(self): 
        #tpceautorunner.run_back()
        poltThread = Thread(target = self.handlePlot)
        poltThread.start()

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

    # def handlePlot(self):
    #     def actionShot():
    #         self.lastPng = os.sep.join([tpceautorunner.paths["screenshots"], tpceautorunner.resultName(int(tpceautorunner.lastResultTime), "jpg")])
    #         plt.savefig(self.lastPng)
    #         logger.info(u'截图%s保存成功！' % self.lastPng)

    #     while True: # ------------
    #         try:
    #             if tpceautorunner.isStarted and tpceautorunner.isGetResultSuccessed:
    #                 _minCount = min(len(tpceautorunner.times),len(tpceautorunner.tpsEs))
    #                 minCount  =  _minCount
    #                 self.plot(tpceautorunner.times[0:minCount], tpceautorunner.tpsEs[0:minCount])
    #                 job = TwoHouerTradeResultJob.BestJob
    #                 if job:
    #                     self.drawMIStartEnd(job)

    #                 plt.pause(int(self.config_map['resultTime']))  #暂停一秒
    #                 plt.ioff()
    #                 logger.info(u'绘图更新成功！')
    #                 if  len(tpceautorunner.tpsEs) > 0:
    #                     actionShot()

    #                 if is_exit:
    #                     actionShot()

    #         except Exception as e:
    #             logger.error(traceback.format_exc(e))
    #             logger.error(u'绘图更新失败')
    #             logger.error(repr(e))
