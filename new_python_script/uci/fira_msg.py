# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library is handling FIRA uci data format and conversion
"""

from . import fira_enums
from . import fira_cap
from . import fira_app
import logging

from .fira_enums import *
from .fira_cap import *
from .fira_app import *

from .utils import *

from .core import MT, PBF

__all__ = [
    "DeviceInfo",
    "NotImplementedData",
    "NoData",
    "CommandStatus",
    "TwrTestOutput",
    "RxTestOutput",
    "PeriodicTxTestOutput",
    "PerRxTestOutput",
    "LoopBackTestOutput",
    "UciMessage",
    "SessionStatus",
    "DeviceStatus",
    "uci_codecs",
    "default_codec",
    "MT",
    "MulticastControleeList",
    "UpdateMulticastListResp",
    "Caps",
    "SessionData",
    "TestConfigSetReq",
    "TestConfigSetResp",
    "TestConfigGetReq",
    "TestConfigGetResp",
]

__all__.extend(fira_enums.__all__)
__all__.extend(fira_cap.__all__)
__all__.extend(fira_app.__all__)

logger = logging.getLogger()


# =============================================================================
# Fira NTF Data
# =============================================================================


class NotImplementedData:
    def __init__(self, gid: int, oid: int, payload: bytes):
        self.gid = gid
        self.oid = oid
        self.payload = payload

    def __str__(self) -> str:
        return f'NTF NotImplementedData for (gid={self.gid}, oid={self.oid}: {self.payload.hex(".", 1)}'


class NoData:
    def __init__(self, payload: bytes):
        self.payload = payload
        b = Buffer(payload)
        if b.remaining_size() != 0:
            logger.warning(
                f'NoData: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return ""


class CommandStatus:
    def __init__(self, payload: bytes):
        self.payload = payload
        b = Buffer(payload)
        self.status = Status(b.pop_uint(1))
        if b.remaining_size() != 0:
            logger.warning(
                f'CommandStatus: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"# Status: {self.status.name} ({self.status})"


class DeviceStatus:
    def __init__(self, payload: bytes):
        self.gid = Gid.Core
        self.oid = OidCore.DeviceStatus
        self.payload = payload
        b = Buffer(payload)
        self.state = DeviceState(b.pop_uint(1))
        if b.remaining_size() != 0:
            logger.warning(
                f'DeviceStatus: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"# DeviceStatus state: {str(self.state)}"


class SessionStatus:
    def __init__(self, payload: bytes):
        self.gid = Gid.Session
        self.oid = OidSession.Status
        self.payload = payload
        b = Buffer(payload)
        self.session_id = b.pop_uint(4)
        self.state = SessionState(b.pop_uint(1))
        self.reason = SessionStateChangeReason(b.pop_uint(1))
        if b.remaining_size() != 0:
            logger.warning(
                f'SessionStatus: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"# SessionStatus id: {self.session_id},  state: {str(self.state.name)}, Reason: {str(self.reason.name)}."


class UpdateMulticastListResp:
    """
    This class is encapsulating SESSION_UPDATE_CONTROLLER_MULTICAST_LIST_RSP data
    as described in Fira Specification UCI Generic Specification v2.0.0_0.9r11 p.76
    """

    def __init__(self, payload: bytes):
        self.payload = payload
        self.controlees = []  # a (MacAddress, MulticastControleeStatus) list
        self.count = 0
        try:
            b = Buffer(payload)
            self.status = Status(b.pop_uint(1))
            count = b.pop_uint(1)
            for i in range(count):
                mac = b.pop_uint(2)
                status = MulticastControleeStatus(b.pop_uint(1))
                self.controlees.append([mac, status])
                self.count = self.count + 1
            if b.remaining_size() != 0:
                logger.warning(
                    f'UpdateMulticastListResp: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )
        except ValueError as e:
            logger.warning(f"UpdateMulticastListResp: {e}.")

    def __str__(self) -> str:
        rts = f"""# List of multicast controlee updates:
        status: {self.status.name} ({self.status.value})
        count: {self.count}\n"""
        nl = "\n        "
        for i in range(self.count):
            if i == 0:
                rts += "Updates:\n"
            rts += f"{nl}{hex(self.controlees[i][0])} : {self.controlees[i][1].name} ({hex(self.controlees[i][1].value)})"
        return rts


class MulticastControleeList:
    """
    This class is encapsulating SESSION_UPDATE_CONTROLLER_MULTICAST_LIST_NTF data
    as described in Fira Specification UCI Generic Specification v2.0.0_0.9r11 p.76
    """

    def __init__(self, payload: bytes):
        self.payload = payload
        self.controlees = []  # a (MacAddress, MulticastControleeStatus) list
        b = Buffer(payload)
        self.session_handle = hex(b.pop_uint(4))
        self.count = b.pop_uint(1)

        for i in range(self.count):
            mac = b.pop_uint(2)
            status = MulticastControleeStatus(b.pop_uint(1))
            self.controlees.append([mac, status])
        if b.remaining_size() != 0:
            logger.warning(
                f'MulticastControleeList: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        rts = f"""# List of multicast controlee updates for session {self.session_handle}:
        count: {self.count}\n"""
        nl = "\n        "
        for i in range(self.count):
            if i == 0:
                rts += "Updates:\n"
            rts += f"{nl}{hex(self.controlees[i][0])} : {self.controlees[i][1].name} ({hex(self.controlees[i][1].value)})"
        return rts


class DeviceInfo(ExtendableClass):
    pass


class DeviceInfo_fira:
    """
    This class is encapsulating the CORE_GET_DEVICE_INFO_RSP data
      - as described in Fira UCI Spec p.18.
      - it includes vendor-specific fields.
    """

    def __init__(self, payload: bytes):
        self.payload = payload
        self.buffer = Buffer(payload)
        self.decode()

    def decode(self):
        self.decode_fira()
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f"DeviceInfo: {self.buffer.remaining_size()} unhandled remaining bytes."
            )

    def decode_fira(self):
        self.uci_version_major = "na"
        self.uci_version_minor = "na"
        self.uci_version_maintenance = "na"
        self.mac_version_major = "na"
        self.mac_version_minor = "na"
        self.mac_version_maintenance = "na"
        self.phy_version_major = "na"
        self.phy_version_minor = "na"
        self.phy_version_maintenance = "na"
        self.uci_test_version_major = "na"
        self.uci_test_version_minor = "na"
        self.uci_test_version_maintenance = "na"
        b = self.buffer
        try:
            self.status = Status(b.pop_uint(1))  # Fira Status
            self.uci_version_major = b.pop_uint(1)  # Fira Generic Version 1/2
            mm = b.pop_uint(1)  # Fira Generic Version 2/2
            self.uci_version_minor, self.uci_version_maintenance = mm >> 4, mm & 0xF
            self.mac_version_major = b.pop_uint(1)  # Fira MAC Version 1/2
            mm = b.pop_uint(1)  # Fira MAC Version 2/2
            self.mac_version_minor, self.mac_version_maintenance = mm >> 4, mm & 0xF
            self.phy_version_major = b.pop_uint(1)  # Fira Phy Version 1/2
            mm = b.pop_uint(1)  # Fira Phy Version 2/2
            self.phy_version_minor, self.phy_version_maintenance = mm >> 4, mm & 0xF
            self.uci_test_version_major = b.pop_uint(1)  # Fira Test Version 1/2
            mm = b.pop_uint(1)  # Fira Test Version 2/2
            self.uci_test_version_minor, self.uci_test_version_maintenance = (
                mm >> 4,
                mm & 0xF,
            )
        except ValueError as v:
            logger.warning(v)

    def __str__(self) -> str:
        return f"""# Get Device Info:
        status:              {self.status.name} ({hex(self.status.value)})
        uci version:         {self.uci_version_major}.{self.uci_version_minor}.{self.uci_version_maintenance}
        mac version:         {self.mac_version_major}.{self.mac_version_minor}.{self.mac_version_maintenance}
        phy version:         {self.phy_version_major}.{self.phy_version_minor}.{self.phy_version_maintenance}
        uci test version:    {self.uci_test_version_major}.{self.uci_test_version_minor}.{self.phy_version_minor}"""


DeviceInfo.extend(DeviceInfo_fira)


class SessionData:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.buffer = Buffer(payload)
        self.decode()

    def decode(self):
        self.decode_fira()
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f"SessionData: {self.buffer.remaining_size()} unhandled remaining bytes."
            )

    def decode_fira(self):
        self.status = "na"
        self.session_handle = None
        b = self.buffer
        try:
            self.status = Status(b.pop_uint(1))
            self.session_handle = b.pop_uint(4)
        except ValueError as v:
            logger.warning(v)

    def __str__(self) -> str:
        return f"""# Session Data Info:
            Status: {self.status.name} ({hex(self.status.value)})
            Session handle: {self.session_handle}"""


class Caps:
    """
    This class is encapsulating the CORE_GET_CAPS_RSP data
      - as described in Fira UCI Spec p.25.
      - it includes vendor-specific fields.
    """

    def __init__(self, payload: bytes):
        self.payload = payload
        self.buffer = Buffer(payload)
        self.decode()

    def decode(self):
        self.decode_fira()
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f"GetCaps: {self.buffer.remaining_size()} unhandled remaining bytes."
            )

    def decode_fira(self):
        self.status = "na"
        b = self.buffer
        try:
            self.status = Status(b.pop_uint(1))
            n = b.pop_uint(1)
            self.caps_list = []
            for i in range(n):
                k = int(b.pop(1).hex(), 16)
                l = b.pop_uint(1)
                v = b.pop(l)
                if k in fira_enums.CapsParameters.as_value_list():
                    cap_enum = fira_enums.CapsParameters(k)
                    cap_obj = caps.get(cap_enum, None)
                    if cap_obj:
                        self.caps_list.append(cap_obj(v))
                else:
                    self.caps_list.append(UnsupportedCap(k, v))

        except ValueError as v:
            logger.warning(v)

    def __str__(self) -> str:
        caps_str = "\n".join([str(cap) for cap in self.caps_list if str(cap)])
        return f"""# Get Caps Info:
        status:              {self.status.name} ({hex(self.status.value)})
        Caps:\n\n\n
{caps_str}"""


class TestConfigSetReq:
    """
    This class is encoding/decoding the c payload
    """

    def __init__(self, payload=None, session_handle="na", params=[]):
        self.session_handle = session_handle
        self.params = params
        if isinstance(payload, bytes) or isinstance(payload, bytearray):
            self.from_bytes(payload)

    def from_bytes(self, value: bytes, byteorder="little"):
        self.session_handle = "na"
        self.params = []
        try:
            b = Buffer(value)
            self.session_handle = b.pop_uint(4)
            self.count = b.pop_uint(1)
            for i in range(self.count):
                t = TestParam(b.pop_uint(1))
                l = b.pop_uint(1)
                try:
                    expected_l = TestParam.defs[t]
                except Exception:
                    expected_l = l
                    logger.warning(f"{t.name} length not specified in uqt.")
                if expected_l != l:
                    logger.warning(
                        f"{t.name} not of expected length. Got {l}, expecting {expected_l}.\n Will use {l}"
                    )
                v = b.pop_uint(l)
                self.params.append((t, v))
            if b.remaining_size() != 0:
                logger.warning(
                    f'TestConfigSetReq: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )
        except ValueError as e:
            logger.warning(f"TestConfigSetReq: {e}.")

    def to_bytes(self, byteorder="little") -> bytes:
        payload = (self.session_handle).to_bytes(4, "little")
        payload += (len(self.params)).to_bytes(1, "little")
        for t, v in self.params:
            payload += t.to_bytes(1, "little")
            try:
                l = TestParam.defs[t]
            except Exception:
                raise ValueError(f"{t.name} length is not known.")
            payload += l.to_bytes(1, "little")
            payload += v.to_bytes(l, "little")
        return payload

    def __str__(self) -> str:
        rts = f"""# Set Test Config Request:
        session handle: {self.session_handle} ({hex(self.session_handle)})
        n of parameters: {len(self.params)}"""
        nl = "\n            "
        for p, v in self.params:
            p = f"{nl}{p.name} ({hex(p)})"
            rts += f"{p:<35} = {v} ({hex(v)})"
        return rts


class TestConfigSetResp:
    """
    This class is encoding/decoding the TEST_CONFIG_SET_RSP payload
    """

    def __init__(self, payload: bytes):
        self.status = "na"
        self.params = []
        try:
            b = Buffer(payload)
            self.status = Status(b.pop_uint(1))
            self.count = b.pop_uint(1)
            for i in range(self.count):
                self.params.append((TestParam(b.pop_uint(1)), Status(b.pop_uint(1))))
            if b.remaining_size() != 0:
                logger.warning(
                    f'TestConfigSetResp: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )
        except ValueError as e:
            logger.warning(f"TestConfigSetResp: {e}.")

    def __str__(self) -> str:
        rts = f"""# Set Test Config Response:
        Status: {self.status.name} ({hex(self.status)})
        n of failed parameters: {self.count}\n"""
        if self.count != 0:
            nl = "\n            "
            for p, s in self.params:
                p = f"        {p.name} ({hex(p)})"
                rts += f"{p:<30} : {s.name} ({hex(s)}){nl}"
        return rts


class TestConfigGetReq:
    """
    This class is encoding/decoding the TEST_CONFIG_GET_CMD payload
    """

    def __init__(self, payload=None, session_handle="na", params=[]):
        self.session_handle = session_handle
        self.params = params
        if isinstance(payload, bytes) or isinstance(payload, bytearray):
            self.from_bytes(payload)

    def from_bytes(self, value: bytes, byteorder="little"):
        self.session_handle = "na"
        self.params = []
        try:
            b = Buffer(value)
            self.session_handle = b.pop_uint(4)
            self.count = b.pop_uint(1)
            for i in range(self.count):
                self.params.append(TestParam(b.pop_uint(1)))
            if b.remaining_size() != 0:
                logger.warning(
                    f'TestConfigGetReq: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )
        except ValueError as e:
            logger.warning(f"TestConfigGetReq: {e}.")

    def to_bytes(self, byteorder="little") -> bytes:
        payload = (self.session_handle).to_bytes(4, "little")
        payload += bytes([len(self.params)] + self.params)
        return payload

    def __str__(self) -> str:
        rts = f"""# Get Test Config Request:
        session handle: {self.session_handle} ({hex(self.session_handle)})
        n of parameters: {len(self.params)}"""
        nl = "\n        "
        for p in self.params:
            rts += f"{nl}{p.name} ({hex(p)})"
        return rts


class TestConfigGetResp:
    """
    This class is encoding/decoding the TEST_CONFIG_GET_RSP payload
    """

    def __init__(self, payload: bytes):
        self.status = "na"
        self.params = []
        try:
            b = Buffer(payload)
            self.status = Status(b.pop_uint(1))
            self.count = b.pop_uint(1)
            for i in range(self.count):
                t = TestParam(b.pop_uint(1))
                l = b.pop_uint(1)
                try:
                    expected_l = TestParam.defs[t]
                except Exception:
                    expected_l = l
                    logger.warning(f"{t.name} length not specified in uqt.")
                if expected_l != l:
                    logger.warning(
                        f"{t.name} not of expected length. Got {l}, expecting {expected_l}.\n Will use {l}"
                    )
                v = b.pop_uint(l)
                self.params.append((t, v))
            if b.remaining_size() != 0:
                logger.warning(
                    f'TestConfigGetResp: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )
        except ValueError as e:
            logger.warning(f"TestConfigGetResp: {e}.")

    def __str__(self) -> str:
        rts = f"""# Get Test Config Response:
        status: {self.status.name} ({hex(self.status)})
        n of parameters: {self.count}"""
        nl = "\n            "
        for p, v in self.params:
            p = f"{nl}{p.name} ({hex(p)})"
            rts += f"{p:<35} = {v} ({hex(v)})"
        return rts


# =============================================================================
# UCI Data Packets NTF
# =============================================================================


class SessionDataCredit:
    """
    This class is encapsulatin SESSION_DATA_CREDIT_NTF
    as described in Fira UCI Test Spec p.52
    All values are in 'natural number' format.
    """

    def __init__(self, gid: int, oid: int, payload: bytes):
        self.gid = gid
        self.oid = oid
        self.payload = payload
        b = Buffer(payload)
        self.session = 255
        self.credit = 255
        try:
            self.session = b.pop_uint(4)
            self.credit = b.pop_uint(1)
        except Exception:
            pass
        if b.remaining_size() != 0:
            logger.warning(
                f'SessionDataCredit: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        credit_message = ""
        if self.credit == 0x00:
            credit_message = "Credit is not available"
        elif self.credit == 0x01:
            credit_message = "Credit is available"
        else:
            credit_message = "Unknown credit value"

        return f"""# SessionDataCredit gid:{self.gid}, oid:{self.oid}, Result:
        Session handle: {hex(self.session)}
        {credit_message}:   {hex(self.credit)}
        """


class SessionDataTransfertStatus:
    """
    This class is encapsulatin SESSION_DATA_TRANSFER_STATUS_NTF
    as described in Fira UCI Test Spec p.53
    All values are in 'natural number' format.
    """

    def __init__(self, gid: int, oid: int, payload: bytes):
        self.gid = gid
        self.oid = oid
        self.payload = payload
        b = Buffer(payload)
        self.session = None
        self.data_sequence_number = None
        self.status = None
        self.tx_count = None
        try:
            self.session = b.pop_uint(4)
            self.data_sequence_number = b.pop_uint(2)
            self.status = Status(b.pop_uint(1))
            self.tx_count = b.pop_uint(1)
        except Exception:
            pass
        if b.remaining_size() != 0:
            logger.warning(
                f'SessionDataTransfertStatus: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"""# SessionDataTransfertStatus gid:{self.gid}, oid:{self.oid}, Result:
        Session handle: {hex(self.session)}
        Data Sequence Number : {hex(self.data_sequence_number)}
        Status: {self.status.name} ({hex(self.status.value)})
        Data Sequence Number : {hex(self.tx_count)}
        """


# =============================================================================
# Fira Test NTF Data
# =============================================================================


class PeriodicTxTestOutput:
    def __init__(self, payload: bytes):
        self.gid = Gid.Test
        self.oid = OidTest.PeriodicTx
        self.payload = payload
        b = Buffer(payload)
        self.status = Status(b.pop_uint(1))
        if b.remaining_size() != 0:
            logger.warning(
                f'PeriodicTxTestOutput: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"""# PeriodicTxTestOutput gid:{self.gid}, oid:{self.oid}, Test Result:
        Status: {self.status.name} ({hex(self.status.value)})
        """


class RxTestOutput:
    def __init__(self, payload: bytes):
        self.gid = Gid.Test
        self.oid = OidTest.Rx
        self.payload = payload
        self.buffer = Buffer(payload)
        self.status = Status(self.buffer.pop_uint(1))
        rx_done_ts_int = self.buffer.pop_uint(
            4
        )  # Integer    part of TX timestamp in 1/124.8     us resolution
        rx_done_ts_frac = self.buffer.pop_uint(
            2
        )  # Fractional part of TX timestamp in 1/124.8/512 us resolution
        self.rx_time = (rx_done_ts_int + rx_done_ts_frac / 512) / 124.8  # in us
        self.aoa_tetha = self.buffer.pop_float(
            True, 8, 7
        )  # AoA Azimuth in degrees. zero if AOA_RESULT_REQ==0
        self.aoa_phi = self.buffer.pop_float(
            True, 8, 7
        )  # AoA Elevation in degrees. zero if AOA_RESULT_REQ==0
        self.toa_gap = self.buffer.pop_uint(1)  # ToA gap in ns
        self.phr = self.buffer.pop_uint(2)  # Received PHR
        self.psdu_len = self.buffer.pop_uint(2)  # Length of following PSDU Data
        self.psdu_data = self.buffer.pop(self.psdu_len)  # PSDU Data
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f'RxTestOutput: {self.buffer.remaining_size()} unhandled remaining bytes: {self.buffer.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"""# RxTestOutput gid:{self.gid}, oid:{self.oid}, Test Result:
        Status: {self.status.name} ({hex(self.status.value)})
        Rx timestamp:  {self.rx_time} us
        AoA azimuth:   {self.aoa_tetha} deg
        AoA elevation: {self.aoa_phi} deg
        ToA Gap:       {self.aoa_phi} ns
        PHR:           {self.phr}
        PSDU len:      {self.psdu_len}
        PSDU data:     {self.psdu_data.hex(".", 1)}"""


class PerRxTestOutput:
    """
    This class is encapsulatin RANGE_DATA_NTF data
    as described in Fira UCI Test Specification p.12.
    All values are in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.gid = Gid.Test
        self.oid = OidTest.PerRx
        self.payload = payload
        self.buffer = Buffer(payload)
        self.status = Status(self.buffer.pop_uint(1))
        self.attempts = self.buffer.pop_uint(4)  # No. of RX attempts
        self.acq_detect = self.buffer.pop_uint(4)  # No. of times signal was detected
        self.acq_reject = self.buffer.pop_uint(4)  # No. of times signal was rejected
        self.rx_fail = self.buffer.pop_uint(
            4
        )  # No. of times RX did not go beyond ACQ stage
        self.sync_cir_ready = self.buffer.pop_uint(
            4
        )  # No. of times sync CIR ready event was received
        self.sfd_fail = self.buffer.pop_uint(
            4
        )  # No. of time RX was stuck at either ACQ detect or sync CIR ready
        self.sfd_found = self.buffer.pop_uint(4)  # No. of times SFD was found
        self.phr_dec_error = self.buffer.pop_uint(4)  # No. of times PHR decode failed
        self.phr_bit_error = self.buffer.pop_uint(4)  # No. of times PHR bits in error
        self.psdu_dec_error = self.buffer.pop_uint(
            4
        )  # No. of times payload decode failed
        self.psdu_bit_error = self.buffer.pop_uint(
            4
        )  # No. of times payload bits in error
        self.sts_found = self.buffer.pop_uint(
            4
        )  # No. of times STS detection was successful
        self.eof = self.buffer.pop_uint(
            4
        )  # No. of times end of frame event was triggered
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f'PerRxTestOutput: {self.buffer.remaining_size()} unhandled remaining bytes: {self.buffer.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"""# PER Rx Test Result:
        Status:         {self.status.name} ({hex(self.status.value)})
        ATTEMPTS:       {self.attempts}
        ACQ_DETECT:     {self.acq_detect}
        ACQ_REJECT:     {self.acq_reject}
        RX_FAIL:        {self.rx_fail}
        SYNC_CIR_READY: {self.sync_cir_ready}
        SFD_FAIL:       {self.sfd_fail}
        SFD_FOUND:      {self.sfd_found}
        PHR_DEC_ERROR:  {self.phr_dec_error}
        PHR_BIT_ERROR:  {self.phr_bit_error}
        PSDU_DEC_ERROR: {self.psdu_dec_error}
        PSDU_BIT_ERROR: {self.psdu_bit_error}
        STS_FOUND:      {self.sts_found}
        EOF:            {self.eof}"""


class LoopBackTestOutput:
    """
    This class is encapsulatin TEST_LOOPBACK_NTF data
    as described in Fira UCI Test Specification p.17.
    All values are returned in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.gid = Gid.Test
        self.oid = OidTest.Loopback
        self.payload = payload
        self.buffer = Buffer(payload)
        self.status = Status(self.buffer.pop_uint(1))
        ts_int = self.buffer.pop_uint(
            4
        )  # Integer    part of TX timestamp in 1/124.8       s resolution
        ts_frac = self.buffer.pop_uint(
            2
        )  # Fractional part of TX timestamp in 1/124.8/512   s resolution
        self.tx_time = (ts_int + ts_frac / 512) / 124.8  # in us
        ts_int = self.buffer.pop_uint(
            4
        )  # Integer    part of RX timestamp in 1/124.8       s resolution
        ts_frac = self.buffer.pop_uint(
            2
        )  # Fractional part of RX timestamp in 1/124.8/512   s resolution
        self.rx_time = (ts_int + ts_frac / 512) / 124.8  # in us
        self.aoa_tetha = self.buffer.pop_float(
            True, 8, 7
        )  # AoA Azimuth in degrees. zero if AOA_RESULT_REQ==0
        self.aoa_phi = self.buffer.pop_float(
            True, 8, 7
        )  # AoA Elevation in degrees. zero if AOA_RESULT_REQ==0
        self.phr = self.buffer.pop_uint(2)  # Received PHR
        l = self.buffer.pop_uint(2)  # Length of following PSDU Data
        self.psdu_data = self.buffer.pop(l)  # PSDU Data

        if self.buffer.remaining_size() != 0:
            logger.warning(
                f'LoopBackTestOutput: {self.buffer.remaining_size()} unhandled remaining bytes: {self.buffer.pop(-1).hex(".")}.'
            )

    def __str__(self) -> str:
        return f"""# Loopback Test Result:
        Status:        {self.status.name} ({hex(self.status.value)})
        Tx timestamp:  {self.tx_time} us
        Rx timestamp:  {self.rx_time} us
        AoA azimuth:   {self.aoa_tetha} deg
        AoA elevation: {self.aoa_phi} deg
        PHR:           {self.phr}
        PSDU data:     {self.psdu_data.hex(".", 1)}"""


