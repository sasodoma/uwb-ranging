# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This file is configuring the package depending on the available variant.
A 'variant' is a FIRA vendor and the list of available addins.
"""
from glob import glob
import os
from .fira import *
from .qorvo import *
from .custom import *


uci_path = os.path.dirname(__file__)

# Get available addins
available_addins = []
for m_path in glob(f"{uci_path}/addin_*.py"):
    addin = os.path.basename(m_path)
    addin = addin.replace(".py", "")
    available_addins.append(addin)

# Get wanted addins
wanted_addins = os.getenv("UQT_ADDINS")
if wanted_addins is None:
    addins_to_load = available_addins
else:
    addins_to_load = wanted_addins.split(":")

# Load addins
loaded_addins = []
for addin in addins_to_load:
    try:
        exec(f"from .{addin} import *")
        loaded_addins.append(addin)
    except Exception as e:
        raise Exception(f'Unable to import ".{addin}" : {e!r}')
