
from PyQt5.QtWidgets import *
from app import TpceApp

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    tpceApp = TpceApp()
    tpceApp.show()

    sys.exit(app.exec_())