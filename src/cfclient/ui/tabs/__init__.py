#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2011-2017 Waymark AB
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
Find all the available tabs so they can be loaded.

Dropping a new .py file into this directory will automatically list and load
it into the UI when it is started.
"""
import logging

logger = logging.getLogger(__name__)

_import_errors = []

# Each tab is imported in a try/except so one missing dependency
# (e.g. lpslib for locopositioning) doesn't break the entire UI.

try:
    from .ConsoleTab import ConsoleTab  # noqa: F401
except Exception as e:
    ConsoleTab = None
    _import_errors.append(('ConsoleTab', str(e)))
    logger.warning("Failed to load tab ConsoleTab: %s", e)

try:
    from .CrtpSharkToolbox import CrtpSharkToolbox  # noqa: F401
except Exception as e:
    CrtpSharkToolbox = None
    _import_errors.append(('CrtpSharkToolbox', str(e)))
    logger.warning("Failed to load tab CrtpSharkToolbox: %s", e)

# from .ExampleTab import ExampleTab

try:
    from .FlightTab import FlightTab  # noqa: F401
except Exception as e:
    FlightTab = None
    _import_errors.append(('FlightTab', str(e)))
    logger.warning("Failed to load tab FlightTab: %s", e)

# from .GpsTab import GpsTab

try:
    from .LEDRingTab import LEDRingTab  # noqa: F401
except Exception as e:
    LEDRingTab = None
    _import_errors.append(('LEDRingTab', str(e)))
    logger.warning("Failed to load tab LEDRingTab: %s", e)

try:
    from .ColorLEDTab import ColorLEDTab  # noqa: F401
except Exception as e:
    ColorLEDTab = None
    _import_errors.append(('ColorLEDTab', str(e)))
    logger.warning("Failed to load tab ColorLEDTab: %s", e)

try:
    from .LogBlockTab import LogBlockTab  # noqa: F401
except Exception as e:
    LogBlockTab = None
    _import_errors.append(('LogBlockTab', str(e)))
    logger.warning("Failed to load tab LogBlockTab: %s", e)

try:
    from .LogTab import LogTab  # noqa: F401
except Exception as e:
    LogTab = None
    _import_errors.append(('LogTab', str(e)))
    logger.warning("Failed to load tab LogTab: %s", e)

try:
    from .ParamTab import ParamTab  # noqa: F401
except Exception as e:
    ParamTab = None
    _import_errors.append(('ParamTab', str(e)))
    logger.warning("Failed to load tab ParamTab: %s", e)

try:
    from .PlotTab import PlotTab  # noqa: F401
except Exception as e:
    PlotTab = None
    _import_errors.append(('PlotTab', str(e)))
    logger.warning("Failed to load tab PlotTab: %s", e)

try:
    from .locopositioning_tab import LocoPositioningTab  # noqa: F401
except Exception as e:
    LocoPositioningTab = None
    _import_errors.append(('LocoPositioningTab', str(e)))
    logger.warning("Failed to load tab WirelessPositioningTab: %s", e)

try:
    from .LogClientTab import LogClientTab  # noqa: F401
except Exception as e:
    LogClientTab = None
    _import_errors.append(('LogClientTab', str(e)))
    logger.warning("Failed to load tab LogClientTab: %s", e)

try:
    from .lighthouse_tab import LighthouseTab  # noqa: F401
except Exception as e:
    LighthouseTab = None
    _import_errors.append(('LighthouseTab', str(e)))
    logger.warning("Failed to load tab OpticsTab: %s", e)

try:
    from .TuningTab import TuningTab  # noqa: F401
except Exception as e:
    TuningTab = None
    _import_errors.append(('TuningTab', str(e)))
    logger.warning("Failed to load tab TuningTab: %s", e)

__author__ = 'Waymark AB'
__all__ = []

available = [t for t in [
    ConsoleTab,
    # ExampleTab,
    FlightTab,
    # GpsTab,
    LighthouseTab,
    LocoPositioningTab,
    LEDRingTab,
    ColorLEDTab,
    LogBlockTab,
    LogTab,
    ParamTab,
    PlotTab,
    TuningTab,
    CrtpSharkToolbox,
    LogClientTab,
] if t is not None]

if _import_errors:
    logger.warning("Some tabs failed to load: %s", _import_errors)
