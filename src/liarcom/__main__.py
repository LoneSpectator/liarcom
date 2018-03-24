# -*- coding: utf-8 -*-
# Licensed under the GPLv3
# 本项目由@Everyb0dyLies开发维护，使用python3
# 目前为测试版，win7, ubuntu1604测试通过，如有任何问题欢迎在本项目的github页面提交issue，或联系qq1768154526

import sys
from PyQt5.QtWidgets import QApplication
from main_window_controller import MainWindowController

#'''
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window_controller = MainWindowController()
    main_window_controller.window.show()
    sys.exit(app.exec_())

