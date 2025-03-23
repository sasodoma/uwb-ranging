#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
    This library is handling several helpers for uqt scripts
"""

__all__ = [
    "uqt_errno",
    "uqt_errmsg",
    "wait_for",
    "get_test_profile",
    "test_profile_keys",
]


import time
import sys
from uci import Status
from uci.utils import FP
from uci.core import UciComStatus
from uci import App

try:
    from uci import SeErrorCodes
except ImportError:

    class SeErrorCodes:
        def __init__(self, value):
            self.name = f"SeErrorCodes({value})"


def uqt_errno(status_code):
    """
    Translate internal UCI Error to uqt errno
    """
    if isinstance(status_code, Status):
        # General UCI Error Codes (200-249)
        # errno: 200-254
        if status_code == Status.Ok:
            errno = 0
        elif 1 <= status_code < 254:
            errno = 200 + status_code
        else:
            raise ValueError(
                f"uqt_errno: Mapping issue. Status.{status_code.name}({status_code}) to uge to map in 200-254"
            )
    elif isinstance(status_code, SeErrorCodes):
        # UCI SE Error codes 160-199
        if status_code == SeErrorCodes.SE_ERROR_OK:
            errno = 0
        elif 0x1000 <= status_code <= 0x1019:
            errno = 160 + (status_code & 0x00FF)
        elif 0x1100 <= status_code <= 0x1119:
            errno = 190 + (status_code & 0x00FF)
        else:
            raise ValueError(
                f"uqt_errno: Mapping issue. SeErrorCodes.{status_code.name}({status_code}) to uge to map in 160-199"
            )
    elif isinstance(status_code, UciComStatus):
        # UCI Transport Error codes
        # errno: 150-159
        if status_code == UciComStatus.Ok:
            errno = 0
        elif 1 <= status_code <= 9:
            errno = 150 + status_code
        else:
            raise ValueError(
                f"uqt_errno: Mapping issue. UciCommStatus.{status_code.name}({status_code}) to uge to map in 150-159"
            )
    else:
        # Default linux standard codes
        errno = int(status_code)
        if errno > 149:
            raise ValueError(
                f"uqt_errno:Mapping issue. linux errno code {errno} to uge to map in 0-149"
            )
    return errno


def uqt_errmsg(errno: int):
    """
    Translate uqt errno to a readable format
    """
    if errno < 150:
        msg = {
            0: "Ok",
            1: "Error",
            2: "Syntax Error",
            126: "Command cannot execute",
            127: "command not found",
        }
        errmsg = msg.get(errno, f"Linux Error {hex(errno)}.")
    elif 150 <= errno < 160:
        msg = {
            0: "Communication error",
            1: "Unknown port",
            2: "Unknown protocol",
            3: "Communication timeout",
        }
        e = UciComStatus(errno - 150)
        errmsg = f"UciComStatus.{e.name} ({hex(e)})"
    elif 160 <= errno < 190:
        e = SeErrorCodes((errno - 160) + 0x1000)
        errmsg = f"SeErrorCodes.{e.name} ({hex(e)})"
    elif 190 <= errno < 200:
        e = SeErrorCodes((errno - 190) + 0x1100)
        errmsg = f"SeErrorCodes.{e.name} ({hex(e)})"
    else:
        # 200 <= errno
        e = Status(errno - 200)
        errmsg = f"Status.{e.name} ({hex(e)})"
    return errmsg


def wait_for(condition, timeout=1, interval=0.1):
    start = time.time()
    while not condition() and (time.time() - start < timeout):
        time.sleep(interval)
    return condition()


test_profile_keys = [
    "app_config_preamble_code_index",
    "app_config_preamble_duration",
    "app_config_sfd_id",
    "app_config_nb_sts_segments",
    "app_config_psdu_data_rate",
    "app_config_rf_frame_config",
    "misc_test_psdu",
    "test_config_randomized_psdu",
]


def get_test_profile(file_name: str) -> ({}, {}, {}):
    app_config = {}
    test_config = {}
    misc_test = {}
    line_nr = 0
    try:
        for line in open(file_name):
            line_nr = line_nr + 1
            line = line.strip()
            if line == "":
                continue
            if line.startswith("#"):
                continue
            k, v = line.split("=")
            k = k.strip()
            v = v.strip()
            vo = v
            if k in ("file_format_version", "file_description", "test_type"):
                continue
            if not (k in test_profile_keys):
                raise ValueError(f"'{k}' unknown parameter")
            try:
                # If we are dealing with an int,
                # verify it, but .. still output it as a string
                if len(vo) <= 0:
                    vo = f"0{vo}"
            except (ValueError, SyntaxError):
                # We are dealing with a bytestream
                # let's Verify it, but .. still output it as a string
                try:
                    vo = vo.replace(":", ".")
                except ValueError as e:
                    sys.exit(f"Bad value format at line {line_nr}: {vo} ({e})")
            if k.startswith("app_config_"):
                app_config[k.replace("app_config_", "")] = vo
            elif k.startswith("test_config_"):
                test_config[k.replace("test_config_", "")] = vo
            elif k.startswith("misc_test_"):
                misc_test[k.replace("misc_test_", "")] = vo
            else:
                raise ValueError(f"'{k}' unknown parameter")
        return (app_config, test_config, misc_test)
    except ValueError as e:
        sys.exit(f"Bad file format at line {line_nr}: {e}")


def compute_dl_tdoa_anchor_location_value(
    presence: int, coord_type: int, coord_x: float, coord_y: float, coord_z: float
):
    """Compute application configuration parameter DlTdoaAnchorLocation and return its value"""
    coord_x = float(coord_x)
    coord_y = float(coord_y)
    coord_z = float(coord_z)

    if presence == 0:  # DT-Anchor location not present
        return 0
    elif presence == 1:  # DT-Anchor location present
        byte_0 = presence + (coord_type << 1)
        App.defs = [param for param in App.defs if param[0] != App.DlTdoaAnchorLocation]
        if coord_type == 0:  # WGS-84 coordinates system
            if (
                coord_x > 90.0
                or coord_x < -90.0
                or coord_y > 180.0
                or coord_y < -180.0
                or coord_z > 255
                or coord_z < -256
            ):
                raise ValueError("DT-Anchor coordinates out of specified range")

            App.defs.append((App.DlTdoaAnchorLocation, 13))
            by_lat = FP(
                coord_x, is_signed=True, n_int=8, n_fract=24, ignore_nbits_error=True
            ).to_bytes(length=-1, byteorder="little")
            by_long = FP(
                coord_y, is_signed=True, n_int=8, n_fract=24, ignore_nbits_error=True
            ).to_bytes(length=-1, byteorder="little")
            # Cannot use FP as value is not aligned. Change to fixed point manually.
            alt = round(coord_z * (1 << 21))
            # Format to bit array string.
            b_alt = format(((1 << 32) - 1) & alt, "032b")
            # Swap bytes.
            b_alt = f"{b_alt[24:32]}{b_alt[16:24]}{b_alt[8:16]}{b_alt[2:8]}"
            # Build binary stream in UCI order.
            # Streams are initially a bit longer to add leading zeros.
            b_type = f"{byte_0:08b}"
            b_lat = format(int(by_lat.hex(), 16), "040b")
            b_long = format(int(by_long.hex(), 16), "040b")
            b_all = f"{b_type}{b_lat[0:33]}{b_long[0:33]}{b_alt}"

            # Change representation to int and swap order (it's swapped on sending again).
            by_all = int(b_all, 2).to_bytes(13, sys.byteorder)
            return int.from_bytes(by_all, "big")

        elif coord_type == 1:  # Relative coordinates system
            if (
                coord_x > (2**27) - 1
                or coord_x < -(2**27)
                or coord_y > (2**27) - 1
                or coord_y < -(2**27)
                or coord_z > (2**23) - 1
                or coord_z < -(2**23)
            ):
                raise ValueError("DT-Anchor coordinates out of specified range")

            App.defs.append((App.DlTdoaAnchorLocation, 11))
            by_x = FP(
                coord_x, is_signed=True, n_int=27, n_fract=0, ignore_nbits_error=True
            ).to_bytes(length=-1, byteorder="little")
            by_y = FP(
                coord_y, is_signed=True, n_int=27, n_fract=0, ignore_nbits_error=True
            ).to_bytes(length=-1, byteorder="little")
            by_z = FP(
                coord_z, is_signed=True, n_int=23, n_fract=0, ignore_nbits_error=True
            ).to_bytes(length=-1, byteorder="little")

            # Build binary stream in UCI order.
            # Streams are initially a bit longer to add leading zeros.
            b_type = f"{byte_0:08b}"
            b_x = format(int(by_x.hex(), 16), "032b")
            b_y = format(int(by_y.hex(), 16), "032b")
            b_z = format(int(by_z.hex(), 16), "024b")
            # Bits 24:28 in little endian are most significant bits of 32 bit value
            # so we cut them off to fit into 28 bit value.
            b_all = f"{b_type}{b_x[0:24]}{b_x[28:32]}{b_y[0:24]}{b_y[28:32]}{b_z[0:24]}"

            # Change representation to int and swap order (it's swapped on sending again).
            by_all = int(b_all, 2).to_bytes(11, sys.byteorder)
            return int.from_bytes(by_all, "big")

        else:
            raise ValueError(f"coord_type=={coord_type}, but should be 0 or 1")
    else:
        raise ValueError(f"presence=={presence}, but should be 0 or 1")


def str2bytes(v: str) -> bytes:
    """convert an input string defining a stream of bytes to bytes
    Two formats are handled:
    - point or colon separated list:
        '12.34.56'
        '"12.34.56"*29'
    - Python List
        '[0x12, 0x34, 0x56]'
        '[12, 34]*25'
        '[ i for i in range(3)]*2'
    """
    try:
        if "[" in v:
            # Python List
            byte_stream = bytes(eval(v))
        else:
            # byte defined as an '.' or ':' separated hex string
            if '"' in v or "'" in v:
                # There are quotes inside the string, it is expexted to have
                # a Python string definition (for instance "example"*2)
                v_str = eval(v)
            else:
                v_str = v
            byte_stream = bytes.fromhex(v_str.replace(":", "").replace(".", ""))
        return byte_stream
    except TypeError:
        raise ValueError(f"'{v}': Bad byte stream definition.")
