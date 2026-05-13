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

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#  02110-1301, USA.

"""
Shows data for the Loco Positioning system
"""

import logging
from enum import Enum
from collections import namedtuple

import time
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWidgets import QLabel

import cfclient
from cfclient.ui.tab_toolbox import TabToolbox

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.mem import MemoryElement
from lpslib.lopoanchor import LoPoAnchor

from cfclient.ui.dialogs.anchor_position_dialog import AnchorPositionDialog

from vispy import scene
import numpy as np

__author__ = 'Waymark AB'
__all__ = ['LocoPositioningTab']

logger = logging.getLogger(__name__)

locopositioning_tab_class = uic.loadUiType(cfclient.module_path + "/ui/tabs/locopositioning_tab.ui")[0]

STYLE_RED_BACKGROUND = "background-color: lightpink;"
STYLE_GREEN_BACKGROUND = "background-color: lightgreen;"
STYLE_NO_BACKGROUND = "background-color: none;"


class Anchor:
    def __init__(self, x=0.0, y=0.0, z=0.0, distance=0.0):
        self.x = x
        self.y = y
        self.z = z
        self._is_position_valid = False
        self._is_active = False
        self.distance = distance

    def set_position(self, position):
        """Sets the position."""
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self._is_position_valid = True

    def get_position(self):
        """Returns the position as a vector"""
        return (self.x, self.y, self.z)

    def is_position_valid(self):
        return self._is_position_valid

    def set_is_active(self, is_active):
        self._is_active = is_active

    def is_active(self):
        return self._is_active


class AxisScaleStep:
    def __init__(self, from_view, from_axis, to_view, to_axis,
                 center_only=False):
        self.from_view = from_view.view
        self.from_axis = from_axis
        self.to_view = to_view.view
        self.to_axis = to_axis
        self.center_only = center_only


