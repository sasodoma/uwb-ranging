#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

import json

from uci import AoaTable, Status


def load_calibration(client, calibration_filename):
    """
    Load calibration to device from given JSON file.
    """
    calib_file = open(calibration_filename, "r")
    calib = json.load(calib_file)

    print("\nSetting provided calibration...")

    try:
        for key, value in calib["calibrations"].items():
            if (
                key == "pdoa_lut0.data"
                or key == "pdoa_lut1.data"
                or key == "pdoa_lut2.data"
                or key == "pdoa_lut3.data"
            ):
                lut = calib["LUT"][value]
                to_set = AoaTable(lut)
                print(f"setting {key} to value {value}", end="")
            else:
                to_set = int(value, 0)
                print(f"setting {key} to value {to_set}", end="")
            ret, _ = client.test_mode_calibrations_set([(key, to_set)])
            print(f"...{ret.name}")
            if ret != Status.Ok:
                print("\n*******************ERROR*********************")
                print(f"Error Setting key '{key}' to value '{value}'")
                print("Device refused to set calibration with reason:" f" {ret.name}")
                print("*********************************************")
                break
    except KeyError as e:
        print("\n*******************ERROR*********************")
        print(f"Expected key {e} not found in JSON file")
        print("*********************************************")
    except Exception as e:
        print("\n*******************ERROR*********************")
        print(f"Error Setting key '{key}' to value '{value}'")
        print(f"Exception: {e}")
        print("*********************************************")

    print("Calibration done.")
