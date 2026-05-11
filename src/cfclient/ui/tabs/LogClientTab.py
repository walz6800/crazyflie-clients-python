#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2011-2023 Waymark AB
#
#  Aeroflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License along with
#  this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
Shows information from the Python logging framework
"""

import logging

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCursor

import cfclient
from cfclient.ui.tab_toolbox import TabToolbox

__author__ = 'Waymark AB'
__all__ = ['LogClientTab']

logger = logging.getLogger(__name__)

log_client_tab_class = uic.loadUiType(cfclient.module_path + "/ui/tabs/logClientTab.ui")[0]


class LogHandler(logging.StreamHandler):
    def __init__(self, signal):
        logging.StreamHandler.__init__(self)
        self._signal = signal

    def emit(self, record):
        fmt = '%(levelname)s:%(name)s:%(message)s'
        formatter = logging.Formatter(fmt)
        #
        # Calling .emit() on the signal will make the callback
        # we registered in LogClientTab run.
        #
        self._signal.emit(formatter.format(record))


class LogClientTab(TabToolbox, log_client_tab_class):
    """
    A tab for showing client logging information, such
    as USB Gamepad connections or scan feedback.
    """
    _update = pyqtSignal(str)

    def __init__(self, helper):
        super(LogClientTab, self).__init__(helper, 'Log Hub')
        self.setupUi(self)

        self._update.connect(self.printText)
        self._clearButton.clicked.connect(self.clear)

        # 最大保留行数，防止 QTextDocument 文本无界增长导致内存泄漏
        self._max_blocks = 5000

        cflogger = logging.getLogger(None)
        self._log_handler = LogHandler(self._update)
        cflogger.addHandler(self._log_handler)

    def printText(self, text):
        # 直接插入文本，不再次记录日志以避免无限递归循环
        self.syslog.insertPlainText(text + '\n')
        # 超过上限时删除最早的行，QTextEdit 无 setMaximumBlockCount
        doc = self.syslog.document()
        if doc.blockCount() > self._max_blocks + 200:
            excess = doc.blockCount() - self._max_blocks
            block = doc.findBlockByNumber(excess)
            if block.isValid():
                cursor = QTextCursor(doc.begin())
                end = QTextCursor(block)
                cursor.setPosition(end.position(), QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()

    def clear(self):
        self.syslog.clear()