class Plot3dLps(scene.SceneCanvas):
    ANCHOR_BRUSH = np.array((0.2, 0.5, 0.2))
    ANCHOR_BRUSH_INVALID = np.array((0.8, 0.5, 0.5))
    HIGHLIGHT_ANCHOR_BRUSH = np.array((0, 1, 0))
    POSITION_BRUSH = np.array((0, 0, 1.0))

    VICINITY_DISTANCE = 2.5
    HIGHLIGHT_DISTANCE = 0.5

    LABEL_SIZE = 100
    LABEL_HIGHLIGHT_SIZE = 200

    ANCHOR_SIZE = 10
    HIGHLIGHT_SIZE = 20

    TEXT_OFFSET = np.array((0.0, 0, 0.25))

    def __init__(self):
        # autoswap=False: Qt QOpenGLWidget 已经处理 FBO 呈现，
        # 启用在 vispy 端会导致冗余交换和持续 60FPS 渲染从而占用内存
        scene.SceneCanvas.__init__(self, keys=None, autoswap=False)
        self.unfreeze()

        self._view = self.central_widget.add_view()
        self._view.bgcolor = '#ffffff'
        self._view.camera = scene.TurntableCamera(
            distance=10.0,
            up='+z',
            center=(0.0, 0.0, 1.0))

        self._cf = scene.visuals.Markers(
            pos=np.array([[0, 0, 0]]),
            parent=self._view.scene,
            face_color=self.POSITION_BRUSH)
        self._anchor_contexts = {}

        self.freeze()

        plane_size = 10
        scene.visuals.Plane(
            width=plane_size,
            height=plane_size,
            width_segments=plane_size,
            height_segments=plane_size,
            color=(0.5, 0.5, 0.5, 0.5),
            edge_color="gray",
            parent=self._view.scene)

        self.addArrows(1, 0.02, 0.1, 0.1, self._view.scene)

    def addArrows(self, length, width, head_length, head_width, parent):
        # The Arrow visual in vispy does not seem to work very good,
        # draw arrows using lines instead.
        w = width / 2
        hw = head_width / 2
        base_len = length - head_length

        # X-axis
        scene.visuals.LinePlot([
            [0, w, 0],
            [base_len, w, 0],
            [base_len, hw, 0],
            [length, 0, 0],
            [base_len, -hw, 0],
            [base_len, -w, 0],
            [0, -w, 0]],
            width=1.0, color='red', parent=parent, marker_size=0.0)

        # Y-axis
        scene.visuals.LinePlot([
            [w, 0, 0],
            [w, base_len, 0],
            [hw, base_len, 0],
            [0, length, 0],
            [-hw, base_len, 0],
            [-w, base_len, 0],
            [-w, 0, 0]],
            width=1.0, color='green', parent=parent, marker_size=0.0)

        # Z-axis
        scene.visuals.LinePlot([
            [0, w, 0],
            [0, w, base_len],
            [0, hw, base_len],
            [0, 0, length],
            [0, -hw, base_len],
            [0, -w, base_len],
            [0, -w, 0]],
            width=1.0, color='blue', parent=parent, marker_size=0.0)

    def update_data(self, anchors, pos, display_mode):
        self.update_cf_position(pos)

        for id, anchor in anchors.items():
            self._update_anchor(id, anchor, display_mode)

        self._purge_anchors(anchors.keys())

    def update_cf_position(self, pos):
        """仅更新无人机位置标记，不触碰 anchor visual。
        用于定时器高频回调，避免每帧向 GPU 上传不变的 anchor 数据。"""
        self._cf.set_data(pos=np.array([pos]), face_color=self.POSITION_BRUSH)

    def _update_anchor(self, id, anchor, display_mode):
        if anchor.is_active():
            color = self.ANCHOR_BRUSH
        else:
            color = self.ANCHOR_BRUSH_INVALID

        size = self.ANCHOR_SIZE
        font_size = self.LABEL_SIZE
        distance = anchor.distance
        if display_mode is DisplayMode.identify_anchor:
            if distance < self.VICINITY_DISTANCE:
                amount = (distance - self.HIGHLIGHT_DISTANCE) / \
                    (self.VICINITY_DISTANCE - self.HIGHLIGHT_DISTANCE)
                color = self._mix(color, self.HIGHLIGHT_ANCHOR_BRUSH, amount)

            if distance < self.HIGHLIGHT_DISTANCE:
                color = self.HIGHLIGHT_ANCHOR_BRUSH
                size = self.HIGHLIGHT_SIZE
                font_size = self.LABEL_HIGHLIGHT_SIZE

        marker_pos = anchor.get_position()
        text_pos = self.TEXT_OFFSET + marker_pos
        if id in self._anchor_contexts:
            self._anchor_contexts[id][0].set_data(
                pos=np.array([marker_pos]),
                face_color=color,
                size=size)

            text = self._anchor_contexts[id][1]
            text.pos = text_pos
            text.font_size = font_size
        else:
            marker = scene.visuals.Markers(
                pos=np.array([marker_pos]),
                face_color=color,
                size=size,
                parent=self._view.scene)
            text = scene.visuals.Text(
                text=str(id),
                font_size=font_size,
                pos=text_pos,
                parent=self._view.scene)
            self._anchor_contexts[id] = [marker, text]

    def _purge_anchors(self, keep):
        to_remove = []
        for id, context in self._anchor_contexts.items():
            if id not in keep:
                to_remove.append(id)
                for visual in context:
                    visual.parent = None
        for id in to_remove:
            self._anchor_contexts.pop(id)

    def _mix(self, col1, col2, mix):
        return col1 * mix + col2 * (1.0 - mix)


class DisplayMode(Enum):
    identify_anchor = 1
    estimated_position = 2


Range = namedtuple('Range', ['min', 'max'])


