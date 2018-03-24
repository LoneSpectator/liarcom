# -*- coding: utf-8 -*-
# Licensed under the GPLv3
# 本项目由@Everyb0dyLies开发维护，使用python3

from main_window import *
from liarcom import *
import sys, json
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QObject, QDir


class MainWindowController:
    def __init__(self):
        self._window = MainWindow(self)
        sys.stdout = OutStream(out_signal=self.print_log)
        self._window.retryCheckBox.stateChanged.connect(self.set_auto_relogin_flag)
        self._window.remPasswdCheckBox.stateChanged.connect(self.save_user_config)
        self._window.retryTimesSpinBox.valueChanged.connect(self.set_relogin_retry_times)
        self._window.timeoutSpinBox.valueChanged.connect(self.set_relogin_timeout)

        self._liarcom = Liarcom()
        if (not self.load_user_config()):
            self._window.retryCheckBox.setChecked(self._liarcom.auto_relogin_flag)
            self._window.retryTimesSpinBox.setValue(self._liarcom.relogin_retry_times)
            self._window.timeoutSpinBox.setValue(self._liarcom.relogin_timeout / 60)
            self._window.remPasswdCheckBox.setChecked(True)
        self.update()

    @property
    def window(self):
        return self._window

    def set_auto_relogin_flag(self):
        self._liarcom.auto_relogin_flag = self._window.retryCheckBox.isChecked()
        self.save_user_config()

    def set_relogin_retry_times(self):
        self._liarcom.relogin_retry_times = self._window.retryTimesSpinBox.value()
        self.save_user_config()

    def set_relogin_timeout(self):
        self._liarcom.relogin_timeout = self._window.timeoutSpinBox.value() * 60
        self.save_user_config()

    def login(self):
        self._liarcom.user = self._window.userNameLineEdit.text()
        self._liarcom.password = self._window.passwordLineEdit.text()
        self.save_user_config()
        self._liarcom.login()
        self.update()

    def logout(self):
        self._liarcom.logout()
        self.update()
    
    def load_user_config(self):
        file_path = QDir.homePath()
        if (sys.platform == "linux"):
            file_path = file_path + "/.liarcom-gui.cfg"
        else:
            file_path = file_path + "\\.liarcom-gui.cfg"
        try:
            f = open(file_path, 'r')
            file_data = f.read()
            f.close()
        except FileNotFoundError:
            return False

        cfg_dict = json.loads(file_data)
        self._window.retryCheckBox.setChecked(cfg_dict["auto_relogin"])
        self._window.retryTimesSpinBox.setValue(cfg_dict["retry_times"])
        self._window.timeoutSpinBox.setValue(cfg_dict["relogin_timeout"] / 60)
        self._window.remPasswdCheckBox.setChecked(cfg_dict["rem_pwd"])
        if cfg_dict["rem_pwd"]:
            self._window.userNameLineEdit.setText(cfg_dict["usr"])
            self._window.passwordLineEdit.setText(cfg_dict["pwd"])
        return True

    def save_user_config(self):
        file_path = QDir.homePath()
        if (sys.platform == "linux"):
            file_path = file_path + "/.liarcom-gui.cfg"
        else:
            file_path = file_path + "\\.liarcom-gui.cfg"
        cfg_dict = {"rem_pwd": self._window.remPasswdCheckBox.isChecked(), 
                    "auto_relogin": self._window.retryCheckBox.isChecked(), 
                    "retry_times": self._window.retryTimesSpinBox.value(),
                    "relogin_timeout": self._window.timeoutSpinBox.value() * 60}
        if self._window.remPasswdCheckBox.isChecked():
            cfg_dict["usr"] = self._window.userNameLineEdit.text()
            cfg_dict["pwd"] = self._window.passwordLineEdit.text()
        
        f = open(file_path, 'w')
        f.write(json.dumps(cfg_dict, sort_keys=True, indent=4))
        f.close()

    def update(self):
        if (self._liarcom.status == "offline"):
            self._window.userNameLineEdit.setEnabled(True)
            self._window.passwordLineEdit.setEnabled(True)
            self._window.remPasswdCheckBox.setEnabled(True)
            self._window.retryCheckBox.setEnabled(True)
            self._window.retryTimesSpinBox.setEnabled(True)
            self._window.timeoutSpinBox.setEnabled(True)
            self._window.loginButton.setText("登录")
            try:
                self._window.loginButton.clicked.disconnect()
            except Exception:
                pass
            self._window.loginButton.clicked.connect(self.login)
        else:
            self._window.userNameLineEdit.setEnabled(False)
            self._window.passwordLineEdit.setEnabled(False)
            self._window.remPasswdCheckBox.setEnabled(False)
            self._window.retryCheckBox.setEnabled(False)
            self._window.retryTimesSpinBox.setEnabled(False)
            self._window.timeoutSpinBox.setEnabled(False)
            self._window.loginButton.setText("登出")
            try:
                self._window.loginButton.clicked.disconnect()
            except Exception:
                pass
            self._window.loginButton.clicked.connect(self.logout)

    def print_log(self, str):
        self._window.logTextBrowser.insertPlainText(str)
        self._window.logTextBrowser.moveCursor(QTextCursor.End)
        self._window.logTextBrowser.horizontalScrollBar().setValue(0)


class OutStream(QObject):  
        out_signal = QtCore.pyqtSignal(str)
        def write(self, text):
            self.out_signal.emit(str(text))

