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
The about dialog.
"""

import sys

import cfclient
import cflib.crtp
from PyQt6.QtCore import QT_VERSION_STR
from PyQt6.QtCore import PYQT_VERSION_STR
from PyQt6 import QtWidgets
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from cflib.crazyflie.mem import MemoryElement

__author__ = 'Waymark AB'
__all__ = ['AboutDialog']

(about_widget_class,
 about_widget_base_class) = (uic.loadUiType(cfclient.module_path +
                                            '/ui/dialogs/about.ui'))

INTERFACE_FORMAT = "{}: {}<br>"
INPUT_READER_FORMAT = "{} ({} devices connected)<br>"
DEVICE_FORMAT = "{}: ({}) {}<br>"
IMU_SENSORS_FORMAT = "{}: {}<br>"
SENSOR_TESTS_FORMAT = "{}: {}<br>"
FIRMWARE_FORMAT = "{:x}{:x} ({})"
DECK_FORMAT = "{}: rev={}, adr={}<br>"


class AboutDialog(QtWidgets.QWidget, about_widget_class):
    _disconnected_signal = pyqtSignal(str)
    _cb_deck_data_updated_signal = pyqtSignal(object)

    """Aeroflie client About box for debugging and information"""

    def __init__(self, helper, *args):
        super(AboutDialog, self).__init__(*args)
        self.setupUi(self)
        self._close_button.clicked.connect(self.close)
        self._name_label.setText(
            self._name_label.text().replace('#version#', cfclient.VERSION))

        self._interface_text = ""
        self._imu_sensors_text = ""
        self._imu_sensor_test_text = ""
        self._decks_text = ""
        self._uri = None
        self._fw_rev0 = None
        self._fw_rev1 = None
        self._fw_modified = None
        self._firmware = None

        self._helper = helper

        helper.cf.param.add_update_callback(
            group="imu_sensors", cb=self._imu_sensors_update)
        helper.cf.param.add_update_callback(
            group="imu_tests", cb=self._imu_sensor_tests_update)
        helper.cf.param.add_update_callback(
            group="firmware", cb=self._firmware_update)
        helper.cf.connected.add_callback(self._connected)

        self._disconnected_signal.connect(self._disconnected)
        helper.cf.disconnected.add_callback(self._disconnected_signal.emit)

        self._cb_deck_data_updated_signal.connect(self._deck_data_updated)

    def showEvent(self, event):
        """Event when the about box is shown"""
        self._interface_text = ""
        interface_status = cflib.crtp.get_interfaces_status()
        for key in list(interface_status.keys()):
            self._interface_text += INTERFACE_FORMAT.format(
                key, interface_status[key])

        self._device_text = ""
        devs = self._helper.inputDeviceReader.available_devices()
        for d in devs:
            self._device_text += DEVICE_FORMAT.format(
                d.reader_name, d.id, d.name)
        if len(self._device_text) == 0:
            self._device_text = self.tr("None") + "<br>"

        self._input_readers_text = ""
        # readers = self._helper.inputDeviceReader.getAvailableDevices()
        for reader in cfclient.utils.input.inputreaders.initialized_readers:
            self._input_readers_text += INPUT_READER_FORMAT.format(
                reader.name, len(reader.devices()))
        if len(self._input_readers_text) == 0:
            self._input_readers_text = self.tr("None") + "<br>"

        if self._uri:
            self._firmware = FIRMWARE_FORMAT.format(
                self._fw_rev0,
                self._fw_rev1,
                self.tr("MODIFIED") if self._fw_modified else self.tr("CLEAN"))

            self._request_deck_data_update()

        self._update_debug_info_view()

    def _sanitize_dynamic_text(self, text):
        """替换动态数据中的品牌名称"""
        if not text:
            return text
        text = text.replace('cfclient', 'FormflieHub')
        text = text.replace('Cfclient', 'FormflieHub')
        text = text.replace('Crazyflie', 'Aeroflie')
        text = text.replace('crazyflie', 'Aeroflie')
        text = text.replace('Crazyradio', 'AeroRadio')
        text = text.replace('Lighthouse positioning', 'Optics positioning')
        text = text.replace('Loco positioning', 'wireless positioning')
        return text

    def _update_debug_info_view(self):
        html = (
            "<b>FormflieHub</b><br>"
            + self.tr("FormflieHub version: {version}") + "<br>"
            + self.tr("System: {system}") + "<br>"
            + self.tr("Python: {pmajor}.{pminor}.{pmicro}") + "<br>"
            + self.tr("Qt: {qt_version}") + "<br>"
            + self.tr("PyQt: {pyqt_version}") + "<br>"
            + "<br>"
            + "<b>" + self.tr("Interface status") + "</b><br>"
            + "{interface_status}" + "<br>"
            + "<b>" + self.tr("Input readers") + "</b><br>"
            + "{input_readers}" + "<br>"
            + "<b>" + self.tr("Input devices") + "</b><br>"
            + "{input_devices}" + "<br>"
            + "<b>Aeroflie</b><br>"
            + self.tr("Connected: {uri}") + "<br>"
            + self.tr("Firmware: {firmware}") + "<br>"
            + "<br>"
            + "<b>" + self.tr("Decks found") + "</b><br>"
            + "{decks}" + "<br>"
            + "<b>" + self.tr("Sensors found") + "</b><br>"
            + "{imu_sensors}" + "<br>"
            + "<b>" + self.tr("Sensors tests") + "</b><br>"
            + "{imu_sensor_tests}"
        ).format(
            version=cfclient.VERSION,
            system=sys.platform,
            pmajor=sys.version_info.major,
            pminor=sys.version_info.minor,
            pmicro=sys.version_info.micro,
            qt_version=QT_VERSION_STR,
            pyqt_version=PYQT_VERSION_STR,
            interface_status=self._sanitize_dynamic_text(self._interface_text),
            input_devices=self._sanitize_dynamic_text(self._device_text),
            input_readers=self._sanitize_dynamic_text(self._input_readers_text),
            uri=self._sanitize_dynamic_text(self._uri) if self._uri else self._uri,
            firmware=self._sanitize_dynamic_text(self._firmware) if self._firmware else self._firmware,
            imu_sensors=self._sanitize_dynamic_text(self._imu_sensors_text),
            imu_sensor_tests=self._sanitize_dynamic_text(self._imu_sensor_test_text),
            decks=self._sanitize_dynamic_text(self._decks_text))
        self._debug_out.setHtml(html)

    def _connected(self, uri):
        """Callback when Aeroflie is connected"""
        self._uri = uri

    def _firmware_update(self, name, value):
        """Callback for firmware parameters"""
        if "revision0" in name:
            self._fw_rev0 = eval(value)
        if "revision1" in name:
            self._fw_rev1 = eval(value)
        if "modified" in name:
            self._fw_modified = eval(value)

    def _imu_sensors_update(self, name, value):
        """Callback for sensor found parameters"""
        param = name[name.index('.') + 1:]
        if param not in self._imu_sensors_text:
            self._imu_sensors_text += IMU_SENSORS_FORMAT.format(
                param, eval(value))

    def _imu_sensor_tests_update(self, name, value):
        """Callback for sensor test parameters"""
        param = name[name.index('.') + 1:]
        if param not in self._imu_sensor_test_text:
            self._imu_sensor_test_text += SENSOR_TESTS_FORMAT.format(
                param, eval(value))

    def _disconnected(self, uri):
        """Callback for Aeroflie disconnected"""
        self._interface_text = ""
        self._imu_sensors_text = ""
        self._imu_sensor_test_text = ""
        self._decks_text = ""
        self._uri = None
        self._fw_rev1 = None
        self._fw_rev0 = None
        self._fw_modified = None
        self._firmware = None

    def _request_deck_data_update(self):
        self._decks_text = ""
        # Query both 1-Wire and DeckCtrl memories for deck information
        mems = self._helper.cf.mem.get_mems(MemoryElement.TYPE_1W)
        mems += self._helper.cf.mem.get_mems(MemoryElement.TYPE_DECKCTRL)
        for mem in mems:
            mem.update(self._cb_deck_data_updated_signal.emit)

    def _deck_data_updated(self, deck_data):
        name = self.tr('N/A')
        if "Board name" in deck_data.elements:
            name = deck_data.elements["Board name"]

        rev = self.tr('N/A')
        if "Board revision" in deck_data.elements:
            rev = deck_data.elements["Board revision"]

        # OWElement has addr attribute, DeckCtrlElement does not
        addr = getattr(deck_data, 'addr', self.tr('N/A'))
        self._decks_text += DECK_FORMAT.format(name, rev, addr)

        self._update_debug_info_view()