class AnchorStateMachine:
    GET_ACTIVE = 0
    GET_IDS = 1
    GET_DATA = 2
    STEPS = [
        GET_ACTIVE,
        GET_ACTIVE,
        GET_IDS,
        GET_ACTIVE,
        GET_ACTIVE,
        GET_DATA,
        GET_ACTIVE,
        GET_ACTIVE,
    ]

    def __init__(self, mem_sub, cb_active_id_list, cb_id_list, cb_data):
        self._current_step = 0
        self._waiting_for_response = False
        self._mem = self._get_mem(mem_sub)

        self._cb_active_id_list = cb_active_id_list
        self._cb_id_list = cb_id_list
        self._cb_data = cb_data

    def poll(self):
        if not self._waiting_for_response:
            self._next_step()
            self._waiting_for_response = self._request_step()

    def _next_step(self):
        self._current_step += 1
        if self._current_step >= len(AnchorStateMachine.STEPS):
            self._current_step = 0

    def _request_step(self):
        result = True

        action = AnchorStateMachine.STEPS[self._current_step]
        if action == AnchorStateMachine.GET_ACTIVE:
            self._mem.update_active_id_list(self._cb_active_id_list_updated)
        elif action == AnchorStateMachine.GET_IDS:
            self._mem.update_id_list(self._cb_id_list_updated)
        else:
            if self._mem.nr_of_anchors > 0:
                # Only request anchor data if we actually have anchors, otherwise the callback will never be called
                self._mem.update_data(self._cb_data_updated)
            else:
                result = False

        return result

    def _get_mem(self, mem_sub):
        mem = mem_sub.get_mems(MemoryElement.TYPE_LOCO2)
        if len(mem) > 0:
            return mem[0]
        return None

    def _cb_active_id_list_updated(self, mem_data):
        self._waiting_for_response = False
        if self._cb_active_id_list:
            self._cb_active_id_list(mem_data.active_anchor_ids)

    def _cb_id_list_updated(self, mem_data):
        self._waiting_for_response = False
        if self._cb_id_list:
            self._cb_id_list(mem_data.anchor_ids)

    def _cb_data_updated(self, mem_data):
        self._waiting_for_response = False
        if self._cb_data:
            self._cb_data(mem_data.anchor_data)


