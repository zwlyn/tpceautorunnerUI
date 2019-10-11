#!/usr/bin/python3

from PyQt5.QtCore import *


class SignalManager(QObject):

    buttonClicked = pyqtSignal(str) # view发送到controller

    nameChanged = pyqtSignal(str) # controller发送回View

    def __init__(self):
        super(SignalManager, self).__init__()

signalManager = SignalManager()
