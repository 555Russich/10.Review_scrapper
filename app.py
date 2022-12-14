import sys
from multiprocessing import freeze_support
from threading import Thread
from scrap import Scrapper
from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(420, 327)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.input_url = QtWidgets.QLineEdit(self.centralwidget)
        self.input_url.setObjectName("input_url")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.input_url)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.button_collect_data = QtWidgets.QPushButton(self.centralwidget)
        self.button_collect_data.setMaximumSize(QtCore.QSize(399, 16777215))
        self.button_collect_data.setObjectName("button_collect_data")
        self.horizontalLayout.addWidget(self.button_collect_data)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.console = QtWidgets.QTextEdit(self.centralwidget)
        self.console.setReadOnly(True)
        self.console.setObjectName("console")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.console)
        self.verticalLayout.addLayout(self.formLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        self.add_functions()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "???????????? ??????????????"))
        self.input_url.setText(_translate("MainWindow", "?????????????? URL"))
        self.button_collect_data.setText(_translate("MainWindow", "????????"))

    def add_functions(self):
        self.button_collect_data.clicked.connect(self.run_collect_data)

    def run_collect_data(self):
        self.console.clear()
        try:
            url = self.get_url()
        except InvalidUrl as err:
            print(str(err))
            return

        self.console.append('???????????? ??????????????...')
        self.thread = QtCore.QThread()
        self.worker = Worker(url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

        self.button_collect_data.setEnabled(False)
        self.thread.finished.connect(self.after_finished_thread)

    def after_finished_thread(self):
        self.button_collect_data.setEnabled(True)
        self.console.append('???????????????????? ?????????????? ??????????????????')

    def get_url(self):
        values = self.input_url.text().split('/')
        match values:
            case scheme, _, domain, *args:
                match scheme:
                    case 'https:' | 'http:':
                        pass
                    case _:
                        raise InvalidUrl('???????????????????????? URL')

                match domain.split('.'):
                    case _, website, _:
                        match website:
                            case 'booking':
                                pass
                            case _:
                                raise InvalidUrl('???????????? ???????? ???? ????????????????????????????')
                    case _:
                        raise InvalidUrl('???????????????????????? URL')

                match args:
                    case ['']:
                        raise InvalidUrl('???????????????????????? URL')
            case _:
                raise InvalidUrl('???????????????????????? URL')

        return self.input_url.text()

    def normalOutputWritten(self, text):
        self.console.append(text)


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        Scrapper().scrap_page(self.url)
        self.finished.emit()


class InvalidUrl(Exception):
    pass


if __name__ == "__main__":
    freeze_support()
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