class TwrTestOutput:
    """
    This class is encapsulatin TEST_SS_TWR_NTF
    as described in Fira UCI Test Spec p.20
    All values are in 'natural number' format.
    """

    def __init__(self, payload: bytes):
        self.gid = Gid.Test
        self.oid = OidTest.SsTwr
        self.payload = payload
        b = Buffer(payload)
        self.status = Status(b.pop_uint(1))
        self.delay = b.pop_uint(4) * 1.0 / 128 / 499.2  # us
        # Initiator Tround time or Responder Treply time
        # expressed in 1/(128 * 499.2Mhz) ticks
        if b.remaining_size() != 0:
            logger.warning(f"TwrTestOutput: {b.size()} unhandled remaining bytes.")

    def __str__(self) -> str:
        return f"""# TWR Test Output:
        Status: {self.status.name} ({hex(self.status.value)})
        delay:  {self.delay} us"""


# =============================================================================
# UCI Message
# =============================================================================


def default_codec(
    name, no_data=False, status_only=False, sid_only=False, payload_only=False
):
    class NoData:
        name = ""

        def __init__(self, payload: bytes):
            self.payload = payload
            b = Buffer(payload)
            if b.remaining_size() != 0:
                logger.warning(
                    f'NoData: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )

        def __str__(self) -> str:
            return f"# {self.name}"

    class CommandStatus:
        name = ""

        def __init__(self, payload: bytes):
            self.payload = payload
            b = Buffer(payload)
            self.status = Status(b.pop_uint(1))
            if b.remaining_size() != 0:
                logger.warning(
                    f'CommandStatus: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )

        def __str__(self) -> str:
            return f"# {self.name}:\n" f"    status: {self.status.name} ({self.status})"

    class CommandSid:
        name = ""

        def __init__(self, payload: bytes):
            self.payload = payload
            b = Buffer(payload)
            self.session_id = b.pop_uint(4)
            self.session_type = SessionType(b.pop_uint(1))
            if b.remaining_size() != 0:
                logger.warning(
                    f'CommandSid: {b.remaining_size()} unhandled remaining bytes: {b.pop(-1).hex(".")}.'
                )

        def __str__(self) -> str:
            return (
                f"# {self.name}:\n"
                f"    Session Id: {hex(self.session_id)}\n"
                f"    Session Type: {hex(self.session_type)}: {self.session_type.name}"
            )

    class CommandPayload:
        name = ""

        def __init__(self, payload: bytes):
            self.payload = payload

        def __str__(self) -> str:
            if len(self.payload) == 0:
                rts = f"# {self.name}"
            else:
                rts = f"# {self.name}:\n    payload: {self.payload.hex('.')}"
            return rts

    class RawPayload:
        name = ""

        def __init__(self, payload: bytes):
            self.payload = payload

        def __str__(self) -> str:
            if len(self.payload) == 0:
                rts = f"# {self.name}"
            else:
                rts = f"# {self.name}:\n    payload: {self.payload.hex('.')}"
            return rts

    if no_data:
        return type(name, (NoData,), dict(name=name))
    elif status_only:
        return type(name, (CommandStatus,), dict(name=name))
    elif sid_only:
        return type(name, (CommandSid,), dict(name=name))
    elif payload_only:
        return type(name, (CommandPayload,), dict(name=name))
    else:
        return type("RawPayload", (RawPayload,), dict(name=name))


class UciMessage:
    """
    This class is encapsulating a full UCI message
      - as described in Fira UCI Specs (UCI Generic & UCI Test Spec)
      - as described in Qorvo specs.
    Warning: PBF.Final is expected
    """

    def __init__(self, payload: bytes):
        b = Buffer(payload)
        b0 = b.pop_uint(1)
        self.mt = MT((b0 & 0b11100000) >> 5)  # Message Type
        self.pbf = PBF((b0 & 0b00010000) >> 4)  # Packet Boundary Flag
        self.gid = b0 & 0b00001111  # Group Identifier
        b1 = b.pop_uint(1)
        self.oid = b1 & 0b111111  # Opcode Identifier
        b.pop_uint(1)  # RFU
        self.l = b.pop_uint(1)  # Payload Length
        self.payload = b.pop(self.l)
        if self.pbf != PBF.Final:
            logger.warning(
                "UciMessage: PBF issue. Full message expected. Decoding will surely fails."
            )
        if b.remaining_size() != 0:
            logger.warning(
                f"UciMessage: Length issue. {b.size()} unhandled remaining bytes. Decoding will surely fails."
            )
        codec = uci_codecs.get((self.mt, self.gid, self.oid), default_codec("Unknown"))
        self.data = codec(self.payload)

    def __str__(self) -> str:
        rts = (
            "---> "
            if self.mt == MT.Command
            else (
                "<--- "
                if self.mt == MT.Response
                else "-!-> " if self.mt == MT.Notif else "??? "
            )
        )
        rts = (
            rts
            + f"{self.mt.name} (gid={hex(self.gid)}, oid={hex(self.oid)}, len={self.l}):\n"
        )
        rts = rts + "    " + str(self.data).replace("\n", "\n    ") + "\n"
        return rts


uci_codecs = {}

# Below is temporary: times to replace all 'raw' codecs with specific-ones.

# Defaults:
for i in OidCore:
    uci_codecs[(MT.Command, Gid.Core, i)] = default_codec(i.name)
    uci_codecs[(MT.Response, Gid.Core, i)] = default_codec(i.name)
for i in OidSession:
    uci_codecs[(MT.Command, Gid.Session, i)] = default_codec(f"session {i.name}")
    uci_codecs[(MT.Response, Gid.Session, i)] = default_codec(f"session {i.name}")
for i in OidTest:
    uci_codecs[(MT.Command, Gid.Test, i)] = default_codec(f"Test {i.name}")
    uci_codecs[(MT.Response, Gid.Test, i)] = default_codec(f"Test {i.name}")
for c in [
    (MT.Response, Gid.Core, OidCore.GenericError),
    (MT.Command, Gid.Core, OidCore.DeviceStatus),
    (MT.Response, Gid.Core, OidCore.DeviceStatus),
    (MT.Command, Gid.Core, OidCore.GenericError),
    (MT.Command, Gid.Session, OidSession.Status),
]:
    uci_codecs.pop(c)


# Final:
uci_codecs.update(
    {
        (MT.Command, Gid.Core, OidCore.Reset): default_codec(
            "Reset", payload_only=True
        ),
        (MT.Response, Gid.Core, OidCore.Reset): default_codec(
            "Reset", status_only=True
        ),
        (MT.Notif, Gid.Session, OidSession.Status): SessionStatus,
        (MT.Notif, Gid.Core, OidCore.DeviceStatus): DeviceStatus,
        (MT.Command, Gid.Core, OidCore.GetDeviceInfo): default_codec(
            "Get Device Info", no_data=True
        ),
        (MT.Response, Gid.Core, OidCore.GetDeviceInfo): DeviceInfo,
        (MT.Command, Gid.Core, OidCore.GetCaps): default_codec(
            "Get Caps", no_data=True
        ),
        (MT.Response, Gid.Core, OidCore.GetCaps): Caps,
        (MT.Command, Gid.Ranging, OidRanging.GetCount): default_codec(
            "Get Ranging Count", sid_only=True
        ),
        # (MT.Response,Gid.Ranging, OidRanging.GetCount)            : todo
        (MT.Command, Gid.Core, OidCore.GetTime): default_codec(
            "Get Time", no_data=True
        ),
        # (MT.Response,Gid.Core,    OidCore.GetTime):
        (MT.Command, Gid.Session, OidSession.Init): default_codec(
            "Session Init", sid_only=True
        ),
        (MT.Response, Gid.Session, OidSession.Init): SessionData,
        (MT.Command, Gid.Session, OidSession.Deinit): default_codec(
            "Session De-Init", sid_only=True
        ),
        (MT.Response, Gid.Session, OidSession.Deinit): default_codec(
            "Session De-Init", status_only=True
        ),
        (MT.Command, Gid.Session, OidSession.GetState): default_codec(
            "Session Get State", sid_only=True
        ),
        # (MT.Response, Gid.Session, OidSession.GetState)             todo
        (MT.Command, Gid.Ranging, OidRanging.Start): default_codec(
            "Ranging Start", sid_only=True
        ),
        (MT.Response, Gid.Ranging, OidRanging.Start): default_codec(
            "Ranging Start", status_only=True
        ),
        (MT.Command, Gid.Ranging, OidRanging.Stop): default_codec(
            "Ranging Stop", sid_only=True
        ),
        (MT.Response, Gid.Ranging, OidRanging.Stop): default_codec(
            "Ranging Stop", status_only=True
        ),
        # (MT.Command, Gid.Session, OidSession.UpdateMulticastList) : todo
        (
            MT.Response,
            Gid.Session,
            OidSession.UpdateMulticastList,
        ): UpdateMulticastListResp,
        (MT.Notif, Gid.Session, OidSession.UpdateMulticastList): MulticastControleeList,
        # Gid.Session, OidSession.SetAnchorRangingRounds: todo
        # Gid.Session, OidSession.SetTagActivity: todo
        (MT.Command, Gid.Test, OidTest.ConfigSet): TestConfigSetReq,
        (MT.Response, Gid.Test, OidTest.ConfigSet): TestConfigSetResp,
        (MT.Command, Gid.Test, OidTest.ConfigGet): TestConfigGetReq,
        (MT.Response, Gid.Test, OidTest.ConfigGet): TestConfigGetResp,
        (MT.Command, Gid.Test, OidTest.PeriodicTx): default_codec(
            "Start Periodic Tx Test", no_data=True
        ),
        (MT.Response, Gid.Test, OidTest.PeriodicTx): default_codec(
            "Start Periodic Tx Test", status_only=True
        ),
        (MT.Notif, Gid.Test, OidTest.PeriodicTx): PeriodicTxTestOutput,
        (MT.Command, Gid.Test, OidTest.PerRx): default_codec(
            "Start Rx PER Test", no_data=True
        ),
        (MT.Response, Gid.Test, OidTest.PerRx): default_codec(
            "Start RX PER Test", status_only=True
        ),
        (MT.Notif, Gid.Test, OidTest.PerRx): PerRxTestOutput,
        (MT.Command, Gid.Test, OidTest.Rx): default_codec(
            "Start Rx Test", no_data=True
        ),
        (MT.Response, Gid.Test, OidTest.Rx): default_codec(
            "Start Rx Test", status_only=True
        ),
        (MT.Notif, Gid.Test, OidTest.Rx): RxTestOutput,
        (MT.Command, Gid.Test, OidTest.Loopback): default_codec(
            "Start Loopback Test", no_data=True
        ),
        (MT.Response, Gid.Test, OidTest.Loopback): default_codec(
            "Start Loopback Test", status_only=True
        ),
        (MT.Notif, Gid.Test, OidTest.Loopback): LoopBackTestOutput,
        (MT.Command, Gid.Test, OidTest.StopSession): default_codec(
            "Test Stop Sesssion", no_data=True
        ),
        (MT.Response, Gid.Test, OidTest.StopSession): default_codec(
            "Test Stop Session", status_only=True
        ),
        (MT.Command, Gid.Test, OidTest.SsTwr): default_codec(
            "Start SS Twr", no_data=True
        ),
        (MT.Response, Gid.Test, OidTest.SsTwr): default_codec(
            "Start SS Twr", status_only=True
        ),
        (MT.Notif, Gid.Test, OidTest.SsTwr): TwrTestOutput,
        (MT.Notif, Gid.Ranging, OidRanging.DataCredit): SessionDataCredit,
        (
            MT.Notif,
            Gid.Ranging,
            OidRanging.DataTransferStatus,
        ): SessionDataTransfertStatus,
    }
)
