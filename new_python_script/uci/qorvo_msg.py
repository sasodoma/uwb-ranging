# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library is handling Qorvo UCI data format and conversion
"""

# It is safe to import the full library

import enum
import logging
from dataclasses import asdict, dataclass
from .utils import *
from .fira import *

__all__ = [
    "OidQorvo",
    "OidCalibration",
    "PllLockTestStatus",
    "PllLockTestStatusMask",
    "PllLockTestOutput",
    "TofTestStatus",
    "SetOffsetCode",
    "TofTestOutput",
    "RTCTestResult",
    "CwTestOutput",
    "RangingTwrData",
    "RangingData",
    "DiagAction",
    "DiagField",
    "DiagMessage",
    "FrameStatusField",
    "SegmentMetricsDiagField",
    "AoaItem",
    "AoaDiagField",
    "CFODiagField",
    "UnknownDiagField",
    "CirDiagField",
    "RangingDiagReport",
    "RangingDiagData",
    "TestDebugData",
    "RtcTestOutput",
    "SegmentType",
    "RangingMeas",
]

logger = logging.getLogger()
OFFSET_CODE = 0

# =============================================================================
# Additional Qorvo Enum
# =============================================================================


class Gid_extension(DynIntEnum):
    Calibration = 0x0E
    Qorvo = 0x0B


Gid.extend(Gid_extension)


class OidQorvo(DynIntEnum):
    TestDebug = 0x00  # TEST_DEBUG_NTF
    TestTxCw = 0x01  # TEST_TX_CW
    TestPllLock = 0x02  # TEST_PLLRF
    TestDiag = 0x03  # FIRA_RANGE_DIAGNOSTICS
    TestRtc = 0x04  # TEST_RTC
    SessionDataXferStatusNtf = 0x05  # SESSION_DATA_TRANSFER_STATUS_NTF
    TestTof = 0x32


class SegmentType(DynIntEnum):
    Ipatov = 0x0
    Sts0 = 0x1
    Sts1 = 0x2
    Sts2 = 0x3
    sts3 = 0x4
    Unknown = -1


class OidCalibration(DynIntEnum):
    Set = 0x2A
    Get = 0x2B


class DiagAction(DynIntEnum):
    Rx = 0
    Tx = 1
    Unknown = -1


class DiagField(enum.IntEnum):
    Aoa = 0x1
    FrameStatus = 0x3
    Cfo = 0x4
    EmitterShortAddr = 0x5
    SegmentMetrics = 0x6
    Cir = 0x7


class DiagMessage(DynIntEnum):
    RangingInitiation = 0  # RIM
    RangingResponse = 1  # RRM
    RangingFinal = 2  # RFM
    Control = 3  # CM
    MeasurementReport = 4  # MRM
    RangingResultReport = 5  # RRRM
    CU = 6  # CU
    Unknown = -1


class PllLockTestStatus(DynIntEnum):
    Success = 0
    ChannelSetError = 1
    StateSetError = 2
    Unknown = -1


class PllLockTestStatusMask(DynIntEnum):
    Ch9BistFailed = 0x4000  # PLL_STATUS_CH9_BIST_FAIL_BIT_MASK
    Ch5BistFailed = 0x2000  # PLL_STATUS_CH5_BIST_FAIL_BIT_MASK
    LockDetectStatus = 0x1F00  # PLL_STATUS_LD_CODE_BIT_MASK
    XtalAmplitudeSet = 0x0040  # PLL_STATUS_XTAL_AMP_SETTLED_BIT_MASK
    CoarseTuneCalAvailable = 0x0020  # PLL_STATUS_VCO_TUNE_UPDATE_BIT_MASK
    VcoTuneDone = 0x0010  # PLL_STATUS_PLL_OVRFLOW_BIT_MASK
    VcoFrequencyTooHigh = 0x0008  # PLL_STATUS_PLL_HI_FLAG_BIT_MASK
    VcoFrequencyTooLow = 0x0004  # PLL_STATUS_PLL_LO_FLAG_N_BIT_MASK
    PllLocked = 0x0002  # PLL_STATUS_PLL_LOCK_FLAG_BIT_MASK
    PllLockedAndCaled = 0x0001  # PLL_STATUS_CPC_CAL_DONE_BIT_MASK


class TofTestStatus(DynIntEnum):
    Pass = 0  # SUCCESS
    Error = 1  # ERROR
    Unknown = -1


class TofTestStatusMask(DynIntEnum):
    VddDig_3F = 1 << 63  # PASS (0) / FAIL (1)
    VddDig_3E = 1 << 62  # PASS (0) / FAIL (1)
    VddDig_3D = 1 << 61  # PASS (0) / FAIL (1)
    VddDig_3C = 1 << 60  # PASS (0) / FAIL (1)
    VddDig_3B = 1 << 59  # PASS (0) / FAIL (1)
    VddDig_3A = 1 << 58  # PASS (0) / FAIL (1)
    VddDig_39 = 1 << 57  # PASS (0) / FAIL (1)
    VddDig_38 = 1 << 56  # PASS (0) / FAIL (1)
    VddDig_37 = 1 << 55  # PASS (0) / FAIL (1)
    VddDig_36 = 1 << 54  # PASS (0) / FAIL (1)
    VddDig_35 = 1 << 53  # PASS (0) / FAIL (1)
    VddDig_34 = 1 << 52  # PASS (0) / FAIL (1)
    VddDig_33 = 1 << 51  # PASS (0) / FAIL (1)
    VddDig_32 = 1 << 50  # PASS (0) / FAIL (1)
    VddDig_31 = 1 << 49  # PASS (0) / FAIL (1)
    VddDig_30 = 1 << 48  # PASS (0) / FAIL (1)
    VddDig_2F = 1 << 47  # PASS (0) / FAIL (1)
    VddDig_2E = 1 << 46  # PASS (0) / FAIL (1)
    VddDig_2D = 1 << 45  # PASS (0) / FAIL (1)
    VddDig_2C = 1 << 44  # PASS (0) / FAIL (1)
    VddDig_2B = 1 << 43  # PASS (0) / FAIL (1)
    VddDig_2A = 1 << 42  # PASS (0) / FAIL (1)
    VddDig_29 = 1 << 41  # PASS (0) / FAIL (1)
    VddDig_28 = 1 << 40  # PASS (0) / FAIL (1)
    VddDig_27 = 1 << 39  # PASS (0) / FAIL (1)
    VddDig_26 = 1 << 38  # PASS (0) / FAIL (1)
    VddDig_25 = 1 << 37  # PASS (0) / FAIL (1)
    VddDig_24 = 1 << 36  # PASS (0) / FAIL (1)
    VddDig_23 = 1 << 35  # PASS (0) / FAIL (1)
    VddDig_22 = 1 << 34  # PASS (0) / FAIL (1)
    VddDig_21 = 1 << 33  # PASS (0) / FAIL (1)
    VddDig_20 = 1 << 32  # PASS (0) / FAIL (1)
    VddDig_1F = 1 << 31  # PASS (0) / FAIL (1)
    VddDig_1E = 1 << 30  # PASS (0) / FAIL (1)
    VddDig_1D = 1 << 29  # PASS (0) / FAIL (1)
    VddDig_1C = 1 << 28  # PASS (0) / FAIL (1)
    VddDig_1B = 1 << 27  # PASS (0) / FAIL (1)
    VddDig_1A = 1 << 26  # PASS (0) / FAIL (1)
    VddDig_19 = 1 << 25  # PASS (0) / FAIL (1)
    VddDig_18 = 1 << 24  # PASS (0) / FAIL (1)
    VddDig_17 = 1 << 23  # PASS (0) / FAIL (1)
    VddDig_16 = 1 << 22  # PASS (0) / FAIL (1)
    VddDig_15 = 1 << 21  # PASS (0) / FAIL (1)
    VddDig_14 = 1 << 20  # PASS (0) / FAIL (1)
    VddDig_13 = 1 << 19  # PASS (0) / FAIL (1)
    VddDig_12 = 1 << 18  # PASS (0) / FAIL (1)
    VddDig_11 = 1 << 17  # PASS (0) / FAIL (1)
    VddDig_10 = 1 << 16  # PASS (0) / FAIL (1)
    VddDig_0F = 1 << 15  # PASS (0) / FAIL (1)
    VddDig_0E = 1 << 14  # PASS (0) / FAIL (1)
    VddDig_0D = 1 << 13  # PASS (0) / FAIL (1)
    VddDig_0C = 1 << 12  # PASS (0) / FAIL (1)
    VddDig_0B = 1 << 11  # PASS (0) / FAIL (1)
    VddDig_0A = 1 << 10  # PASS (0) / FAIL (1)
    VddDig_09 = 1 << 9  # PASS (0) / FAIL (1)
    VddDig_08 = 1 << 8  # PASS (0) / FAIL (1)


class RTCTestResult(DynIntEnum):
    Pass = 0  # SUCCESS
    GpioNotFound = 1  # GPIO_NOT_FOUND
    GpioCtrlError = 2  # GPIO_CTLR_ERROR
    RtcProgError = 3  # RTC_PROG_ERROR
    RtcElapseError = 4  # RTC_ELAPSE_ERROR
    Unknown = -1


class RangingMeas(DynIntEnum):
    OwrUltdoa = 0  # OWR UL-TDoA
    Twr = 1  # TWR (SS-TWR & DS-TWR)
    OwrDltdoa = 2  # OWR DL-TDoA
    OwrAoa = 3  # OWR for AoA
    Unknown = 0xFF


class RangingMsgType(DynIntEnum):
    PollDtm = 0x00
    ResponseDtm = 0x01
    FinalDtm = 0x02
    Unknown = 0xFF


class SessionDataTransferStatusNtf(DynIntEnum):
    STATUS_REPETITION_OK = 0x00
    STATUS_OK = 0x01
    STATUS_ERROR_DATA_TRANSFER = 0x02
    STATUS_ERROR_NO_CREDIT_AVAILABLE = 0x03
    STATUS_ERROR_REJECTED = 0x04
    STATUS_SESSION_TYPE_NOT_SUPPORTED = 0x05
    STATUS_ERROR_DATA_TRANSFER_IS_ONGOING = 0x06
    Unknown = 0xFF


class RangingMsgControl:
    def __init__(self, word):
        self.time = "common" if (word & 1) == 1 else "local"
        flag = (word >> 1) & 0b11
        self.tx_time_size = 40 if (flag == 0) else 64 if (flag == 1) else "na"
        flag = (word >> 3) & 0b11
        self.rx_time_size = 40 if (flag == 0) else 64 if (flag == 1) else "na"
        dt_anchor_loc_types = ["unknown", "WGS-84", "relative", "RFU"]
        dt_anchor_loc_sizes = [0, 12, 10, 0]  # bytes (cf DL_TDOA_ANCHOR_LOCATION p 121)
        idx = (word >> 5) & 0b11
        self.dt_anchor_loc_type = dt_anchor_loc_types[idx]
        self.dt_anchor_loc_size = dt_anchor_loc_sizes[idx]
        self.n_active_ranging = (word >> 7) & 0b1111

    def __str__(self):
        rts = f"{self.time} time|tx time:{self.tx_time_size} bits|rx time: {self.rx_time_size} bits|"
        rts += f"{self.dt_anchor_loc_type} location type|{self.n_active_ranging} active ranging."
        return rts


class DlTdoaAnchorLocation:
    def __init__(self, type: str, buf: Buffer) -> None:
        self.type = type
        if type == "WGS-84":
            # Bits alignment of WGS-84 coordinates:
            # binary buffer |0 .....32|33......65|66.....95|
            #              --------------------------------
            # variable      |   lat   |   long   |   alt   |
            #              --------------------------------
            # bytes order   |LSB...MSB|LSB....MSB|LSB...MSB|
            #              --------------------------------
            location = buf.pop(12)
            # Convert location to bit stream.
            value_bin_str = "{:096b}".format(int(location.hex(), 16))
            # Retrieve bits corresponding to each location param.
            # Convert params to int.
            # Align latitude ang longitude to full bytes, example:
            # -128.0 -> 00000000 00000000 00000000 10000000 1 (Q9.24 little endian)
            # 1 10000000 00000000 00000000 00000000 (Q9.24 big endian)
            # 11111111 10000000 00000000 00000000 00000000 (Q9.24 extended big endian).
            latitude = (int(value_bin_str[0:33], 2) << 7) + (
                2**7 - 1 if value_bin_str[32] == "1" else 0
            )
            self.latitude = FP(latitude, True, 8, 24, True, "big").as_float()
            longitude = (int(value_bin_str[33:66], 2) << 7) + (
                2**7 - 1 if value_bin_str[65] == "1" else 0
            )
            self.longitude = FP(longitude, True, 8, 24, True, "big").as_float()

            # Altitude needs special swapping as it's not aligned:
            # -256.0 -> 00000000 00000000 00000000 100000 (Q9.21 little endian)
            # 100000 00000000 00000000 00000000 (Q9.21 big endian).

            # Extract altitude for easier bit-number manipulation.
            alt_str = value_bin_str[66:96]
            # Extension to 32 bytes.
            alt_prefix = "11" if alt_str[24] == "1" else "00"
            # Swap bytes.
            alt_str = f"{alt_prefix}{alt_str[24:30]}{alt_str[16:24]}{alt_str[8:16]}{alt_str[0:8]}"
            self.altitude = FP(int(alt_str, 2), True, 8, 21, True, "little").as_float()

        elif type == "relative":
            # Bits alignment of relative coordinates:
            # binary buffer |0 .....27|28......55|56.....80|
            #              --------------------------------
            # variable      |    x    |    y     |    z    |
            #              --------------------------------
            # bytes order   |LSB...MSB|LSB....MSB|LSB...MSB|
            #              --------------------------------
            location = buf.pop(10)
            # Convert location to bit stream.
            value_bin_str = "{:080b}".format(int(location.hex(), 16))
            # When converting 28 bit value to 38 bit value, bits 24:28 are most significant so
            # they need to be artificially injected and filled with '1' if value is negative.
            x_b_prefix = "1111" if value_bin_str[24] == "1" else "0000"
            # Create 32 bit binary string.
            x_b = f"{value_bin_str[0:24]}{x_b_prefix}{value_bin_str[24:28]}"
            # Use FP class to Swap endianness.
            self.x = FP(int(x_b, 2), True, 27, 0, True, "big").as_int()
            # Same steps as above.
            y_b_prefix = "1111" if value_bin_str[52] == "1" else "0000"
            y_b = f"{value_bin_str[28:52]}{y_b_prefix}{value_bin_str[52:56]}"
            self.y = FP(int(y_b, 2), True, 27, 0, True, "big").as_int()
            # Decoding z is easier because it's aligned to full bytes.
            z = int(value_bin_str[56:80], 2)
            self.z = FP(z, True, 23, 0, True, "big").as_int()

    def __str__(self) -> str:
        if self.type == "WGS-84":
            return f"latitude:{self.latitude}|longitude:{self.longitude}|altitude:{self.altitude}"
        elif self.type == "relative":
            return f"x:{self.x}|y:{self.y}|z:{self.z}"
        else:
            return "not present"


# =============================================================================
# Additional Qorvo NTF Data (all in Natural numbers)
# =============================================================================


@dataclass
class RangingTwrData:
    """
    This class is used by RangingData (RANGE_DATA_NTF) for TWR type measurements.
    Description in Fira UCI Generic Technical Specification 2.0.0-0.9r2 p70
    """

    meas_n: int
    mac_add: str
    status: Status
    nlos: bool
    distance: float
    aoa_tetha: float
    aoa_tetha_fom: float
    aoa_phi: float
    aoa_phi_fom: float
    aoa_dest_tetha: float
    aoa_dest_tetha_fom: float
    aoa_dest_phi: float
    aoa_dest_phi_fom: float
    slot_in_error: int
    rssi: float

    def __init__(self, b: Buffer, mac_add_size, meas_n):
        self.mac_add_size = mac_add_size
        self.meas_n = meas_n
        self.mac_add = b.pop_reverse(self.mac_add_size).hex(
            ":"
        )  # MAC Address (2 or 8 bytes)
        self.status = Status(b.pop_uint(1))  # Status
        self.nlos = IsTrue(b.pop_uint(1))  # Is a non-Line of sight measurement?
        self.distance = float(b.pop_uint(2))  # distance in cm using  C=299,702,547 m/s.
        self.aoa_tetha = b.pop_float(
            True, 8, 7
        )  # AoA azimuth (deg) ranging from -180 to 180 deg
        self.aoa_tetha_fom = float(
            b.pop_uint(1)
        )  # AOA azimuth estimator reliability. in % (100%: best) or 0.
        self.aoa_phi = b.pop_float(
            True, 8, 7
        )  # AoA elevation (deg) ranging from -90 to 90 deg
        self.aoa_phi_fom = float(
            b.pop_uint(1)
        )  # AOA elevation estimator reliability. in %(100%: best) or 0.
        self.aoa_dest_tetha = b.pop_float(
            True, 8, 7
        )  # AoA dest. azimuth ranging        if MRR=1 else 0
        self.aoa_dest_tetha_fom = float(
            b.pop_uint(1)
        )  # AOA dest. azimuth reliability    if MRR=1 else 0
        self.aoa_dest_phi = b.pop_float(
            True, 8, 7
        )  # AoA dest. elevation ranging      if MRR=1 else 0
        self.aoa_dest_phi_fom = float(
            b.pop_uint(1)
        )  # AOA dest. elevation reliability  if MRR=1 else 0
        self.slot_in_error = b.pop_uint(
            1
        )  # if failure, error position slot number (first slot is slot # 0)
        self.rssi = -1 * b.pop_float(
            False, 7, 1
        )  # rssi of the slot in error, or min. RSSI, or 0
        b.pop(11 if self.mac_add_size == 2 else 5)  # RFU

    def __str__(self) -> str:
        return f"""        # Measurement {self.meas_n}:
            status:             {self.status.name} ({hex(self.status.value)})
            mac address:        {self.mac_add} hex
            is nlos meas:       {self.nlos.name}
            distance:           {self.distance} cm
            AoA azimuth:        {self.aoa_tetha} deg
            AoA az. FOM:        {self.aoa_tetha_fom} %
            AoA elevation:      {self.aoa_phi} deg
            AoA elev. FOM:      {self.aoa_phi_fom}
            AoA dest azimuth:   {self.aoa_dest_tetha} deg
            AoA dest az. FOM:   {self.aoa_dest_tetha_fom} %
            AoA dest elevation: {self.aoa_dest_phi} deg
            AoA dest elev. FOM: {self.aoa_dest_phi_fom} %
            slot in error:      {self.slot_in_error}
            rssi:               {self.rssi} dBm\n"""


@dataclass
class RangingOwrAoaData:
    """
    This class is used by RangingData (RANGE_DATA_NTF) for OWR for AoA type measurements.
    Description in Fira UCI Generic Technical Specification 2.0.0-0.9r2 p72
    """

    meas_n: int
    mac_add: str
    status: Status
    nlos: bool
    frame_sequence_number: int
    block_index: int
    aoa_azimuth: float
    aoa_azimuth_fom: float
    aoa_elevation: float
    aoa_elevation_fom: float

    def __init__(self, b: Buffer, mac_add_size, meas_n):
        self.mac_add_size = mac_add_size
        self.meas_n = meas_n
        self.mac_add = b.pop_reverse(self.mac_add_size).hex(
            ":"
        )  # MAC Address (2 or 8 bytes)
        self.status = Status(b.pop_uint(1))  # Status
        self.nlos = IsTrue(b.pop_uint(1))  # Is a non-Line of sight measurement?
        self.frame_sequence_number = b.pop_uint(1)  # Sequence number as received in MHR
        self.block_index = b.pop_uint(
            2
        )  # Block Index number from Advertiser OWR message
        self.aoa_azimuth = b.pop_float(
            True, 8, 7
        )  # AoA azimuth (deg) ranging from -180 to 180 deg
        self.aoa_azimuth_fom = float(
            b.pop_uint(1)
        )  # AOA azimuth estimator reliability. in % (100%: best) or 0.
        self.aoa_elevation = b.pop_float(
            True, 8, 7
        )  # AoA elevation (deg) ranging from -90 to 90 deg
        self.aoa_elevation_fom = float(
            b.pop_uint(1)
        )  # AOA elevation estimator reliability. in %(100%: best) or 0.

    def __str__(self) -> str:
        return f"""        # Measurement {self.meas_n}:
            status:             {self.status.name} ({hex(self.status.value)})
            mac address:        {self.mac_add} hex
            is nlos meas:       {self.nlos.name}
            frame sequence num: {self.frame_sequence_number}
            bloc idx:           {self.block_index}
            AoA azimuth:        {self.aoa_azimuth} deg
            AoA az. FOM:        {self.aoa_azimuth_fom} %
            AoA elevation:      {self.aoa_elevation} deg
            AoA elev. FOM:      {self.aoa_elevation_fom} %\n"""


@dataclass
class RangingOwrUltdoaData:
    """
    This class is used by RangingData (RANGE_DATA_NTF) for  OWR UL TDoA measurements.
    Description in Fira UCI Generic Technical Specification 2.0.0-0.9r2 p68
    """

    meas_n: int
    mac_add: str
    status: Status
    msg_control: RangingMsgControl
    frame_type: int
    nlos: bool
    aoa_tetha: float
    aoa_tetha_fom: float
    aoa_phi: float
    aoa_phi_fom: float
    frame_n: str
    rx_time: float
    device_id: str
    tx_time: str

    def __init__(self, b: Buffer, mac_add_size, meas_n):
        self.mac_add_size = mac_add_size
        self.meas_n = meas_n
        self.mac_add = b.pop_reverse(self.mac_add_size).hex(
            ":"
        )  # MAC Address (2 or 8 bytes)
        self.status = Status(b.pop_uint(1))  # Status
        self.msg_control = RangingMsgControl(b.pop_uint(2))  # message control
        self.frame_type = b.pop_uint(
            1
        )  # Frame type. 0: UT-Tag, 1: UT-Synchronization Anchor
        self.nlos = IsTrue(b.pop_uint(1))  # Is a non-Line of sight measurement?
        self.aoa_tetha = b.pop_float(
            True, 8, 7
        )  # AoA azimuth (deg) ranging from -180 to 180 deg
        self.aoa_tetha_fom = float(
            b.pop_uint(1)
        )  # AOA azimuth estimator reliability. in % (100%: best) or 0.
        self.aoa_phi = b.pop_float(
            True, 8, 7
        )  # AoA elevation (deg) ranging from -90 to 90 deg
        self.aoa_phi_fom = float(
            b.pop_uint(1)
        )  # AOA elevation estimator reliability. in %(100%: best) or 0.
        self.frame_n = hex(b.pop_uint(4))  # As received in the UT payload
        n = self.msg_control.rx_time_size // 8
        self.rx_time = b.pop_uint(
            n
        )  # in Ranging Ticks. unit is ? of the 499.2 MHz chipping T ~ 15.65ps.
        # As of 2.0.0-0.9r2 p68, Below Spec is not finished. Waiting to be...
        # ~ self.device_id=b.pop(0/2/4/8)                   # As received in the UT payload
        # ~ n = self.msg_control.tx_time_size//8
        # ~ self.tx_time=b.pop_uint(n)*0.01565              # in ns. unit is ? of the 499.2 MHz chipping T ~ 15.65ps.
        self.device_id = "na"
        self.tx_time = "na"

    def __str__(self) -> str:
        return f"""        # Measurement {self.meas_n}:
            status:             {self.status.name} ({hex(self.status.value)})
            mac address:        {self.mac_add} hex
            message control:    {self.msg_control}
            frame type:         {'UT-tag' if self.frame_type==0 else 'UT-Synchronization' if self.frame_type==1 else 'na'}
            is nlos meas:       {self.nlos.name}
            AoA azimuth:        {self.aoa_tetha} deg
            AoA az. FOM:        {self.aoa_tetha_fom} %
            AoA elevation:      {self.aoa_phi} deg
            AoA elev. FOM:      {self.aoa_phi_fom}
            frame number        {self.frame_n}
            rx time:            {self.rx_time} Ranging Ticks
            device id           {self.device_id}
            tx time:            {self.tx_time} Ranging Ticks\n"""


@dataclass
class RangingOwrDltdoaData:
    """
    This class is used by RangingData (RANGE_DATA_NTF) for OWR DL TDoA measurements.
    Description in Fira UCI Generic Technical Specification 2.0.0-0.9r2 p73
    """

    meas_n: int
    mac_add: str
    status: Status
    msg_type: RangingMsgType
    msg_control: RangingMsgControl
    block_idx: int
    round_idx: int
    nlos: bool
    aoa_tetha: float
    aoa_tetha_fom: float
    aoa_phi: float
    aoa_phi_fom: float
    rssi: float
    tx_time: float
    rx_time: float
    anchor_cfo: float
    cfo: float
    initiator_reply_time: float
    responder_reply_time: float
    anchor_location: DlTdoaAnchorLocation
    active_rounds: str

    def __init__(self, b: Buffer, mac_add_size, meas_n):
        self.mac_add_size = mac_add_size
        self.meas_n = meas_n
        self.mac_add = "na"
        self.status = "na"
        self.msg_type = "na"
        self.msg_control = "na"
        self.block_idx = "na"
        self.round_idx = "na"
        self.nlos = "na"
        self.aoa_tetha = "na"
        self.aoa_tetha_fom = "na"
        self.aoa_phi = "na"
        self.aoa_phi_fom = "na"
        self.rssi = "na"
        self.tx_time = "na"
        self.rx_time = "na"
        self.anchor_cfo = "na"
        self.cfo = "na"
        self.initiator_reply_time = "na"
        self.responder_reply_time = "na"
        self.tof = "na"
        self.anchor_location = "na"
        self.active_rounds = "na"
        try:
            self.mac_add = b.pop_reverse(self.mac_add_size).hex(
                ":"
            )  # MAC Address (2 or 8 bytes)
            self.status = Status(b.pop_uint(1))  # Status
            self.msg_type = RangingMsgType(
                b.pop_uint(1)
            )  # packet received message type.
            self.msg_control = RangingMsgControl(b.pop_uint(2))  # message control
            self.block_idx = b.pop_uint(2)  # Block Index of the current ranging block.
            self.round_idx = b.pop_uint(1)  # Round Index of the current ranging round.
            self.nlos = IsTrue(b.pop_uint(1))  # Is a non-Line of sight measurement?
            self.aoa_tetha = b.pop_float(
                True, 8, 7
            )  # AoA azimuth (deg) ranging from -180 to 180 deg
            self.aoa_tetha_fom = float(
                b.pop_uint(1)
            )  # AOA azimuth estimator reliability. in % (100%: best) or 0.
            self.aoa_phi = b.pop_float(
                True, 8, 7
            )  # AoA elevation (deg) ranging from -90 to 90 deg
            self.aoa_phi_fom = float(
                b.pop_uint(1)
            )  # AOA elevation estimator reliability. in %(100%: best) or 0.
            self.rssi = -1 * b.pop_float(
                False, 7, 1
            )  # Minimum rssi or 0 if not supported/available
            n = self.msg_control.tx_time_size // 8
            self.tx_time = b.pop_uint(
                n
            )  # in Ranging Ticks. unit is ? of the 499.2 MHz chipping T ~ 15.65ps.
            n = self.msg_control.rx_time_size // 8
            self.rx_time = b.pop_uint(
                n
            )  # in Ranging Ticks. unit is ? of the 499.2 MHz chipping T ~ 15.65ps.
            self.anchor_cfo = b.pop_float(
                True, 5, 10
            )  # Reported CFO of a responder Vs initiator (in ppm units).
            self.cfo = b.pop_float(
                True, 5, 10
            )  # Measured CFO from the sender (in ppm units).
            self.initiator_reply_time = b.pop_uint(
                4
            )  # in Ranging Ticks. time difference measured by the Initiator DT-Anchor (in 15.65ps. units)
            self.responder_reply_time = b.pop_uint(
                4
            )  # in Ranging Ticks. time difference measured at the Responder DT-Anchor (in 15.65ps units)
            self.tof = b.pop_uint(
                2
            )  # in Ranging Ticks. ToF between the Responder and the Initiator  (in 15.65ps units)
            self.anchor_location = DlTdoaAnchorLocation(
                self.msg_control.dt_anchor_loc_type, b
            )
            n = self.msg_control.n_active_ranging
            self.active_rounds = b.pop(n).hex(
                "."
            )  # List of ranging round indexes in where the DT-Anchor is present.
        except ValueError as v:
            logger.warning(v)

    def __str__(self) -> str:
        return f"""        # Measurement {self.meas_n}:
            status:             {self.status.name} ({hex(self.status.value)})
            mac address:        {self.mac_add} hex
            message type:       {self.msg_type}
            message control:    {self.msg_control}
            block index:        {self.block_idx}
            round index:        {self.round_idx}
            is nlos meas:       {self.nlos.name}
            AoA azimuth:        {self.aoa_tetha} deg
            AoA az. FOM:        {self.aoa_tetha_fom} %
            AoA elevation:      {self.aoa_phi} deg
            AoA elev. FOM:      {self.aoa_phi_fom}
            rssi:               {self.rssi} dBm
            rx time:            {self.rx_time} Ranging Ticks
            tx time:            {self.tx_time} Ranging Ticks
            anchor cfo:         {self.anchor_cfo} ppm
            cfo:                {self.cfo} ppm
            initiator TD:       {self.initiator_reply_time} Ranging Ticks
            responder TD:       {self.responder_reply_time} Ranging Ticks
            ToF:                {self.tof} Ranging Ticks
            anchor location:    {self.anchor_location}
            active round:       {self.active_rounds}\n"""


@dataclass
class RangingData:
    """
    This class is encapsulatin RANGE_DATA_NTF data
    as described in Fira UCI Generic Technical Specification 2.0.0-0.9r2 p67
    All values are in 'natural number' format.
    """

    gid: Gid
    oid: OidRanging
    meas: list
    idx: int
    session_handle: int
    ranging_interval: int
    ranging_meas: RangingMeas
    primary_session_id: str

    def __init__(self, payload: bytes):
        self.gid = Gid.Ranging
        self.oid = OidRanging.Start
        self.payload = payload
        self.meas = []
        self.buffer = Buffer(payload)
        self.idx = self.buffer.pop_uint(4)  # Sequence Counter start at 0.
        self.session_handle = self.buffer.pop_uint(4)  # Session ID of the ranging Round
        self.buffer.pop(1)  # RFU
        self.ranging_interval = self.buffer.pop_uint(
            4
        )  # Ranging interval setting in the unit of 1200 RSTU (=1ms).
        self.ranging_meas = RangingMeas(
            self.buffer.pop_uint(1)
        )  # Ranging Measurement Type
        self.buffer.pop(1)  # RFU
        self.mac_add_size = (
            2 if self.buffer.pop_uint(1) == 0 else 8
        )  # MAC Addressing Mode. 0: 2 Bytes, 1: 8 Bytes.
        self.primary_session_id = hex(
            self.buffer.pop_uint(4)
        )  # Session ID of the primary session or 0
        self.buffer.pop(4)  # RFU
        self.n_meas = self.buffer.pop_uint(1)  # number of measurements
        if self.ranging_meas == RangingMeas.Unknown:
            logger.warning("RangingData: Unknown ranging measurement type.")
            logger.warning(f"Dropping the {self.n_meas} Measurements.")
            self.n_meas = 0
        for i in range(self.n_meas):
            if self.ranging_meas == RangingMeas.OwrAoa:
                x = RangingOwrAoaData(self.buffer, self.mac_add_size, i + 1)
            elif self.ranging_meas == RangingMeas.Twr:
                x = RangingTwrData(self.buffer, self.mac_add_size, i + 1)
            elif self.ranging_meas == RangingMeas.OwrDltdoa:
                x = RangingOwrDltdoaData(self.buffer, self.mac_add_size, i + 1)
            elif self.ranging_meas == RangingMeas.OwrUltdoa:
                # Will break after first loop:
                # As of 2.0.0-0.9r2 p68, RangingOwrUltdoaData Spec is not finished...
                x = RangingOwrUltdoaData(self.buffer, self.mac_add_size, i + 1)
            self.meas.append(x)
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f"RangingData: {self.buffer.remaining_size()} unhandled remaining bytes."
            )

    def __str__(self) -> str:
        rts = f"""# Ranging Data:
        session handle:         {self.session_handle}
        sequence n:         {self.idx}
        ranging interval:   {self.ranging_interval} ms
        measurement type:   {self.ranging_meas.name}
        Mac add size:       {self.mac_add_size}
        primary session id: {self.primary_session_id}
        n of measurement:   {self.n_meas}\n"""
        for i in range(self.n_meas):
            rts += str(self.meas[i])
        return rts


@dataclass
class FrameStatusField:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    frame_status: int

    def __init__(self, b: Buffer, field_n: int):
        self.field_n = field_n
        b.pop_uint(2)  # Field Size 2 expected.
        self.frame_status = b.pop_uint(2)  # Frame status bit field

    def __str__(self) -> str:
        return f"""\
            # Frame Status Report:
                is processing ok  : {(self.frame_status & FrameStatusMask.FrameProcessedOk)//FrameStatusMask.FrameProcessedOk}
                is wifi activated : {(self.frame_status & FrameStatusMask.WifiActivationDuringFrame)//
                                     FrameStatusMask.WifiActivationDuringFrame}\n"""


@dataclass
class SegmentMetricsItem:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    idx: int
    segment_type: SegmentType
    primary_recv: int
    receiver_id: str
    noise_value: float
    rsl_dbm: float
    path1_idx: int
    path1_rsl_dbm: float
    path1_snr: float
    path1_t: int
    peak_idx: int
    peak_rsl_dbm: float
    peak_snr: float
    peak_t: int

    def __init__(self, b: Buffer, idx: int):
        self.idx = idx
        a = b.pop_uint(1)  # Receiver/segment Id
        self.segment_type = SegmentType(a & 0x7)
        self.primary_recv = (
            a & 0x8
        ) >> 3  # primary receiver indicator, bit is set if the receiver is the primary
        self.receiver_id = hex((a & 0xF0) >> 4)
        self.noise_value = b.pop_int(2)  # noise value
        self.rsl_dbm = -(b.pop_float(False, 8, 8))  # RSL in human readable format dBm
        self.path1_idx = b.pop_uint(
            2
        )  # absolute index of the sample considered as the first path
        self.path1_rsl_dbm = -(b.pop_float(False, 8, 8))  # First path RSL (dBm)
        self.path1_snr = self.path1_rsl_dbm - self.noise_value  # first path SNR
        self.path1_t = b.pop_uint(2)  # first path time (ns)
        self.peak_idx = b.pop_uint(2)  # peak path absolute index
        self.peak_rsl_dbm = -(b.pop_float(False, 8, 8))  # Peak path RSL (dBm)
        self.peak_snr = self.peak_rsl_dbm - self.noise_value  # peak path SNR
        self.peak_t = b.pop_uint(2)  # first path time (ns)

    def __str__(self) -> str:
        return f"""\
                # Segment Metrics       {self.idx}:
                    segment type:       {self.segment_type}
                    primary_recv:       {self.primary_recv}
                    receiver Id:        {self.receiver_id}
                    noise_value:        {self.noise_value}
                    rsl_dBm:            {self.rsl_dbm}
                    path1_rsl_dbm:      {self.path1_rsl_dbm}
                    path1_idx:          {self.path1_idx}
                    path1_snr:          {self.path1_snr}
                    path1_t:            {self.path1_t}
                    peak_rsl_dbm:       {self.peak_rsl_dbm}
                    peak_idx:           {self.peak_idx}
                    peak_snr:           {self.peak_snr}
                    peak_t:             {self.peak_t}\n"""


@dataclass
class SegmentMetricsDiagField:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    segment_metrics: list

    def __init__(self, b: Buffer, field_n: int):
        self.field_n = field_n
        size = b.pop_uint(2)  # Field Size. 1 measurement == 17 bytes.
        self.n_seg_metrics = size // 17
        self.segment_metrics = []
        for i in range(self.n_seg_metrics):
            a = SegmentMetricsItem(b, i)
            self.segment_metrics.append(a)

    def __str__(self) -> str:
        rtv = f"""\
            # Segment Metrics Reports:
                Nbr of Segment Metrics: {len(self.segment_metrics)} \n"""
        for a in self.segment_metrics:
            rtv += str(a)
        return rtv


@dataclass
class AoaItem:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    idx: int
    tdoa: float
    pdoa: float
    aoa: float
    aoa_fom: int
    aoa_type: AoaType

    def __init__(self, b: Buffer, idx: int):
        self.idx = idx
        self.tdoa = b.pop_float(True, 4, 11)
        self.pdoa = 180 * b.pop_float(True, 4, 11) / 3.14
        self.aoa = 180 * b.pop_float(True, 4, 11) / 3.14
        self.aoa_fom = b.pop_uint(1)
        self.aoa_type = AoaType(b.pop_uint(1))

    def __str__(self) -> str:
        return f"""\
            # AoA Report on axis {self.idx}:
                TDoA:     {self.tdoa}
                PDoA:     {self.pdoa} deg
                AoA:      {self.aoa}  deg
                AoA FOM:  {self.aoa_fom} %
                AoA Type: {self.aoa_type.name}\n"""


@dataclass
class AoaDiagField:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    aoa: list

    def __init__(self, b: Buffer, field_n: int):
        self.field_n = field_n
        size = b.pop_uint(2)  # Field Size. 1 measurement == 8 bytes.
        self.n_axis = (
            size // 8
        )  # Depend on Antenna capabilities (so far, only 1 measurement seen)
        self.aoa = []
        for i in range(self.n_axis):
            a = AoaItem(b, i)
            self.aoa.append(a)

    def __str__(self) -> str:
        rtv = ""
        for a in self.aoa:
            rtv = rtv + str(a)
        return rtv


@dataclass
class CFODiagField:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    cfo: float

    def __init__(self, b: Buffer, field_n: int):
        self.field_n = field_n
        b.pop_uint(2)  # cfo size
        self.cfo = b.pop_float(True, 5, 26) * 1e6  # ratio -> ppm

    def __str__(self) -> str:
        return f"""\
            # CFO Report:
                cfo:     {round(self.cfo, 3) if type(self.cfo) is float else self.cfo} ppm\n"""


@dataclass
class UnknownDiagField:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    def __init__(self, b: Buffer, field_n: int, report_type: int):
        self.field_n = field_n
        self.report_type = report_type
        size = b.pop_uint(2)  # Field Size.
        self.data = b.pop(size)  # Purge buffer from unknown data

    def __str__(self) -> str:
        return f"""\
            # Unknown Report (of type {self.report_type}):
                bytes:   {self.data}\n"""


@dataclass
class CirDiagField:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    cir: list

    def __init__(self, b: Buffer, field_n: int):
        self.field_n = field_n
        self.cir = []
        size = b.pop_uint(2)  # Size of All CIRs 143*n+1 expected

        class C:
            pass

        while size > 0:
            c = C()
            a = b.pop_uint(1)  # Receiver/segment Id
            c.segment_type = SegmentType(a & 0x7)
            c.primary_recv = (
                a & 0x8
            ) >> 3  # primary receiver indicator, bit is set if the receiver is the primary
            c.receiver_id = hex((a & 0xF0) >> 4)
            c.path1_ridx = b.pop_uint(
                1
            )  # first path relative index (within the sample window)
            c.n_samples = b.pop_uint(1)  # window size
            c.sample_size = b.pop_uint(1)  # sample size  (i,q) samples
            c.samples = []
            iq_size = c.sample_size // 2  # Expected to be 4
            for j in range(c.n_samples):  # list of (i,q) samples. Expected to be signed
                c.samples.append((b.pop_int(iq_size), b.pop_int(iq_size)))
            self.cir.append(c)
            size = size - 4 - c.sample_size * c.n_samples

    def __str__(self) -> str:
        rts = f"""\
            # CIR Report:
                Nbr of CIRs: {len(self.cir)} \n"""
        for i in range(len(self.cir)):
            rts += f"""\
                # CIR {i}:
                    segment type: {self.cir[i].segment_type}
                    primary_recv: {self.cir[i].primary_recv}
                    receiver Id:  {self.cir[i].receiver_id}
                    path1_ridx:   {self.cir[i].path1_ridx}
                    n_samples :   {self.cir[i].n_samples}
                    sample_size:  {self.cir[i].sample_size}
                    window (i,q): {self.cir[i].samples[0:4]}
                                  {self.cir[i].samples[4:8]}
                                  {self.cir[i].samples[8:12]}
                                  {self.cir[i].samples[12:]} \n"""
        return rts


@dataclass
class RangingDiagReport:
    """
    This class in used by RangingDiagData (RANGE_DIAGNOSTICS_NTF data)
    """

    report_n: int
    fields: list
    msg_id: str
    action: str
    antenna_set: str
    n_fields: int

    def __init__(self, b: Buffer, i: int):
        self.report_n = i
        self.fields = []
        self.msg_id = "na"
        self.action = "na"
        self.antenna_set = "na"
        self.n_fields = "na"
        try:
            self.msg_id = DiagMessage(b.pop_uint(1))
            self.action = DiagAction(b.pop_uint(1))
            self.antenna_set = b.pop_uint(1)
            self.n_fields = b.pop_uint(1)
            for i in range(self.n_fields):
                report_type = b.pop_uint(1)
                if report_type == DiagField.SegmentMetrics:
                    x = SegmentMetricsDiagField(b, i)
                elif report_type == DiagField.Aoa:
                    x = AoaDiagField(b, i)
                elif report_type == DiagField.Cir:
                    x = CirDiagField(b, i)
                elif report_type == DiagField.FrameStatus:
                    x = FrameStatusField(b, i)
                elif report_type == DiagField.Cfo:
                    x = CFODiagField(b, i)
                else:
                    x = UnknownDiagField(b, i, report_type)
                self.fields.append(x)
        except ValueError as e:
            logger.warning(f"{self.__class__.__name__} bad decoding: {e}")

    def __str__(self) -> str:
        rts = f"""\
        # Ranging Diag. Report {self.report_n}:
            Message id:    {self.msg_id.name}
            Action:        {self.action.name}
            Antenna_set:   {self.antenna_set}
            Nbr of fields: {self.n_fields} \n"""
        for f in self.fields:
            rts += str(f)
        return rts


@dataclass
class RangingDiagData:
    """
    This class is encapsulating RANGE_DIAGNOSTICS_NTF data
    as described in Qorvo Mobile UWB Diagnostic Specification p.12.
    All values are in 'natural number' format.
    """

    session_handle: int
    sequence_n: int
    n_reports: int
    reports: list

    def __init__(self, payload: bytes):
        self.gid = Gid.Qorvo
        self.oid = OidQorvo.TestDiag
        self.payload = payload
        self.reports = []
        b = Buffer(payload)
        self.session_handle = "na"
        self.sequence_n = "na"
        self.n_reports = "na"
        try:
            self.session_handle = b.pop_uint(4)  # related session
            self.sequence_n = b.pop_uint(
                4
            )  # sequence number (same as the related RANGE_DATA_NTF)
            self.n_reports = b.pop_uint(1)  # number of frames reports
            for i in range(self.n_reports):
                x = RangingDiagReport(b, i)
                self.reports.append(x)
            if b.remaining_size() != 0:
                logger.warning(
                    f"RangingDiagData: {b.size()} unhandled remaining bytes."
                )
        except ValueError as e:
            logger.warning(f"{self.__class__.__name__} bad decoding: {e}")

    def __str__(self) -> str:
        rts = f"""# Ranging Diagnostic Data:
        Session handle:     {self.session_handle}
        Sequence n:     {self.sequence_n}
        Nbr of reports: {self.n_reports} \n"""
        for i in range(self.n_reports):
            rts += str(self.reports[i])
        return rts

    def get_aoa_report(self):
        aoa_report = []
        for r in self.reports:
            report = asdict(r)
            # Ranging Response contain AoA/PDOA
            if report["msg_id"] == DiagMessage.RangingResponse:
                for field in report["fields"]:
                    if "aoa" in field:
                        aoa_report.append(field["aoa"])
        return aoa_report

    def get_cir_report(self):
        cir_report = []
        for r in self.reports:
            report = asdict(r)
            # Ranging Response contains CIR
            if report["msg_id"] == DiagMessage.RangingResponse:
                for field in report["fields"]:
                    if "cir" in field:
                        cir_report.append(field["cir"])
        return cir_report


# =============================================================================
# Qorvo Test NTF Data
# =============================================================================


class TestDebugData:
    """
    This class is encapsulating TEST_DEBUG_NTF data
    as described in Qorvo Mobile Factory Test Specification 2.0.pdf dated 2022.10.10 p. 26
    All values are returned in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.gid = Gid.Qorvo
        self.oid = OidQorvo.TestDebug
        self.payload = payload
        b = Buffer(payload)
        self.pdoa_tetha = b.pop_float(
            True, 8, 7
        )  # PDoA azimuth (deg) ranging from -180 to 180 deg
        self.pdoa_phi = b.pop_float(
            True, 8, 7
        )  # PDoA elevation (deg) ranging from -90 to 90 deg
        self.n_rssi = b.pop_int(1)  # Number of RSSIs
        self.rssis = []
        for n in range(self.n_rssi):
            self.rssis.append(-b.pop_float(False, 8, 8))  # in dBm
        self.noise_val = b.pop_int(2)  # in dB
        self.aoa_tetha = b.pop_float(
            True, 8, 7
        )  # AoA azimuth (deg) ranging from -180 to 180 deg
        self.aoa_phi = b.pop_float(
            True, 8, 7
        )  # AoA elevation (deg) ranging from -90 to 90 deg
        self.cfo = "na"
        if b.remaining_size() >= 4:
            self.cfo = (
                b.pop_float(True, 5, 26) * 1e6
            )  # Clock Frequency Offset. Tx_clock - Rx_clock in ppm
        if b.remaining_size() != 0:
            logger.warning(f"TestDebugData: {b.size()} unhandled remaining bytes.")

    def __str__(self) -> str:
        return f"""# Test Debug Data:
        Number of RSSI:  {self.n_rssi}
        RSSI:            {" | ".join([f"{rssi} dBm" for rssi in self.rssis])}
        Noise Value:     {self.noise_val} dB
        PDoA azimuth:    {self.pdoa_tetha} deg
        PDoA elevation:  {self.pdoa_phi} deg
        AoA azimuth:     {self.aoa_tetha} deg
        AoA elevation:   {self.aoa_phi} deg
        CFO:             {round(self.cfo, 3) if type(self.cfo) is float else self.cfo} ppm\n"""


class PllLockTestOutput:
    """
    This class is encapsulating TEST_PLL_LOCK_NTF data
    as described in Qorvo Mobile Factory Test Specification 2.0.pdf dated 2022.10.10 p. 23
    Warning: T, L, V are all coded in the bytestream with size(T)==size(L)=1.
    All values are returned in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.gid = Gid.Qorvo
        self.oid = OidQorvo.TestPllLock
        self.payload = payload
        b = Buffer(payload)
        count = b.pop_uint(1)  # Number of reports
        self.reports = []
        for i in range(count):
            report_type = b.pop_uint(1)
            report_size = b.pop_uint(1)
            if report_type == 0x01:  # Status
                self.reports.append(PllLockTestStatus(b.pop_uint(1)))
            elif report_type == 0x02:  # Report Status
                self.reports.append(b.pop_uint(4))
            else:
                logger.warning(
                    f'PllLockTestOutput: "{report_type}" unknown report type of size {report_size}.'
                )
                b.pop(report_size)
        if b.remaining_size() != 0:
            logger.warning(
                f"PllLockTestOutput: {b.remaining_size()} unhandled remaining bytes."
            )

    def __str__(self) -> str:
        rts = "# Test PLL Data:\n"
        idx = 0
        for r in self.reports:
            idx = idx + 1
            if isinstance(r, PllLockTestStatus):
                rts = (
                    rts + f"    Report {idx}: Test Result: {r.name} ({hex(r.value)})\n"
                )
            else:
                rts = rts + f"    Report {idx}: Lock Status ({hex(r)}):\n"
                for m in PllLockTestStatusMask:
                    if m == PllLockTestStatusMask.LockDetectStatus:
                        rts = rts + f"           -{m.name:<25}: {(r & m.value)>>8}\n"
                    else:
                        rts = (
                            rts
                            + f"           -{m.name:<25}: {(r & m.value)//m.value}\n"
                        )
        return rts[:-1]


class SetOffsetCode:
    def __init__(self, offset_code):
        global OFFSET_CODE
        OFFSET_CODE = offset_code


class TofTestOutput:
    """
    This class is encapsulating TEST_TOF_NTF data.
    Warning: T, L, V are all coded in the bytestream with size(T)==size(L)=1.
    All values are returned in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.end_pattern = "ENDTOF"
        self.gid = Gid.Qorvo
        self.oid = OidQorvo.TestTof
        self.payload = payload
        b = Buffer(payload)
        count = b.pop_uint(1)  # Number of reports
        self.reports = []
        for i in range(count):
            report_type = b.pop_uint(1)
            report_size = b.pop_uint(4)
            if report_type == 0x01:  # Status
                self.reports.append(TofTestStatus(b.pop_uint(1)))
            elif report_type == 0x02:  # Report Status
                for el in range(0, report_size):
                    self.reports.append(b.pop_uint(1))
            else:
                logger.warning(
                    f'TofTestOutput: "{report_type}" unknown report type of size {report_size}.'
                )
                b.pop(report_size)
        if b.remaining_size() != 0:
            logger.warning(
                f"TofTestOutput: {b.remaining_size()} unhandled remaining bytes."
            )

    def coarse(self, voltage):
        return (voltage & 0xF0) >> 4

    def trim(self, voltage):
        return voltage & 0x0F

    def vdddig_code_to_mv(self, current, reference):
        if self.coarse(reference) == 0x02:
            ref_v = 1.06
        else:
            ref_v = 0.96

        trim_diff = self.trim(current) - self.trim(reference)
        coarse_diff = self.coarse(current) - self.coarse(reference)
        abs_current = round(ref_v + trim_diff * 0.01 + coarse_diff * 0.1, 2)

        return abs_current

    def __str__(self) -> str:
        tof_tests_l = ["VDDIG", "1", "4", "5", "7", "15", "17", "19", "22", "23", "24"]
        res_dir = {}
        for el in tof_tests_l:
            res_dir[el] = []

        rts = "# ToF Data:\n"
        idx = 0
        otp_vdddig = ""
        scr_vdddig = ""
        for cur_idx, r in enumerate(self.reports):
            if isinstance(r, TofTestStatus):
                rts += f"Report {idx}: Test Result: {r.name} ({hex(r.value)})\n"
            else:
                if "".join(chr(x) for x in self.reports[cur_idx:]) != self.end_pattern:
                    if cur_idx == 1:
                        otp_vdddig = f"{int(r):x}"
                        rts += f"OTP_VDDDIG = 0x{otp_vdddig}\n"
                        continue
                    elif cur_idx == 2:
                        qmf_vdddig = f"{int(r):x}"
                        rts += f"QMF_VDDDIG = 0x{qmf_vdddig}\n"
                        continue
                    elif cur_idx == 3:
                        scr_vdddig = f"{int(r):x}"
                        rts += f"SCR_VDDDIG = 0x{scr_vdddig}\n"
                        continue
                    id = f"{tof_tests_l[idx % len(tof_tests_l)]}"
                    res_dir[id].append(r)
                    idx += 1
                else:
                    print("End of ProductionTest Pattern Detected")
                    break

        if ((int(qmf_vdddig, 16) + int(OFFSET_CODE)) > 0x2F) and int(
            scr_vdddig, 16
        ) == 0x2F:
            print("Warning: Verdict code is limited to 0x2F")

        subs = ""
        subs += f"{'voltage':>10s},"
        for test_res in list(res_dir.keys())[1:]:
            test_name = "lcss" if test_res == "24" else "tof"
            test_id = f"{test_name}_{test_res}"
            subs += f"{test_id:>10s},"
        subs += f"{'STATUS':>10s},"
        subs += f"{'VOLTAGE':>10s}"
        rts += subs + "\n"

        subs = ""
        cur_idx = 0
        for vdd_dig in res_dir[tof_tests_l[0]]:
            vdddig_v = self.vdddig_code_to_mv(vdd_dig, int(otp_vdddig, 16))
            str_vdddig = f"0x{vdd_dig:02x}"
            subs += f"{str_vdddig:>10s},"
            status = 0
            for test_id in tof_tests_l[1:]:
                test_res = res_dir[test_id][cur_idx]
                subs += f"{test_res:>10},"
                status += test_res
            result = "OK" if status == 0 else "FAIL"
            subs += f"{result:>10s},"
            subs += f"{vdddig_v:>10.2f}"
            rts += subs + "\n"
            subs = ""
            cur_idx += 1
        return rts[:-1]


class RtcTestOutput:
    """
    This class is encapsulating TEST UCI_SYS_TEST_RTC_NTF
    as described in Qorvo Mobile Factory Test Specification 2.0.pdf dated 2022.10.10 p. 27
    Warning: T, L, V are all coded in the bytestream with size(T)==size(L)=1.
    All values are returned in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.gid = Gid.Qorvo
        self.oid = OidQorvo.TestRtc
        self.payload = payload
        b = Buffer(payload)
        count = b.pop_uint(1)  # Number of reports
        self.reports = []
        for i in range(count):
            report_type = b.pop_uint(1)
            report_size = b.pop_uint(1)
            if report_type == 0x01:  # Status
                self.reports.append(RTCTestResult(b.pop_uint(1)))
            elif report_type == 0x02:  # elapsed time in ms
                self.reports.append(b.pop_uint(2))
            else:
                logger.warning(
                    f'RtcTestOutput: "{report_type}" unknown report type of size {report_size}.'
                )
                b.pop(report_size)
        if b.remaining_size() != 0:
            logger.warning(
                f"RtcTestOutput: {b.remaining_size()} unhandled remaining bytes."
            )

    def __str__(self) -> str:
        rts = "# Test RTC Data:\n"
        for r in self.reports:
            if isinstance(r, RTCTestResult):
                rts = rts + f"        Result:       {r.name} ({hex(r.value)})\n"
            else:
                rts = rts + f"        Elapsed time: {r} ms\n"
        return rts[:-1]


class CwTestOutput:
    def __init__(self, payload: bytes):
        self.gid = Gid.Qorvo
        self.oid = OidQorvo.TestTxCw
        self.payload = payload
        b = Buffer(payload)
        self.status = Status(b.pop_uint(1))
        if b.remaining_size() != 0:
            logger.warning(
                f"RtcTestOutput: {b.remaining_size()} unhandled remaining bytes."
            )

    def __str__(self) -> str:
        rts = f"# Test CW:\n    Status: {self.status.name} ({self.status.value})"
        return rts


class SessionDataTransferStatus:
    """
    This class is encapsulating SESSION_DATA_TRANSFER_STATUS_NTF data
    as described in the 2.0 version of the FIRA Generic Technical Specification 0.9r2 p58.
    All values are returned in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.gid = Gid.Qorvo
        self.oid = OidQorvo.SessionDataXferStatusNtf
        self.payload = payload
        b = Buffer(payload)
        self.session_handle = b.pop_int(
            4
        )  # Session Handle for which the data transfer is requested.
        self.uci_sequence_number = b.pop_int(
            1
        )  # The Sequence Number identifying the UCI Data Message.
        self.status = SessionDataTransferStatusNtf(b.pop_int(1))  # Status code.
        self.tx_count = b.pop_int(
            1
        )  # TX Count indicates the number of times Application Data with
        # the same UCI Sequence Number has been transmitted
        if b.remaining_size() != 0:
            logger.warning(
                f"SessionDataTransferStatus: {b.remaining_size()} unhandled remaining bytes."
            )

    def __str__(self) -> str:
        return f"""# Session Data Transfer Status NTF:
        Session Handle:       {self.session_handle}
        UCI Sequence Number:  {self.uci_sequence_number}
        Status:               {self.status}
        TX Count:             {self.tx_count}
        """


# =============================================================================
# UCI Message Extension
# =============================================================================

# Below is temporary: times to replace all 'raw' codecs with specific-ones.

# Defaults:
for i in OidQorvo:
    uci_codecs[(MT.Command, Gid.Qorvo, i)] = default_codec(i.name)
    uci_codecs[(MT.Response, Gid.Qorvo, i)] = default_codec(i.name)
for i in OidCalibration:
    uci_codecs[(MT.Command, Gid.Calibration, i)] = default_codec(f"{i.name}Calibration")
    uci_codecs[(MT.Response, Gid.Calibration, i)] = default_codec(
        f"{i.name}Calibration"
    )

# Final:
uci_codecs.update(
    {
        (MT.Notif, Gid.Qorvo, OidQorvo.TestDebug): TestDebugData,
        (MT.Notif, Gid.Qorvo, OidQorvo.TestDiag): RangingDiagData,
        (MT.Response, Gid.Qorvo, OidQorvo.TestTxCw): CwTestOutput,
        (MT.Response, Gid.Qorvo, OidQorvo.TestPllLock): default_codec(
            "Start PLL Lock Test", status_only=True
        ),
        (MT.Notif, Gid.Qorvo, OidQorvo.TestPllLock): PllLockTestOutput,
        (MT.Response, Gid.Qorvo, OidQorvo.TestTof): default_codec(
            "Start ToF Test", status_only=True
        ),
        (MT.Notif, Gid.Qorvo, OidQorvo.TestTof): TofTestOutput,
        (MT.Response, Gid.Qorvo, OidQorvo.TestRtc): default_codec(
            "Start RTC Test", status_only=True
        ),
        (MT.Notif, Gid.Qorvo, OidQorvo.TestRtc): RtcTestOutput,
        (
            MT.Notif,
            Gid.Qorvo,
            OidQorvo.SessionDataXferStatusNtf,
        ): SessionDataTransferStatus,
        (MT.Notif, Gid.Ranging, OidRanging.Start): RangingData,
    }
)
