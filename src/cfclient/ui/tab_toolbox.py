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
Superclass for all tabs that implements common functions.
"""

import logging

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent

from cfclient.utils.config import Config

__author__ = 'Waymark AB'
__all__ = ['TabToolbox']

logger = logging.getLogger(__name__)


class TabToolbox(QtWidgets.QWidget):
    """Superclass for all tabs that implements common functions."""

    CONF_KEY_OPEN_TABS = "open_tabs"
    CONF_KEY_OPEN_TOOLBOXES = "open_toolboxes"
    CONF_KEY_TOOLBOX_AREAS = "toolbox_areas"

    # Display states
    DS_HIDDEN = 0
    DS_TAB = 1
    DS_TOOLBOX = 2

    def __init__(self, helper, tab_toolbox_name):
        super(TabToolbox, self).__init__()
        self._helper = helper
        # 保存原始英文名称作为配置键值（稳定不变）和初始显示名
        self._tab_config_key = tab_toolbox_name
        self.tab_toolbox_name = self.tr(tab_toolbox_name)

        # Dock widget for toolbox behavior (set window title via translated name)
        self.dock_widget = self.ClosingDockWidget(self.tab_toolbox_name)
        self.dock_widget.tab_toolbox = self

        self._display_state = self.DS_HIDDEN

        self._dock_area = self._get_toolbox_area_config()

        # Do not allow floating toolboxes, it seems to be buggy
        self.dock_widget.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable |
                                     QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # If floating is set in the config, change to right docking area
        if self._dock_area == Qt.DockWidgetArea.NoDockWidgetArea:
            self._dock_area = Qt.DockWidgetArea.RightDockWidgetArea

    def get_tab_toolbox_name(self):
        """返回当前语言的显示名称，用于标签页或工具箱标题"""
        return self.tr(self._tab_config_key)

    def get_tab_config_key(self):
        """返回稳定的英文配置键值，用于配置文件存储"""
        return self._tab_config_key

    def is_visible(self):
        return self._display_state != self.DS_HIDDEN

    def get_display_state(self):
        return self._display_state

    def set_display_state(self, new_display_state):
        if new_display_state != self._display_state:
            self._display_state = new_display_state
            self._update_open_config(new_display_state)

            if new_display_state == self.DS_HIDDEN:
                self.disable()
            else:
                self.enable()

    def preferred_dock_area(self):
        return self._dock_area

    def set_preferred_dock_area(self, area):
        self._dock_area = area
        self._store_toolbox_area_config(area)

    def enable(self):
        pass

    def disable(self):
        pass

    # 不应在启动时自动打开的标签页（含 OpenGL 重量级组件，需用户手动打开）
    # 同时包含中英文名称，因为配置文件可能存储了任意语言的版本
    MANUAL_OPEN_TABS = {'Optics Positioning', 'Wireless Positioning',
                        '光学定位', '无线定位'}

    @classmethod
    def read_open_tab_config(cls):
        config = cls._read_open_config(TabToolbox.CONF_KEY_OPEN_TABS)
        return [name for name in config if name not in cls.MANUAL_OPEN_TABS]

    @classmethod
    def read_open_toolbox_config(cls):
        return TabToolbox._read_open_config(TabToolbox.CONF_KEY_OPEN_TOOLBOXES)

    @classmethod
    def _read_open_config(cls, key):
        config = []
        try:
            value = Config().get(key)
            # Python will return a list of an empty string if value is empty, filter it
            config = list(filter(None, value.split(",")))
        except KeyError:
            logger.debug(f'No config found for {key}')

        return config

    def _update_open_config(self, display_state):
        if display_state == self.DS_HIDDEN:
            self._remove_from_open_config(TabToolbox.CONF_KEY_OPEN_TABS)
            self._remove_from_open_config(TabToolbox.CONF_KEY_OPEN_TOOLBOXES)
        elif display_state == self.DS_TAB:
            self._add_to_open_config(TabToolbox.CONF_KEY_OPEN_TABS)
            self._remove_from_open_config(TabToolbox.CONF_KEY_OPEN_TOOLBOXES)
        elif display_state == self.DS_TOOLBOX:
            self._remove_from_open_config(TabToolbox.CONF_KEY_OPEN_TABS)
            self._add_to_open_config(TabToolbox.CONF_KEY_OPEN_TOOLBOXES)

    def _add_to_open_config(self, key):
        config = self._read_open_config(key)
        name = self._tab_config_key

        if name not in config:
            config.append(name)
            self._store_open_config(key, config)

    def _remove_from_open_config(self, key):
        config = self._read_open_config(key)
        name = self._tab_config_key

        if name in config:
            config.remove(name)
            self._store_open_config(key, config)

    def _store_open_config(self, key, config):
        value = ','.join(config)
        Config().set(key, value)

    def _get_toolbox_area_config(self):
        result = Qt.DockWidgetArea.RightDockWidgetArea

        config = self._read_toolbox_area_config()

        if self._tab_config_key in config.keys():
            result = Qt.DockWidgetArea(config[self._tab_config_key])

        return result

    def _store_toolbox_area_config(self, area):
        config = self._read_toolbox_area_config()
        config[self._tab_config_key] = area.value
        self._write_toolbox_area_config(config)

    def _read_toolbox_area_config(self):
        composite_config = []
        try:
            key = self.CONF_KEY_TOOLBOX_AREAS
            value = Config().get(key)
            # Python will return a list of an empty string if value is empty, filter it
            composite_config = list(filter(None, value.split(",")))
        except KeyError:
            logger.debug(f'No config found for {key}')

        config = {}
        for composite in composite_config:
            try:
                parts = composite.split(':')
                config[parts[0]] = int(parts[1])
            except (KeyError, ValueError):
                logger.info(f'Can not understand config {composite}')

        return config

    def _write_toolbox_area_config(self, config):
        key = self.CONF_KEY_TOOLBOX_AREAS
        value = ','.join(map(lambda item: f'{item[0]}:{item[1]}', config.items()))
        Config().set(key, value)

    class ClosingDockWidget(QtWidgets.QDockWidget):
        closed = pyqtSignal()

        def closeEvent(self, event: QCloseEvent) -> None:
            super(TabToolbox.ClosingDockWidget, self).closeEvent(event)
            self.closed.emit()
