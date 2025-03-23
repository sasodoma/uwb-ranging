# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library is handling Qorvo calibration parameters conversion & serialization
"""

import math
import re
import io
from .utils import *

__all__ = [
    "AoaTable",
    "AntConf",
    "ant_port",
    "ext_switch",
    "prf",
    "sfd",
    "psr",
    "data",
    "phr",
    "sts_n",
    "sts_len",
    "PhyFrame",
    "std_frame",
    "CalibrationParams",
    "cal_params",
    "build_cal_params",
    "dot",
]

# =============================================================================
# AoaTable
# =============================================================================


class AoaTable:
    """
    PDoA to AoA Look Up Table.
    This table contains 31 s4.11 encoded (pdoa,aoa) couples expressed in radian.

    feeding the table may be done using one of below:
        - "theory": the table is filled with theoretical 31 evenly spaced
                values from a computation depending on channel and
                antenna distance.
        - "identity": the table is filled with 31 evenly spaced values
                so as aoa == pdoa
        - a [ (pdoa1, aoa1), (pdoa2, aoa2), ... ] list in radians.
        - a bytes/bytearray stream of 62 s4.11 values
        - a csv file with proper column name and natural values in radians
                 pdoa      aoa
                <pdoa1>   <aoa1>
                <pdoa2>   <aoa2>
                ...
    """

    def __init__(self, value=None, name="unknown", channel=9, antenna_dist_mm=20.8):

        self.name = name
        self.value = []  # the table is stored internally as a list of couples
        if value == "theory":
            self.from_theory(channel, antenna_dist_mm)
        elif (value is None) or (value == "identity"):
            self.value = [
                (-3.14, 0),
                (-2.93, 0.21),
                (-2.72, 0.42),
                (-2.51, 0.63),
                (-2.3, 0.84),
                (-2.09, 1.05),
                (-1.88, 1.26),
                (-1.68, 1.47),
                (-1.47, -1.47),
                (-1.26, -1.26),
                (-1.05, -1.05),
                (-0.84, -0.84),
                (-0.63, -0.63),
                (-0.42, -0.42),
                (-0.21, -0.21),
                (0, 0),
                (0.21, 0.21),
                (0.42, 0.42),
                (0.63, 0.63),
                (0.84, 0.84),
                (1.05, 1.05),
                (1.26, 1.26),
                (1.47, 1.47),
                (1.68, -1.47),
                (1.88, -1.26),
                (2.09, -1.05),
                (2.3, -0.84),
                (2.51, -0.63),
                (2.72, -0.42),
                (2.93, -0.21),
                (3.14, 0),
            ]
        elif isinstance(value, list):
            self.from_list(value)
        elif isinstance(value, bytes) or isinstance(value, bytearray):
            self.from_bytes(value)
        elif isinstance(value, str):
            self.from_csv(value)
        else:
            raise ValueError(f' AoaTable building type "{type(value)}" not supported.')

    def __len__(self):
        return 124

    def _add(self, value):
        """
        Add a list of calibration value to the look-up table.
        Expected list Format: [ (<pdoa_1>, <aoa_1>), (<pdoa_2>, <aoa_2>),
                                                 ..., (<pdoa_n>, <aoa_n>),]
        """
        for pdoa, aoa in value:
            try:
                # Sanity check values and store real rounded-ones
                pdoa = FP(pdoa, is_signed=True, n_int=4, n_fract=11).as_float()
                aoa = FP(aoa, is_signed=True, n_int=4, n_fract=11).as_float()
                self.value.append((pdoa, aoa))
            except Exception as e:
                raise ValueError(f'({pdoa},{aoa}): "{str(e)}"')

    def from_list(self, value: list):
        if len(value) != 31:
            raise ValueError(f"Expected list length: 31. Got {len(value)}.")
        self.value = []
        self._add(value)
        return self

    def from_csv(self, path: str):
        is_file_ok = False
        v = []
        with open(path, "r") as f:
            for length in f:
                length = length.strip()
                if length == "":
                    continue
                if length[0] == "#":
                    continue
                l_i = re.split("\t|;| |:", length)
                pdoa, aoa = [x for x in l_i if x != ""]
                if [pdoa, aoa] == ["pdoa", "aoa"]:
                    is_file_ok = True
                    continue
                if not is_file_ok:
                    raise ValueError(
                        f'"{path}" seems not to contain AoaTable data. Expecting "{pdoa} | {aoa}" column headers.'
                    )
                v.append((float(pdoa), float(aoa)))
        self.from_list(v)
        return self

    def from_bytes(self, value: bytes):
        """
        Build the table from a provided little endian byte stream.
        This stream is expected to be serie of 32 s4.11 (pdoa, aoa) radian values.
        """
        self.value = []
        if len(value) % 4 != 0:
            raise ValueError(
                "Expecting a multiple of 4 bytes to build AoaTable from bytes stream."
            )
        for i in range(0, len(value), 4):
            pdoa = FP(value[i : i + 2], is_signed=True, n_int=4, n_fract=11).as_float()
            aoa = FP(
                value[i + 2 : i + 4], is_signed=True, n_int=4, n_fract=11
            ).as_float()
            self.value.append((pdoa, aoa))
        return self

    def from_theory(self, channel=9, antenna_dist_mm=20.8):
        v = []
        pi = 3.141592653589793
        C = 2.99702547e8
        f = 6.5e9 if channel == 5 else 7.9872e9 if channel == 9 else "NA"
        Ln = C / f / 2 / pi
        dP = 2 * pi / 30
        pdoa = -pi
        for i in range(31):
            phi = min(1.0, max(-1.0, pdoa * Ln / antenna_dist_mm * 1000))
            aoa = math.asin(phi)
            v.append((pdoa, aoa))
            pdoa = pdoa + dP
        self._add(v)
        return self

    def as_hex(self):
        return "NA"

    def as_list(self):
        return self.value

    def to_csv(self, path: str = None, sep=" "):
        output = io.StringIO()
        output.write(f"pdoa{sep}aoa\n")
        for pdoa, aoa in self.value:
            output.write(f"{pdoa}{sep}{aoa}\n")
        rtv = output.getvalue()
        output.close()
        if path is not None:
            with open(path, "w") as f:
                f.write(rtv)
        return rtv

    def to_bytes(self, length=-1, byteorder="little"):
        """
        Return as a byte stream.
        length == -1 : the default length is used. (124 bytes)
        """
        v = bytearray()
        for pdoa, aoa in self.value:
            v.extend(FP(pdoa, is_signed=True, n_int=4, n_fract=11).to_bytes())
            v.extend(FP(aoa, is_signed=True, n_int=4, n_fract=11).to_bytes())
        if byteorder == "big":
            v = v[::-1]
        if length != -1:
            if byteorder == "little":
                v = v + b"\x00" * (length - len(v))
            else:
                v = b"\x00" * (length - len(v)) + v
        return v

    def __str__(self):
        rts = f'\n      {"pdoa":<20} {"aoa":<20}\n'
        for pdoa, aoa in self.value:
            rts = rts + f"    {pdoa:<20} {aoa:<20}\n"
        return rts

    def __repr__(self):
        return f"AoaTable({self.value!r})"


# Pḧy Frame definition

# Ref.
# [1] Fira Consortium UWB Phy Technical Requirements Ver. 1.3.0 p.9


# PRF:
class prf(DynIntEnum):
    b = 0
    h = 1
    Unknown = 0xFFFF


# SFD Type:
class sfd(DynIntEnum):
    ieee4a = 0
    ieee4z4 = 1
    ieee4z8 = 2
    ieee4z16 = 3
    ieee4z32 = 4
    rfu = 5
    dw8 = 6
    dw16 = 7
    Unknown = 0xFFFF


# Preamble symbols (SYNC PSR)
class psr(DynIntEnum):
    n16 = 0
    n24 = 1
    n32 = 2
    n48 = 3
    n64 = 4
    n96 = 5
    n128 = 6
    n256 = 7
    n512 = 8
    n1024 = 9
    n2048 = 10
    n4096 = 11
    Unknown = 15


# Payload rate:
class data(DynIntEnum):
    r850k = 0
    r6m8 = 1
    nodata = 2
    rfu = 3
    r6m8_128 = 4
    r27m_256 = 5
    r6m8_187_k7 = 0xC
    r27m_256_k7 = 0xD
    r54m_256 = 0xE
    r108m_256 = 0xF
    Unknown = 0xFFFF


# BPRF PHR Rate:
class phr(DynIntEnum):
    std = 0  # As in standard
    as_data = 1  # same as data rate (6.8M)
    Unknown = 0xFFFF


# STS Segment number:
class sts_n(DynIntEnum):
    n0 = 0
    n1 = 1
    n2 = 2
    n3 = 3
    n4 = 4
    Unknown = 7


# STS Segment length:
class sts_len(DynIntEnum):
    n0 = 0
    n16 = 1
    n32 = 3
    n64 = 7
    n128 = 15
    n256 = 31
    n512 = 63
    n1024 = 127
    n2048 = 255
    Unknown = 0xFFFF


# Standard Fira Frame set:
class std_frame(DynIntEnum):
    bprf3 = 0x03
    bprf4 = 0x04
    hprf16 = 0x90
    hprf24 = 0x98
    Unknown = 0xFFFF


class PhyFrame:
    """
    Phy layer frame definition.
    This object is used to define & serialize a Physical layer frame definition
    as needed by the ref_frame<>.phy_cfg calibration parameters.

    Defining the frame may be done as below:
        - using & 3 bytes int value:
          ex: PhyFrame0x072144        using a 3 byte bytes/bytearray stream:
          ex: PhyFrame(b'\x44\x21\x07')
        - using a standard frame:
          PhyFrame(std_frame.bprf3)
          PhyFrame(std_frame.hprf16)
        - building by items:
          ex: PhyFrame().set( prf.b, sfd.ieee4z8, psr.n64, data.r6m8,
                              phr.std, sts_n.n1, sts_len.n64          )
    """

    def __init__(self, *args):
        self._prf = prf.h
        self._sfd = sfd.ieee4z8
        self._psr = psr.n32
        self._data = data.r27m_256
        self._phr = phr.std
        self._sts_n = sts_n.n1
        self._sts_len = sts_len.n32

        if len(args) != 0:
            self.set(*args)

    def set(self, *args):
        for value in args:
            if isinstance(value, prf):
                self._prf = value
            elif isinstance(value, sfd):
                self._sfd = value
            elif isinstance(value, psr):
                self._psr = value
            elif isinstance(value, data):
                self._data = value
            elif isinstance(value, phr):
                self._phr = value
            elif isinstance(value, sts_n):
                self._sts_n = value
            elif isinstance(value, sts_len):
                self._sts_len = value
            elif isinstance(value, std_frame):
                self.from_std(value)
            elif isinstance(value, bytes) or isinstance(value, bytearray):
                self.from_bytes(value)
            elif isinstance(value, int):
                self.from_int(value)
            else:
                raise ValueError(
                    f'"{value} ({type(value)})" not supported as a building PhyFrame value/type.'
                )

    def from_std(self, value: std_frame):
        if value == std_frame.bprf3:
            self.set(
                prf.b, sfd.ieee4z8, psr.n64, data.r6m8, phr.std, sts_n.n1, sts_len.n64
            )
        elif value == std_frame.bprf4:
            self.set(
                prf.b, sfd.ieee4z8, psr.n64, data.nodata, phr.std, sts_n.n1, sts_len.n64
            )
        elif value == std_frame.hprf16:
            self.set(
                prf.h,
                sfd.ieee4z8,
                psr.n32,
                data.r27m_256,
                phr.std,
                sts_n.n1,
                sts_len.n32,
            )
        elif value == std_frame.hprf24:
            self.set(
                prf.h, sfd.ieee4z8, psr.n64, data.nodata, phr.std, sts_n.n1, sts_len.n64
            )
        else:
            raise ValueError(
                f'PhyFrame std_frame value "{type(value.name)}" not implemented.'
            )
        return self

    def from_bytes(self, value: bytes):
        """
        Build the table from a provided little endian 3 bytes stream.
        """
        self.from_int(int.from_bytes(value, "little"))
        return self

    def from_int(self, value):
        """
        Update internals from  as a 3 byte int field coded as below:
        | sts_len     | sts_n       |  phr_rate | data_rate  | psr       | sfd       | prf |
        | #23-#16 (4) | #15-#13 (3) | #12       | #11-#8 (4) | #7-#4 (4) | #3-#1 (3) | #0  |
        """
        self._sts_len = sts_len((value >> 16) & (2**4 - 1))
        self._sts_n = sts_n((value >> 13) & (2**3 - 1))
        self._phr = phr((value >> 12) & (2**1 - 1))
        self._data = data((value >> 8) & (2**4 - 1))
        self._psr = psr((value >> 4) & (2**4 - 1))
        self._sfd = sfd((value >> 1) & (2**3 - 1))
        self._prf = prf((value >> 0) & (2**1 - 1))

    def as_int(self):
        """
        Return as a 3 byte int coded as below:
        | sts_len     | sts_n       |  phr_rate | data_rate  | psr       | sfd       | prf |
        | #23-#16 (4) | #15-#13 (3) | #12       | #11-#8 (4) | #7-#4 (4) | #3-#1 (3) | #0  |
        """
        return (
            (self._sts_len.value << 16)
            + (self._sts_n.value << 13)
            + (self._phr.value << 12)
            + (self._data << 8)
            + (self._psr << 4)
            + (self._sfd << 1)
            + self._prf
        )

    def as_hex(self):
        return hex(self.as_int())

    def to_bytes(self, length=3, byteorder="little"):
        return self.as_int().to_bytes(length, byteorder)

    def __str__(self):
        rts = f"PhyFrame(prf.{self._prf.name}, sfd.{self._sfd.name}, psr.{self._psr.name}, "
        rts += f"data.{self._data.name}, phr.{self._phr.name}, sts_n.{self._sts_n.name}, sts_len.{self._sts_len.name})"
        return rts

    def __repr__(self):
        return f"PhyFrame({self.as_hex()})"


# =============================================================================
# Antenna Configuration
# =============================================================================


class ext_switch(DynIntEnum):
    on = 1
    off = 0
    Unknown = 0xFF


class ant_port(DynIntEnum):
    n1 = 1
    n2 = 2
    n3 = 3
    n4 = 4
    Unknown = 0xFF


class AntConf:
    """
    Antenna Configuration
    This object is used to define & serialize a AntConf definition
    as needed by the ant<>.config calibration parameters.

    Defining the frame may be done as below:
        - using & 1 bytes int value:
          ex: AntConf0x01                   - building by items:
          ex: AntConf(ext_switch.on, ant_port.n1)
    """

    def __init__(self, *args):
        self._port = ant_port.n1
        self._switch = ext_switch.on
        if len(args) != 0:
            self.set(*args)

    def set(self, *args):
        for value in args:
            if isinstance(value, ext_switch):
                self._switch = value
            elif isinstance(value, ant_port):
                self._port = value
            elif isinstance(value, int):
                self.from_int(value)
            else:
                raise ValueError(
                    f'"{value} ({type(value)})" not supported as a building AntConf value/type.'
                )

    def from_bytes(self, value: bytes):
        """
        Build from a provided byte
        """
        self.from_int(int.from_bytes(value, "little"))
        return self

    def from_int(self, value):
        """
        Update internals from  1 byte int. field coded as below:
        | #7-#5  | #4    | #3-#0   |
        |  NA    | PA On | port N |
        """
        self._switch = ext_switch((value >> 4) & 1)
        self._port = ant_port(value & 7)

    def as_int(self):
        """
        Return as a 1 byte int. field coded as below:
        | #7-#5  | #4    | #3-#0   |
        |  NA    | PA On | port N |
        """
        return (self._switch.value << 4) + self._port

    def as_hex(self):
        return hex(self.as_int())

    def to_bytes(self, length=1, byteorder="little"):
        return self.as_int().to_bytes(length, byteorder)

    def __str__(self):
        return f"AntConf(ext_switch.{self._switch.name}, ant_port.{self._port.name})"

    def __repr__(self):
        return f"AntConf({self.as_hex()})"


# =============================================================================
# Calibration Data
# =============================================================================
class CalibrationParams(DynIntEnum):
    AntDelay = 0x00
    PgCount = 0x2
    PgDelay = 0x3
    PdoaOffs = 0x04
    PdoaLut = 0x05
    SpacingMmQ11 = 0x06
    DummyParam = 0x1A
    PllLockingCode = 0x07
    XtalTrim = 0x08
    TemperatureReference = 0x09
    VoltageReference = 0x0A
    TxPowerControl = 0x21
    PhyCfg = 0x22
    PayloadSize = 0x23
    TxPowerIndex = 0x28
    RestrictedChannels = 0x30
    WifiCoexMode = 0x31
    WifiCoexTimeGap = 0x32
    WifiCoexEnabled = 0x33
    AlternatePulseShape = 0x34
    CirNTaps = 0x35
    CirTapOffset = 0x36
    RxSegment = 0x39
    RfNoiseOffset = 0x3B
    MaxGatinGain = 0x3C
    PaGainOffset = 0x3E
    DebugPaEnabled = 0x3F
    WifiSwCfg = 0x50
    # 0x40-0x42: for addin_post_tx_tone
    MaxGrantDuration = 0x43
    DualRxAutoAcculPeriod = 0x44
    DualRxAutoRssiDiffRes = 0x45
    DualRxAutoErrorRateThres = 0x46
    MinInactiveDuration = 0x47
    DebugPllCfg = 0x51
    ByPassDelayOffset = 0x52
    # use for new antenna management
    Transceiver = 0x70
    Port = 0x71
    Lna = 0x72
    ExtSwCfg = 0x73
    AntPaths = 0x74
    Axis = 0x75
    PdoaLutId = 0x76
    TxAntPath = 0x77
    NbRxAnts = 0x78
    RxAnts = 0x79
    RxAntsArePairs = 0x81
    PostTxPatternRepetitions = 0x82
    PostTxPatternData = 0x83
    DebugTxPower = 0x84
    PostTxPowerIndex = 0x85
    PdoaOffset = 0x86
    IpStsSanityThresQ2 = 0x87
    Pa = 0x88


CalibrationParams.defs = [
    (CalibrationParams.Transceiver, 1, r"ant\d+\.transceiver$"),
    (CalibrationParams.Port, 1, r"ant\d+\.port$"),
    (CalibrationParams.Lna, 1, r"ant\d+\.lna$"),
    (CalibrationParams.Pa, 1, r"ant\d+\.pa$"),
    (CalibrationParams.ExtSwCfg, 1, r"ant\d+\.ext_sw_cfg$"),
    (CalibrationParams.AntPaths, 2, r"ant_pair\d+\.ant_paths$"),
    (CalibrationParams.Axis, 1, r"ant_pair\d+\.axis$"),
    (CalibrationParams.PdoaLutId, 1, r"ant_pair\d+\.ch\d+\.pdoa.lut_id$"),
    (CalibrationParams.PdoaOffset, 2, r"ant_pair\d+\.ch\d+\.pdoa.offset$"),
    (CalibrationParams.TxAntPath, 1, r"ant_set\d+\.tx_ant_path$"),
    (CalibrationParams.NbRxAnts, 1, r"ant_set\d+\.nb_rx_ants$"),
    (CalibrationParams.RxAnts, 3, r"ant_set\d+\.rx_ants$"),
    (CalibrationParams.RxAntsArePairs, 1, r"ant_set\d+\.rx_ants_are_pairs$"),
    (CalibrationParams.WifiSwCfg, 1, r"wifi_sw_cfg"),
    (CalibrationParams.WifiCoexEnabled, 1, r"ch\d+\.wifi_coex_enabled$"),
    (CalibrationParams.WifiCoexTimeGap, 1, r"wifi_coex_time_gap$"),
    (CalibrationParams.WifiCoexMode, 1, r"wifi_coex_mode$"),
    (CalibrationParams.MaxGrantDuration, 1, r"wifi_coex_max_grant_duration$"),
    (CalibrationParams.MinInactiveDuration, 1, r"wifi_coex_min_inactive_duration$"),
    (CalibrationParams.PhyCfg, 3, r"ref_frame\d+\.phy_cfg$"),
    (CalibrationParams.PayloadSize, 2, r"ref_frame\d+\.payload_size$"),
    (CalibrationParams.PostTxPatternRepetitions, 2, r"post_tx\.pattern_repetitions$"),
    (CalibrationParams.PostTxPatternData, 8, r"post_tx\.pattern_data$"),
    (CalibrationParams.RestrictedChannels, 2, r"restricted_channels$"),
    (CalibrationParams.AlternatePulseShape, 1, r"alternate_pulse_shape$"),
    (CalibrationParams.TxPowerControl, 1, r"ant_set\d+\.tx_power_control$"),
    (CalibrationParams.DebugTxPower, 4, r"debug\.tx_power$"),
    (CalibrationParams.DebugPaEnabled, 1, r"debug.pa_enabled$"),
    (CalibrationParams.DualRxAutoErrorRateThres, 1, r"dual_rx_auto\.error_rate_thres$"),
    (CalibrationParams.DualRxAutoRssiDiffRes, 1, r"dual_rx_auto\.rssi_diff_thres$"),
    (CalibrationParams.DualRxAutoAcculPeriod, 1, r"dual_rx_auto\.accum_period$"),
    (CalibrationParams.RxSegment, 1, r"debug.rx_segment"),
    (CalibrationParams.CirTapOffset, 2, r"rx_diag_config\.cir_fp_tap_offset$"),
    (CalibrationParams.CirNTaps, 2, r"rx_diag_config\.cir_n_taps$"),
    (CalibrationParams.AntDelay, 4, r"ant\d+\.ch\d+\.ant_delay$"),
    (
        CalibrationParams.ByPassDelayOffset,
        1,
        r"ant\d+\.ch\d+\.(tx|rx)_bypass_delay_offset$",
    ),
    (CalibrationParams.PaGainOffset, 1, r"ant\d+\.ch\d+\.pa_gain_offset$"),
    (
        CalibrationParams.TxPowerIndex,
        4,
        r"ant\d+\.ch\d+\.ref_frame\d+\.tx_power_index$",
    ),
    (
        CalibrationParams.PostTxPowerIndex,
        1,
        r"ant\d+\.ch\d+\.ref_frame\d+\.post_tx_power_index$",
    ),
    (
        CalibrationParams.MaxGatinGain,
        4,
        r"ant\d+\.ch\d+\.ref_frame\d+\.max_gating_gain$",
    ),
    (CalibrationParams.PgCount, 1, r"ant\d+\.ch\d+\.pg_count$"),
    (CalibrationParams.PgDelay, 1, r"ant\d+\.ch\d+\.pg_delay$"),
    (CalibrationParams.PdoaOffs, 2, r"ant_pair\d+\.ch\d+\.pdoa.axis[xyz].offset$"),
    (CalibrationParams.PdoaLut, 124, r"pdoa_lut\d+\.data$"),
    (CalibrationParams.PllLockingCode, 1, r"ch\d+\.pll_locking_code$"),
    (CalibrationParams.TemperatureReference, 1, r"temperature_reference$"),
    (CalibrationParams.XtalTrim, 1, r"xtal_trim$"),
    (CalibrationParams.VoltageReference, 4, r"voltage_reference$"),
    (CalibrationParams.RfNoiseOffset, 1, r"rf_noise_offset$"),
    (CalibrationParams.IpStsSanityThresQ2, 1, r"ip_sts_sanity_thres_q2"),
    (CalibrationParams.DebugPllCfg, 4, r"debug.pll_cfg$"),
]


def dot(*elements):
    """
    distribute and concatenate as strings elements of provided table/set/vector.
    Example:
        in:  dot('h_',[a,b,c],[1,2,3],[w,x,c]
        out: [h_a1w, h_a1x, ..., h_a2w, h_a2x, ..., h_b1w, ...]
    """
    o = [""]
    for x in elements:
        o_tmp = o
        o = []
        for i in o_tmp:
            if isinstance(x, str):
                o.append(i + x)
            else:
                for j in x:
                    o.append(i + str(j))
    return o


def build_cal_params(cal_def):
    """
    build a dictionary of cal params from below definition:
    (([key1, key2, ..., keyn] , value), ...)
    """
    o = {}
    for x, y in cal_def:
        for i in x:
            o[i] = y

    return o


ant_id = [0, 1, 2, 3]
pair_id = [0, 1, 2, 3]
set_id = [0, 1, 2, 3]
ref_frame_ids = [0, 1, 2, 3, 4, 5, 6, 7]
pdoa_lut_ids = [0, 1, 2, 3]

cal_params_in = (
    (dot("ant", ant_id, ".transceiver"), Uint8),
    (dot("ant", ant_id, ".port"), Uint8),
    (dot("ant", ant_id, ".lna"), Uint8),
    (dot("ant", ant_id, ".pa"), Uint8),
    (dot("ant", ant_id, ".ext_sw_cfg"), Uint8),
    (dot("ant_pair", pair_id, ".ant_paths"), Int16),
    (dot("ant_pair", pair_id, ".axis"), Uint8),
    (dot("ant_pair", pair_id, ".ch", [5, 9], ".pdoa.lut_id"), Int8),
    (dot("ant_pair", pair_id, ".ch", [5, 9], ".pdoa.offset"), S4_11),
    (dot("ant_set", set_id, ".tx_ant_path"), Int8),
    (dot("ant_set", set_id, ".nb_rx_ants"), Uint8),
    (dot("ant_set", set_id, ".rx_ants"), Int24),
    (dot("ant_set", set_id, ".rx_ants_are_pairs"), Int8),
    (["debug.pll_cfg"], Uint32),
    (["wifi_sw_cfg"], Uint8),
    (dot("ch", [5, 9], ".wifi_coex_enabled"), Uint8),
    (["wifi_coex_mode", "wifi_coex_time_gap"], Uint8),
    (["wifi_coex_max_grant_duration", "wifi_coex_min_inactive_duration"], Uint8),
    (dot("ref_frame", ref_frame_ids, ".phy_cfg"), PhyFrame),
    (dot("ref_frame", ref_frame_ids, ".payload_size"), Uint16),
    (["post_tx.pattern_repetitions"], Uint16),
    (["post_tx.pattern_data"], Uint64),
    (["restricted_channels"], Uint16),
    (["alternate_pulse_shape"], Uint8),
    (dot("ant_set", set_id, ".tx_power_control"), Uint8),
    (["debug.tx_power"], Uint32),
    (["debug.pa_enabled"], Uint8),
    (["ip_sts_sanity_thres_q2"], Uint8),
    (
        [
            "dual_rx_auto.accum_period",
            "dual_rx_auto.rssi_diff_thres",
            "dual_rx_auto.error_rate_thres",
        ],
        Uint8,
    ),
    (["debug.rx_segment"], Uint8),
    (["rx_diag_config.cir_n_taps", "rx_diag_config.cir_fp_tap_offset"], Uint16),
    (dot("ant", ant_id, ".ch", [5, 9], ".ant_delay"), Uint32),
    (dot("ant", ant_id, ".ch", [5, 9], ".tx_bypass_delay_offset"), Uint8),
    (dot("ant", ant_id, ".ch", [5, 9], ".rx_bypass_delay_offset"), Uint8),
    (
        dot(
            "ant", ant_id, ".ch", [5, 9], ".ref_frame", ref_frame_ids, ".tx_power_index"
        ),
        Uint32,
    ),
    (
        dot(
            "ant",
            ant_id,
            ".ch",
            [5, 9],
            ".ref_frame",
            ref_frame_ids,
            ".post_tx_power_index",
        ),
        Uint8,
    ),
    (
        dot(
            "ant",
            ant_id,
            ".ch",
            [5, 9],
            ".ref_frame",
            ref_frame_ids,
            ".max_gating_gain",
        ),
        Uint32,
    ),
    (dot("ant", ant_id, ".ch", [5, 9], ".pa_gain_offset"), Int8),
    (dot("ant", ant_id, ".ch", [5, 9], ".pg_count"), Int8),
    (dot("ant", ant_id, ".ch", [5, 9], ".pg_delay"), Int8),
    (dot("pdoa_lut", pdoa_lut_ids, ".data"), AoaTable),
    (dot("ch", [5, 9], ".pll_locking_code"), Uint8),
    (["xtal_trim", "temperature_reference"], Uint8),
    (["voltage_reference"], Uint32),
    (["rf_noise_offset"], Int8),
)

cal_params = build_cal_params(cal_params_in)
