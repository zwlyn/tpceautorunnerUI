#!/usr/bin/python3

from PyQt5.QtCore import *


class SignalManager(QObject):

    startTest = pyqtSignal() 

    startArgsChanged = pyqtSignal(dict)

    configArgsChanged = pyqtSignal(dict)

    def __init__(self):
        super(SignalManager, self).__init__()

signalManager = SignalManager()
