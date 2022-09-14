import time
import sys
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
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.input_url.setText(_translate("MainWindow", "Введите URL"))
        self.button_collect_data.setText(_translate("MainWindow", "Пуск"))

    def add_functions(self):
        self.button_collect_data.clicked.connect(self.run_collect_data)

    def run_collect_data(self):
        self.console.clear()
        self.console.append('Скрипт запущен...')
        app.processEvents()
        url = self.get_url()
        Scrapper().scrap_page(url)
        self.console.append('Выполнение скрипта завершено')

    def get_url(self):
        text = self.input_url.text()
        return text

    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        # Maybe QTextEdit.append() works as well, but this is how I do it:
        cursor = self.console.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))


class InvalidUrl(BaseException):
    pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
