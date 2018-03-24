# -*- coding: utf-8 -*-
# Licensed under the GPLv3
# 本项目由@Everyb0dyLies开发维护，使用python3

from main_window import *
from liarcom import *
import sys
#from PyQt5.QtGui import 
#from PyQt5.QtCore import 
#from PyQt5.QtWidgets import 


class MainWindowController:
    def __init__(self):
        self._liarcom = Liarcom()
        
        self._window = MainWindow(self)
        self.update()

    @property
    def window(self):
        return self._window

    def update(self):
        pass

