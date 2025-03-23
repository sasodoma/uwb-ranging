# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library is handling custom parameters for QM33SDK customization option.
"""

from . import fira
from .fira import *
from .utils import DynIntEnum

__all__ = ["config_params"]


class Config(DynIntEnum):
    pass


fira.config_params.pop(fira.Config.LowPowerMode)
fira.config_params.pop(fira.Config.Traces)
fira.config_params.pop(fira.Config.PmMinInactivityS4)
