# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

from dataclasses import dataclass
from statistics import mean, stdev

from uci import AoaType
from uci import Status


@dataclass
class RangingStats:
    _stats: dict

    def __init__(self, range_ntf: list, diagnostic_ntf: list):
        self._stats = dict()
        self._diag_present = False
        diagnostic_ntf_idx = 0
        for range in range_ntf:
            diag = diagnostic_ntf[diagnostic_ntf_idx] if diagnostic_ntf else None
            if diag:
                aoas = diag.get_aoa_report()
                if aoas:
                    self._diag_present = True
                # normally, the sequence id of the range ntf and the diag ntf correspond
                meas_idx = 0
            diagnostic_ntf_idx += 1
            for measurements in range.meas:
                # There should be the same number of AoAs in the diagnostics as the devices on the ranges
                if self._diag_present:
                    aoa = aoas[meas_idx] if aoas else 0
                    meas_idx += 1
                mac = measurements.mac_add
                if mac not in self._stats.keys():
                    self._stats[mac] = {
                        "total_ranges": 0,
                        "total_ranges_ok": 0,
                        "distances": [],
                        "AoA_az": [],
                        "AoA_el": [],
                        "AoA_x": [],
                        "AoA_y": [],
                        "AoA_z": [],
                        "Pdoa_x": [],
                        "Pdoa_y": [],
                        "Pdoa_z": [],
                    }
                self._stats[mac]["total_ranges"] += 1
                if measurements.status == Status.Ok:
                    self._stats[mac]["total_ranges_ok"] += 1
                    try:
                        self._stats[mac]["distances"].append(measurements.distance)
                    except AttributeError:
                        self._stats[mac]["distances"].append(0)
                    self._stats[mac]["AoA_az"].append(measurements.aoa_tetha)
                    self._stats[mac]["AoA_el"].append(measurements.aoa_phi)
                    if self._diag_present:
                        for axis in aoa:
                            if axis["aoa_type"] == AoaType.XAxis:
                                try:
                                    self._stats[mac]["AoA_x"].append(axis["aoa"])
                                    self._stats[mac]["Pdoa_x"].append(axis["pdoa"])
                                except AttributeError:
                                    print(f"ERROR: {axis}")
                            elif axis["aoa_type"] == AoaType.YAxis:
                                self._stats[mac]["AoA_y"].append(axis["aoa"])
                                self._stats[mac]["Pdoa_y"].append(axis["pdoa"])
                            elif axis["aoa_type"] == AoaType.ZAxis:
                                self._stats[mac]["AoA_z"].append(axis["aoa"])
                                self._stats[mac]["Pdoa_z"].append(axis["pdoa"])

        for mac in self._stats:
            if self._stats[mac]["total_ranges_ok"] >= 2:
                self._stats[mac]["avg_distance"] = mean(self._stats[mac]["distances"])
                self._stats[mac]["stddev_distance"] = stdev(
                    self._stats[mac]["distances"]
                )
                self._stats[mac]["avg_AoA_azimuth"] = mean(self._stats[mac]["AoA_az"])
                self._stats[mac]["stddev_AoA_azimuth"] = stdev(
                    self._stats[mac]["AoA_az"]
                )
                self._stats[mac]["avg_AoA_elevation"] = mean(self._stats[mac]["AoA_el"])
                self._stats[mac]["stddev_AoA_elevation"] = stdev(
                    self._stats[mac]["AoA_el"]
                )
                self._stats[mac]["avg_AoA_x"] = 0
                self._stats[mac]["stddev_AoA_x"] = 0
                self._stats[mac]["avg_Pdoa_x"] = 0
                self._stats[mac]["stddev_Pdoa_x"] = 0
                self._stats[mac]["avg_AoA_y"] = 0
                self._stats[mac]["stddev_AoA_y"] = 0
                self._stats[mac]["avg_Pdoa_y"] = 0
                self._stats[mac]["stddev_Pdoa_y"] = 0
                self._stats[mac]["avg_AoA_z"] = 0
                self._stats[mac]["stddev_AoA_z"] = 0
                self._stats[mac]["avg_Pdoa_z"] = 0
                self._stats[mac]["stddev_Pdoa_z"] = 0
                if self._diag_present:
                    if (
                        "AoA_x" in self._stats[mac].keys()
                        and len(self._stats[mac]["AoA_x"]) > 1
                    ):
                        self._stats[mac]["avg_AoA_x"] = mean(self._stats[mac]["AoA_x"])
                        self._stats[mac]["stddev_AoA_x"] = stdev(
                            self._stats[mac]["AoA_x"]
                        )
                        self._stats[mac]["avg_Pdoa_x"] = mean(
                            self._stats[mac]["Pdoa_x"]
                        )
                        self._stats[mac]["stddev_Pdoa_x"] = stdev(
                            self._stats[mac]["Pdoa_x"]
                        )
                    if (
                        "AoA_y" in self._stats[mac].keys()
                        and len(self._stats[mac]["AoA_y"]) > 1
                    ):
                        self._stats[mac]["avg_AoA_y"] = mean(self._stats[mac]["AoA_y"])
                        self._stats[mac]["stddev_AoA_y"] = stdev(
                            self._stats[mac]["AoA_y"]
                        )
                        self._stats[mac]["avg_Pdoa_y"] = mean(
                            self._stats[mac]["Pdoa_y"]
                        )
                        self._stats[mac]["stddev_Pdoa_y"] = stdev(
                            self._stats[mac]["Pdoa_y"]
                        )
                    if (
                        "AoA_z" in self._stats[mac].keys()
                        and len(self._stats[mac]["AoA_z"]) > 1
                    ):
                        self._stats[mac]["avg_AoA_z"] = mean(self._stats[mac]["AoA_z"])
                        self._stats[mac]["stddev_AoA_z"] = stdev(
                            self._stats[mac]["AoA_z"]
                        )
                        self._stats[mac]["avg_Pdoa_z"] = mean(
                            self._stats[mac]["Pdoa_z"]
                        )
                        self._stats[mac]["stddev_Pdoa_z"] = stdev(
                            self._stats[mac]["Pdoa_z"]
                        )
                else:
                    self._stats[mac]["avg_AoA_x"] = 0
                    self._stats[mac]["stddev_AoA_x"] = 0
                    self._stats[mac]["avg_Pdoa_x"] = 0
                    self._stats[mac]["stddev_Pdoa_x"] = 0
                    self._stats[mac]["avg_AoA_y"] = 0
                    self._stats[mac]["stddev_AoA_y"] = 0
                    self._stats[mac]["avg_Pdoa_y"] = 0
                    self._stats[mac]["stddev_Pdoa_y"] = 0
                    self._stats[mac]["avg_AoA_z"] = 0
                    self._stats[mac]["stddev_AoA_z"] = 0
                    self._stats[mac]["avg_Pdoa_z"] = 0
                    self._stats[mac]["stddev_Pdoa_z"] = 0
            else:
                self._stats[mac]["avg_distance"] = 0
                self._stats[mac]["stddev_distance"] = 0
                self._stats[mac]["avg_AoA_azimuth"] = 0
                self._stats[mac]["stddev_AoA_azimuth"] = 0
                self._stats[mac]["avg_AoA_elevation"] = 0
                self._stats[mac]["stddev_AoA_elevation"] = 0
                self._stats[mac]["avg_AoA_x"] = 0
                self._stats[mac]["stddev_AoA_x"] = 0
                self._stats[mac]["avg_Pdoa_x"] = 0
                self._stats[mac]["stddev_Pdoa_x"] = 0
                self._stats[mac]["avg_AoA_y"] = 0
                self._stats[mac]["stddev_AoA_y"] = 0
                self._stats[mac]["avg_Pdoa_y"] = 0
                self._stats[mac]["stddev_Pdoa_y"] = 0
                self._stats[mac]["avg_AoA_z"] = 0
                self._stats[mac]["stddev_AoA_z"] = 0
                self._stats[mac]["avg_Pdoa_z"] = 0
                self._stats[mac]["stddev_Pdoa_z"] = 0

    def __str__(self) -> str:
        ret = ""
        for mac in self._stats:
            ret += f"""Device: {mac}
                    {self._stats[mac]['total_ranges_ok']} Successful/ {self._stats[mac]['total_ranges']} Total
                    AVG Ranging: {self._stats[mac]['avg_distance']:.2f}
                    STDEV Ranging: {self._stats[mac]['stddev_distance']:.2f}
                    AVG AoA Azimuth: {self._stats[mac]['avg_AoA_azimuth']:.3f}
                    STDEV AoA Azimuth: {self._stats[mac]['stddev_AoA_azimuth']:.3f}
                    AVG AoA Elevation: {self._stats[mac]['avg_AoA_elevation']:.3f}
                    STDEV AoA Elevation: {self._stats[mac]['stddev_AoA_elevation']:.3f}"""
            if self._diag_present:
                ret += f"""
                    Diagnostics:
                        X Axis:
                        AVG Raw AoA: {self._stats[mac]["avg_AoA_x"]:.3f}
                        STDEV Raw AoA: {self._stats[mac]["stddev_AoA_x"]:.3f}
                        AVG Raw Pdoa: {self._stats[mac]["avg_Pdoa_x"]:.3f}
                        STDEV Raw Pdoa: {self._stats[mac]["stddev_Pdoa_x"]:.3f}
                        Y Axis:
                        AVG Raw AoA: {self._stats[mac]["avg_AoA_y"]:.3f}
                        STDEV Raw AoA: {self._stats[mac]["stddev_AoA_y"]:.3f}
                        AVG Raw Pdoa: {self._stats[mac]["avg_Pdoa_y"]:.3f}
                        STDEV Raw Pdoa: {self._stats[mac]["stddev_Pdoa_y"]:.3f}
                        Z Axis:
                        AVG Raw AoA: {self._stats[mac]["avg_AoA_z"]:.3f}
                        STDEV Raw AoA: {self._stats[mac]["stddev_AoA_z"]:.3f}
                        AVG Raw Pdoa: {self._stats[mac]["avg_Pdoa_z"]:.3f}
                        STDEV Raw Pdoa: {self._stats[mac]["stddev_Pdoa_z"]:.3f}
                        """
        return ret