class LocoPositioningTab(TabToolbox, locopositioning_tab_class):
    """Tab for plotting Loco Positioning data"""

    # Update period of log data in ms
    UPDATE_PERIOD_LOG = 100

    # Update period of anchor position data
    UPDATE_PERIOD_ANCHOR_STATE = 1000

    UPDATE_PERIOD_LOCO_MODE = 1000

    LOCO_MODE_UNKNOWN = -1
    LOCO_MODE_AUTO = 0
    LOCO_MODE_TWR = 1
    LOCO_MODE_TDOA2 = 2
    LOCO_MODE_TDOA3 = 3

    PARAM_MDOE_GR = 'loco'
    PARAM_MODE_NM = 'mode'
    PARAM_MODE = PARAM_MDOE_GR + '.' + PARAM_MODE_NM

    # 界面刷新帧率（每秒更新次数，200ms 一次）
    FPS = 5

    _connected_signal = pyqtSignal(str)
    _disconnected_signal = pyqtSignal(str)
    _log_error_signal = pyqtSignal(object, str)
    _anchor_range_signal = pyqtSignal(int, object, object)
    _loco_sys_signal = pyqtSignal(int, object, object)
    _cb_param_to_detect_loco_deck_signal = pyqtSignal(object, object)

    _anchor_active_id_list_updated_signal = pyqtSignal(object)
    _anchor_data_updated_signal = pyqtSignal(object)

    def __init__(self, helper):
        super(LocoPositioningTab, self).__init__(helper, 'Wireless Positioning')
        self.setupUi(self)

        # 状态变量必须在 _clear_state() 之前初始化，因为 _clear_state 会访问它们
        self._anchors = {}
        self._indicator_state = {}
        self._last_pose = None
        self._is_connected = False
        self._clear_state()
        self._refs = []

        self._display_mode = DisplayMode.estimated_position

        # Always wrap callbacks from Aeroflie API though QT Signal/Slots
        # to avoid manipulating the UI when rendering it
        self._connected_signal.connect(self._connected)
        self._disconnected_signal.connect(self._disconnected)
        self._anchor_range_signal.connect(self._anchor_range_received)
        self._loco_sys_signal.connect(self._loco_sys_received)
        self._cb_param_to_detect_loco_deck_signal.connect(
            self._cb_param_to_detect_loco_deck)

        self._anchor_active_id_list_updated_signal.connect(
            self._active_id_list_updated)
        self._anchor_data_updated_signal.connect(
            self._anchor_data_updated)

        self._id_anchor_button.toggled.connect(
            lambda enabled:
            self._do_when_checked(
                enabled,
                self._set_display_mode,
                DisplayMode.identify_anchor)
        )

        self._estimated_postion_button.toggled.connect(
            lambda enabled:
            self._do_when_checked(
                enabled,
                self._set_display_mode,
                DisplayMode.estimated_position)
        )

        self._mode_auto.toggled.connect(
            lambda enabled: self._request_mode(enabled, self.LOCO_MODE_AUTO)
        )

        self._mode_twr.toggled.connect(
            lambda enabled: self._request_mode(enabled, self.LOCO_MODE_TWR)
        )

        self._mode_tdoa2.toggled.connect(
            lambda enabled: self._request_mode(enabled, self.LOCO_MODE_TDOA2)
        )

        self._mode_tdoa3.toggled.connect(
            lambda enabled: self._request_mode(enabled, self.LOCO_MODE_TDOA3)
        )

        self._enable_mode_buttons(False)

        self._switch_mode_to_twr_button.setEnabled(False)
        self._switch_mode_to_tdoa2_button.setEnabled(False)
        self._switch_mode_to_tdoa3_button.setEnabled(False)

        self._switch_mode_to_twr_button.clicked.connect(
            lambda enabled:
            self._send_anchor_mode(self.LOCO_MODE_TWR)
        )
        self._switch_mode_to_tdoa2_button.clicked.connect(
            lambda enabled:
            self._send_anchor_mode(self.LOCO_MODE_TDOA2)
        )
        self._switch_mode_to_tdoa3_button.clicked.connect(
            lambda enabled:
            self._send_anchor_mode(self.LOCO_MODE_TDOA3)
        )

        self._clear_anchors_button.clicked.connect(self._clear_anchors)

        self._configure_anchor_positions_button.clicked.connect(
            self._show_anchor_postion_dialog)

        # Connect the Aeroflie API callbacks to the signals
        self._helper.cf.connected.add_callback(
            self._connected_signal.emit)

        self._helper.cf.disconnected.add_callback(
            self._disconnected_signal.emit)

        self._set_up_plots()

        self.is_loco_deck_active = False

        self._graph_timer = QTimer()
        self._graph_timer.setInterval(int(1000 / self.FPS))
        self._graph_timer.timeout.connect(self._update_graphics)
        self._graph_timer.start()

        # 3D 渲染在独立慢速定时器中运行（1Hz），避免高频 OpenGL 调用导致 GPU 内存泄漏
        self._plot_timer = QTimer()
        self._plot_timer.setInterval(1000)
        self._plot_timer.timeout.connect(self._update_3d_plot)
        self._plot_timer.start()

        self._anchor_state_timer = QTimer()
        self._anchor_state_timer.setInterval(self.UPDATE_PERIOD_ANCHOR_STATE)
        self._anchor_state_timer.timeout.connect(self._poll_anchor_state)
        self._anchor_state_timer.start()
        self._anchor_state_machine = None

        self._update_position_label(self._helper.pose_logger.position)

        self._lps_state = self.LOCO_MODE_UNKNOWN
        self._update_lps_state(self.LOCO_MODE_UNKNOWN)

        self._anchor_position_dialog = AnchorPositionDialog(self, helper)
        self._configure_anchor_positions_button.setEnabled(False)

    def _do_when_checked(self, enabled, fkn, arg):
        if enabled:
            fkn(arg)

    def _set_up_plots(self):
        self._plot_3d = Plot3dLps()
        self._plot_layout.addWidget(self._plot_3d.native)

    def _set_display_mode(self, display_mode):
        self._display_mode = display_mode

    def _send_anchor_mode(self, mode):
        lopo = LoPoAnchor(self._helper.cf)

        mode_translation = {
            self.LOCO_MODE_TWR: lopo.MODE_TWR,
            self.LOCO_MODE_TDOA2: lopo.MODE_TDOA,
            self.LOCO_MODE_TDOA3: lopo.MODE_TDOA3,
        }

        # Set the mode from the last to the first anchor
        # In TDoA 2 mode this ensures that the master anchor is set last
        # Note: We only switch mode of anchor 0 - 7 since this is what is
        # supported in TWR and TDoA 2
        for j in range(5):
            for i in reversed(range(8)):
                lopo.set_mode(i, mode_translation[mode])

    def _clear_state(self):
        self._clear_anchors()
        self._update_ranging_status_indicators()
        self._id_anchor_button.setEnabled(True)
        # 重置状态缓存和姿态缓存，确保重连后样式和 3D 渲染被正确刷新
        self._indicator_state.clear()
        self._last_pose = None

    def _clear_anchors(self):
        """清除 anchor 数据并释放 vispy GPU 资源"""
        self._anchors = {}
        # _clear_state() 可能在 _set_up_plots() 之前被 __init__ 调用，
        # 此时 _plot_3d 尚未创建，需要检查属性存在性
        if hasattr(self, '_plot_3d'):
            for context in self._plot_3d._anchor_contexts.values():
                for visual in context:
                    visual.parent = None
            self._plot_3d._anchor_contexts.clear()

    def _connected(self, link_uri):
        """Callback when the Aeroflie has been connected"""
        self._is_connected = True
        self._request_param_to_detect_loco_deck()

    def _request_param_to_detect_loco_deck(self):
        """Send a parameter request to detect if the Loco deck is installed"""
        group = 'deck'

        def register(group, param):
            if self._is_in_param_toc(group, param):
                logger.debug("Requesting loco deck parameter")
                self._helper.cf.param.add_update_callback(group=group,
                                                          name=param,
                                                          cb=self._cb_param_to_detect_loco_deck_signal.emit)

        register(group, 'bcLoco')
        register(group, 'bcDWM1000')  # For backwards compatibility

    def _cb_param_to_detect_loco_deck(self, name, value):
        """Callback from the parameter sub system when the Loco deck detection
        parameter has been updated"""
        if value == '1':
            self._loco_deck_detected()

    def _loco_deck_detected(self):
        """Called when the loco deck has been detected. Enables the tab,
        starts logging and polling of the memory sub system as well as starts
        timers for updating graphics"""
        if not self.is_loco_deck_active:
            self.is_loco_deck_active = True
            try:
                self._register_logblock(
                    "LoPoTab0",
                    [
                        ("ranging", "distance0", "float"),
                        ("ranging", "distance1", "float"),
                        ("ranging", "distance2", "float"),
                        ("ranging", "distance3", "float"),
                    ],
                    self._anchor_range_signal.emit,
                    self._log_error_signal.emit)

                self._register_logblock(
                    "LoPoTab1",
                    [
                        ("ranging", "distance4", "float"),
                        ("ranging", "distance5", "float"),
                        ("ranging", "distance6", "float"),
                        ("ranging", "distance7", "float"),
                    ],
                    self._anchor_range_signal.emit,
                    self._log_error_signal.emit)

                self._register_logblock(
                    "LoPoSys",
                    [
                        ("loco", "mode", "uint8_t")
                    ],
                    self._loco_sys_signal.emit,
                    self._log_error_signal.emit,
                    update_period=self.UPDATE_PERIOD_LOCO_MODE)
            except KeyError as e:
                logger.warning(str(e))
            except AttributeError as e:
                logger.warning(str(e))

            self._start_polling_anchor_pos(self._helper.cf)
            self._enable_mode_buttons(True)
            self._configure_anchor_positions_button.setEnabled(True)

            self._helper.cf.param.add_update_callback(
                group=self.PARAM_MDOE_GR,
                name=self.PARAM_MODE_NM,
                cb=self._loco_mode_updated)

            if self.PARAM_MDOE_GR in self._helper.cf.param.values:
                if self.PARAM_MODE_NM in \
                        self._helper.cf.param.values[self.PARAM_MDOE_GR]:
                    self._loco_mode_updated(
                        self.PARAM_MODE,
                        self._helper.cf.param.values[self.PARAM_MDOE_GR][
                            self.PARAM_MODE_NM])

    def _remove_loco_param_callbacks(self):
        """移除在连接时注册的参数回调，防止回调累积导致内存泄漏"""
        try:
            self._helper.cf.param.remove_update_callback(
                group=self.PARAM_MDOE_GR, name=self.PARAM_MODE_NM,
                cb=self._loco_mode_updated)
        except (KeyError, AttributeError):
            pass
        try:
            self._helper.cf.param.remove_update_callback(
                group='deck', name='bcLoco',
                cb=self._cb_param_to_detect_loco_deck_signal.emit)
        except (KeyError, AttributeError):
            pass
        try:
            self._helper.cf.param.remove_update_callback(
                group='deck', name='bcDWM1000',
                cb=self._cb_param_to_detect_loco_deck_signal.emit)
        except (KeyError, AttributeError):
            pass

    def _disconnected(self, link_uri):
        """Callback for when the Aeroflie has been disconnected"""
        self._is_connected = False
        self._stop_polling_anchor_pos()
        self._remove_loco_param_callbacks()
        self._clear_state()
        self._update_graphics()
        self.is_loco_deck_active = False
        self._update_lps_state(self.LOCO_MODE_UNKNOWN)
        self._enable_mode_buttons(False)
        self._loco_mode_updated('', self.LOCO_MODE_UNKNOWN)
        self._configure_anchor_positions_button.setEnabled(False)
        self._anchor_position_dialog.close()

    def _register_logblock(self, logblock_name, variables, data_cb, error_cb,
                           update_period=UPDATE_PERIOD_LOG):
        """Register log data to listen for. One logblock can contain a limited
        number of parameters (6 for floats)."""
        lg = LogConfig(logblock_name, update_period)
        for variable in variables:
            if self._is_in_log_toc(variable):
                lg.add_variable('{}.{}'.format(variable[0], variable[1]),
                                variable[2])

        self._helper.cf.log.add_config(lg)
        lg.data_received_cb.add_callback(data_cb)
        lg.error_cb.add_callback(error_cb)
        lg.start()
        return lg

    def _is_in_log_toc(self, variable):
        toc = self._helper.cf.log.toc
        group = variable[0]
        param = variable[1]
        return group in toc.toc and param in toc.toc[group]

    def _is_in_param_toc(self, group, param):
        toc = self._helper.cf.param.toc
        return bool(group in toc.toc and param in toc.toc[group])

    def _anchor_range_received(self, timestamp, data, logconf):
        """Callback from the logging system when a range is updated."""
        for name, value in data.items():
            valid, anchor_number = self._parse_range_param_name(name)
            # Only set distance on anchors that we have seen through other
            # messages to avoid creating anchor 0-7 even if they do not exist
            # in a TDoA3 set up for instance
            if self._anchor_exists(anchor_number):
                if valid:
                    anchor = self._get_create_anchor(anchor_number)
                    anchor.distance = float(value)

    def _loco_sys_received(self, timestamp, data, logconf):
        """Callback from the logging system when the loco pos sys config
        is updated."""
        if self.PARAM_MODE in data:
            lps_state = data[self.PARAM_MODE]
            if lps_state == self.LOCO_MODE_TDOA2:
                if self._id_anchor_button.isEnabled():
                    if self._id_anchor_button.isChecked():
                        self._estimated_postion_button.setChecked(True)
                    self._id_anchor_button.setEnabled(False)
            else:
                if not self._id_anchor_button.isEnabled():
                    self._id_anchor_button.setEnabled(True)
            self._update_lps_state(lps_state)

    def _update_ranging_status_indicators(self):
        """更新 anchor 指示灯 QLabel 矩阵，使用样式缓存避免重复 setStyleSheet"""
        container = self._anchor_stats_container

        ids = sorted(self._anchors.keys())

        # 当 anchor ID 集合变化时，labels 位置会发生移位，必须清空缓存重新应用样式。
        # 否则新创建的 label widget 会因缓存命中而跳过 setStyleSheet，显示为无背景色。
        cached_ids = set(self._indicator_state.keys())
        if cached_ids != set(ids):
            self._indicator_state.clear()

        # Update existing labels or add new if needed
        count = 0
        for id in ids:
            col = count % 8
            row = int(count / 8)

            if count < container.count():
                label = container.itemAtPosition(row, col).widget()
            else:
                label = QLabel()
                label.setMinimumSize(30, 0)
                label.setProperty('frameShape', 'QFrame::Box')
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                container.addWidget(label, row, col)

            label.setText(str(id))

            new_style = STYLE_GREEN_BACKGROUND if self._anchors[id].is_active() else STYLE_RED_BACKGROUND
            old_style = self._indicator_state.get(id)
            if new_style != old_style:
                label.setStyleSheet(new_style)
                self._indicator_state[id] = new_style

            count += 1

        # Remove labels if there are too many
        for i in range(count, container.count()):
            col = i % 8
            row = int(i / 8)

            item = container.itemAtPosition(row, col)
            if item is not None:
                label = item.widget()
                if label is not None:
                    container.removeWidget(label)
                    label.deleteLater()

    def _logging_error(self, log_conf, msg):
        """Callback from the log layer when an error occurs"""
        QMessageBox.about(self, self.tr("LocoPositioningTab error"),
                          self.tr("Error when using log config"),
                          self.tr(" [{0}]: {1}").format(log_conf.name, msg))

    def _start_polling_anchor_pos(self, Aeroflie):
        """Set up a timer to poll anchor positions from the memory sub
        system"""
        if not self._anchor_state_machine:
            self._anchor_state_machine = AnchorStateMachine(
                Aeroflie.mem,
                self._anchor_active_id_list_updated_signal.emit,
                None,
                self._anchor_data_updated_signal.emit
            )
        self._anchor_state_timer.start()

    def _stop_polling_anchor_pos(self):
        self._anchor_state_timer.stop()
        self._anchor_state_machine = None

    def _poll_anchor_state(self):
        if self._anchor_state_machine:
            self._anchor_state_machine.poll()

    def _active_id_list_updated(self, anchor_list):
        """Callback from the anchor state machine when we get a list of active
        anchors"""
        for id, anchor_data in self._anchors.items():
            anchor_data.set_is_active(False)

        for id in anchor_list:
            anchor_data = self._get_create_anchor(id)
            anchor_data.set_is_active(True)

        self._update_ranging_status_indicators()

    def _anchor_data_updated(self, position_dict):
        """Callback from the anchor state machine when the anchor positions
         are updated"""
        prev_count = len(self._anchors)
        for id, anchor_data in position_dict.items():
            anchor = self._get_create_anchor(id)
            if anchor_data.is_valid:
                anchor.set_position(anchor_data.position)

        self._update_positions_in_config_dialog()
        # Anchor 数据首次加载或数量变化时，触发一次完整的 3D 场景更新。
        # Anchor 位置是固定的（物理基站不移动），无需定时器重复刷新。
        if len(self._anchors) != prev_count:
            self._plot_3d.update_data(
                self._anchors, self._helper.pose_logger.position, self._display_mode)

    def _parse_range_param_name(self, name):
        """Parse a parameter name for a ranging distance and return the number
           of the anchor. The name is on the format 'ranging.distance4' """
        valid = False
        anchor = 0
        if name.startswith('ranging.distance'):
            anchor = int(name[-1])
            valid = True
        return (valid, anchor)

    def _parse_position_param_name(self, name):
        """Parse a parameter name for a position and return the
           axis (0=x, 1=y, 2=z).
           The param name is on the format 'kalman.stateY' """
        valid = False
        axis = 0
        if name.startswith('kalman.state'):
            axis = {'X': 0, 'Y': 1, 'Z': 2}[name[-1]]
            valid = True
        return (valid, axis)

    def _get_create_anchor(self, anchor_number):
        if anchor_number not in self._anchors:
            self._anchors[anchor_number] = Anchor()
        return self._anchors[anchor_number]

    def _anchor_exists(self, anchor_number):
        return anchor_number in self._anchors

    def _update_graphics(self):
        """UI 刷新定时器回调（5Hz）。
        位置标签不依赖 loco deck，只要已连接就更新；
        QLabel 指示灯和 3D 渲染由独立定时器/回调驱动。"""
        if not self.is_visible():
            return
        # 位置数据来自 PoseLogger，不依赖 loco deck，
        # 只要已连接就应该更新（解决位置数据永不刷新的问题）
        if self._is_connected:
            self._update_position_label(self._helper.pose_logger.position)
        # QLabel 指示灯依赖 loco deck 固件数据，定时刷新确保 UI 同步
        if self.is_loco_deck_active and self._anchors:
            self._update_ranging_status_indicators()
        elif self.is_loco_deck_active:
            # loco deck 已激活但锚点尚未加载，跳过指示灯刷新
            pass

    def _update_3d_plot(self):
        """3D 渲染定时器回调（1Hz）。
        仅更新无人机位置标记（CF marker），不触碰 anchor visual。
        Anchor 位置是固定的（物理基站不移动），仅在 _anchor_data_updated 回调中更新。
        这样 GPU 上传从 16 次/秒（8 anchor × 2 visual）降为 0-1 次/秒（仅 CF marker）。"""
        if not self.is_visible() or not self._is_connected:
            return
        if not self.is_loco_deck_active:
            return

        current_pose = self._helper.pose_logger.position
        # 姿态变化不足 5cm 时跳过更新，传感器噪声不会触发 GPU 上传
        if self._last_pose is not None and current_pose and len(current_pose) == 3:
            dist = sum((self._last_pose[i] - current_pose[i]) ** 2 for i in range(3))
            if dist < 0.0005:  # 5cm² 阈值（约 2.2cm 线性距离）
                return

        # 仅更新 CF 位置标记，anchor 数据未变化无需重复上传 GPU
        self._plot_3d.update_cf_position(current_pose)
        self._last_pose = list(current_pose) if current_pose else None

    def _update_position_label(self, position):
        if len(position) == 3:
            coordinate = "({:0.2f}, {:0.2f}, {:0.2f})".format(
                position[0], position[1], position[2])
        else:
            coordinate = '(0.00, 0.00, 0.00)'

        self._status_position.setText(coordinate)

    def _update_lps_state(self, state):
        if state != self._lps_state:
            self._update_lps_state_indicator(self._state_twr,
                                             state == self.LOCO_MODE_TWR)
            self._update_lps_state_indicator(self._state_tdoa2,
                                             state == self.LOCO_MODE_TDOA2)
            self._update_lps_state_indicator(self._state_tdoa3,
                                             state == self.LOCO_MODE_TDOA3)
        self._lps_state = state

    def _update_lps_state_indicator(self, element, active):
        if active:
            element.setStyleSheet(STYLE_GREEN_BACKGROUND)
        else:
            element.setStyleSheet(STYLE_NO_BACKGROUND)

    def _enable_mode_buttons(self, enabled):
        self._mode_auto.setEnabled(enabled)
        self._mode_twr.setEnabled(enabled)
        self._mode_tdoa2.setEnabled(enabled)
        self._mode_tdoa3.setEnabled(enabled)

    def _request_mode(self, enabled, mode):
        if enabled:
            self._helper.cf.param.set_value(self.PARAM_MODE, str(mode))

            if mode == self.LOCO_MODE_TWR:
                self._switch_mode_to_twr_button.setEnabled(False)
                self._switch_mode_to_tdoa2_button.setEnabled(True)
                self._switch_mode_to_tdoa3_button.setEnabled(True)
            elif mode == self.LOCO_MODE_TDOA2:
                self._switch_mode_to_twr_button.setEnabled(True)
                self._switch_mode_to_tdoa2_button.setEnabled(False)
                self._switch_mode_to_tdoa3_button.setEnabled(True)
            elif mode == self.LOCO_MODE_TDOA3:
                self._switch_mode_to_twr_button.setEnabled(True)
                self._switch_mode_to_tdoa2_button.setEnabled(True)
                self._switch_mode_to_tdoa3_button.setEnabled(False)
            else:
                self._switch_mode_to_twr_button.setEnabled(False)
                self._switch_mode_to_tdoa2_button.setEnabled(False)
                self._switch_mode_to_tdoa3_button.setEnabled(False)

    def _loco_mode_updated(self, name, value):
        mode = int(value)
        if mode == self.LOCO_MODE_AUTO:
            if not self._mode_auto.isChecked():
                self._mode_auto.setChecked(True)
        elif mode == self.LOCO_MODE_TWR:
            if not self._mode_twr.isChecked():
                self._mode_twr.setChecked(True)
        elif mode == self.LOCO_MODE_TDOA2:
            if not self._mode_tdoa2.isChecked():
                self._mode_tdoa2.setChecked(True)
        elif mode == self.LOCO_MODE_TDOA3:
            if not self._mode_tdoa3.isChecked():
                self._mode_tdoa3.setChecked(True)
        else:
            self._mode_auto.setChecked(False)
            self._mode_twr.setChecked(False)
            self._mode_tdoa2.setChecked(False)
            self._mode_tdoa3.setChecked(False)

    def _show_anchor_postion_dialog(self):
        self._anchor_position_dialog.show()

    def _update_positions_in_config_dialog(self):
        positions = {}

        for id, anchor in self._anchors.items():
            if anchor.is_position_valid():
                positions[id] = (anchor.x, anchor.y, anchor.z)

        self._anchor_position_dialog.anchor_postions_updated(positions)

    def write_positions_to_anchors(self, anchor_positions):
        lopo = LoPoAnchor(self._helper.cf)

        for _ in range(3):
            for id, position in anchor_positions.items():
                lopo.set_position(id, position)
            time.sleep(0.2)
