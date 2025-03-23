# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library contains the Qorvo vendor UCI customization.
"""

from . import qorvo_cal
from . import qorvo_msg

import enum
import re
import struct

from colorama import init
import logging

from . import core
from . import fira
from .fira import *
from .utils import *
from .qorvo_cal import *
from .qorvo_app import *
from .qorvo_msg import *

__all__ = []
__all__.extend(qorvo_cal.__all__)
__all__.extend(qorvo_msg.__all__)

init()
logger = logging.getLogger()

# =============================================================================
# Additional Core Enums
# =============================================================================


class TestRxNotif(enum.IntEnum):
    TxTsInt = 0x00
    TxTsFrac = 0x1
    AoaAzimuth = 0x02
    AoaElevation = 0x03
    ToaGap = 0x4
    Phr = 0x05
    PsduLength = 0x06
    Psdu = 0x07


TestRxNotif.defs = [
    (TestRxNotif.TxTsInt, 4),
    (TestRxNotif.TxTsFrac, 2),
    (TestRxNotif.AoaAzimuth, 2),
    (TestRxNotif.AoaElevation, 2),
    (TestRxNotif.ToaGap, 1),
    (TestRxNotif.Phr, 2),
    (TestRxNotif.PsduLength, 2),
    (TestRxNotif.Psdu, 0),
]


class TestPerRxNotif(enum.IntEnum):
    Attempts = 0x00
    AcqDetect = 0x1
    AcqReject = 0x2
    Rxfail = 0x3
    SyncCirReady = 0x04
    SfdFail = 0x05
    SfdFound = 0x06
    PhrDecError = 0x07
    PhrBitError = 0x08
    PsduDecError = 0x0A
    PsduBitError = 0x0B
    StsFound = 0x0C
    Eof = 0x0D


TestPerRxNotif.defs = [
    (TestPerRxNotif.Attempts, 4),
    (TestPerRxNotif.AcqDetect, 4),
    (TestPerRxNotif.AcqReject, 4),
    (TestPerRxNotif.Rxfail, 4),
    (TestPerRxNotif.SyncCirReady, 4),
    (TestPerRxNotif.SfdFail, 4),
    (TestPerRxNotif.SfdFound, 4),
    (TestPerRxNotif.PhrDecError, 4),
    (TestPerRxNotif.PhrBitError, 4),
    (TestPerRxNotif.PsduDecError, 4),
    (TestPerRxNotif.PsduBitError, 4),
    (TestPerRxNotif.StsFound, 4),
    (TestPerRxNotif.Eof, 4),
]


class TestLoopbackNotif(enum.IntEnum):
    TxTsInt = 0x00
    TxTsFrac = 0x1
    RxTsInt = 0x2
    RxTsFrac = 0x3
    AoaAzimuth = 0x04
    AoaElevation = 0x05
    Phr = 0x06
    PsduLength = 0x07
    Psdu = 0x08


TestLoopbackNotif.defs = [
    (TestLoopbackNotif.TxTsInt, 4),
    (TestLoopbackNotif.TxTsFrac, 2),
    (TestLoopbackNotif.RxTsInt, 4),
    (TestLoopbackNotif.RxTsFrac, 2),
    (TestLoopbackNotif.AoaAzimuth, 2),
    (TestLoopbackNotif.AoaElevation, 2),
    (TestLoopbackNotif.Phr, 2),
    (TestLoopbackNotif.PsduLength, 2),
    (TestLoopbackNotif.Psdu, 0),
]


class TestDebugNotif(enum.IntEnum):
    PDoAazimuth = 0x00
    PDoAelevation = 0x1
    RSSI = 0x2
    AoAazimuth = 0x3
    AoAelevation = 0x4


TestDebugNotif.defs = [
    (TestDebugNotif.PDoAazimuth, 2),
    (TestDebugNotif.PDoAelevation, 2),
    (TestDebugNotif.RSSI, 1),
    (TestDebugNotif.AoAazimuth, 2),
    (TestDebugNotif.AoAelevation, 2),
]


class TestTxCwSwitch(enum.IntEnum):
    StartCwTx = 1
    StopCwTx = 0


class TestDsTwr(enum.IntEnum):
    DeviceFunction = 0x00
    PsduData = 0x1
    RxAntenna = 0x2
    TxAntenna = 0x3


TestDsTwr.defs = [
    (TestDsTwr.DeviceFunction, 1),
    (TestDsTwr.PsduData, 1),
    (TestDsTwr.RxAntenna, 1),
    (TestDsTwr.RxAntenna, 1),
]

# =============================================================================
# Configuration Data
# =============================================================================


class Config(DynIntEnum):
    ChannelNumber = 0xA0
    Traces = 0xA8
    PmMinInactivityS4 = 0xA9


fira.Config.extend(Config)

fira.Config.defs.extend(
    [
        (Config.ChannelNumber, 1),
        (Config.Traces, 4),
        (Config.PmMinInactivityS4, 4),
    ]
)

fira.config_params.update(
    {
        # Enum Value,               parameter type, Read Only, description)
        Config.ChannelNumber: (Int8, 0, "get/set current used channel. 5 or 9."),
        Config.Traces: (
            Int32,
            0,
            "bitfield to enable traces: 1 mcps, 2 fira, 4 lld, 8 lldd, x10 lldc, x20 pctt, x40 radar, x80 ccc.",
        ),
        Config.PmMinInactivityS4: (
            Int32,
            0,
            "get/set minimum inactivity time prior triggering a S4. in ms.",
        ),
    }
)

# =============================================================================
# Helpers
# =============================================================================


def unpack_t_from_bytes(defs, payload):
    res = []
    # n = len(defs)
    p = 0

    for t, length in defs:
        # Special case for undefined PSDU data size,
        # take all remaining data
        if length == 0:
            length = len(payload[p:])

        if length <= 4:
            v = hex((int).from_bytes(payload[p : p + length], "little"))
        else:
            v = []
            for b in range(length):
                v.append(hex((int).from_bytes(payload[p + b : p + b + 1], "little")))
        res.append((t, length, v))
        p += length

    return res


def get_key_value_size(defs, key_name):
    for t, l, p in defs:
        if re.match(p, key_name):
            return l

    return None


def klvs_from_bytes(defs, payload):
    res = []
    n = (int).from_bytes(payload[0:2], "little")
    p = 2

    for k in range(n):
        kn_l = (int).from_bytes(payload[p : p + 1], "little")
        p += 1

        if kn_l == 0:
            continue

        key_name = struct.unpack("{}s".format(kn_l), payload[p : p + kn_l])[0]
        p += kn_l

        k_s = (int).from_bytes(payload[p : p + 1], "little")
        p += 1

        kv_l = (int).from_bytes(payload[p : p + 1], "little")
        p += 1

        if kv_l <= 4:
            kv = (int).from_bytes(payload[p : p + kv_l], "little")
        else:
            kv = payload[p : p + kv_l]
        p += kv_l

        res.append((key_name, Status(k_s), kv_l, kv))

    return res


def tv_to_bytes(defs, tv):
    payload = b""
    for t, v in tv:
        length = core.get_length(defs, t)
        if isinstance(v, list):
            for s in v:
                payload += (s).to_bytes(length, "little")
        else:
            payload += (v).to_bytes(length, "little")

    return payload


def klv_to_bytes(key, value_len, value):
    key_len = len(key)
    payload = (0x01).to_bytes(1, "little")
    payload += (key_len).to_bytes(1, "little")
    payload += struct.pack("{}s".format(key_len), key.encode("UTF-8"))
    payload += (value_len).to_bytes(1, "little")
    payload += (value).to_bytes(value_len, "little")

    return payload


def kv_to_bytes(defs, params):
    n = len(params)
    payload = (n).to_bytes(2, "little")

    for k, v in params:
        kn_l = len(k)
        payload += (kn_l).to_bytes(1, "little")

        payload += struct.pack("{}s".format(kn_l), k.encode("UTF-8"))

        kv_l = get_key_value_size(defs, k)

        if kv_l is None:
            if isinstance(v, bytes):
                kv_l = len(v)
            else:
                raise ValueError(f'"{k}": unknown calibration key')
        payload += (kv_l).to_bytes(1, "little")
        if not isinstance(v, bytes):
            try:
                v = (v).to_bytes(kv_l, "little")
            except OverflowError:
                raise ValueError(f'"{k}" value "{v!r}": expecting {kv_l} bytes.')
        if kv_l != len(v):
            raise ValueError(f'"{k}" value "{v!r}": expecting {kv_l} bytes.')
        payload += v

    return payload


def k_to_bytes(defs, params):
    n = len(params)
    payload = (n).to_bytes(2, "little")
    if n != 0:
        for k in params:
            kn_l = len(k)
            payload += (kn_l).to_bytes(1, "little")

            payload += struct.pack("{}s".format(kn_l), k.encode("UTF-8"))
    return payload


# =============================================================================
# Client
# =============================================================================


class Client_extension:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_tx_cw(self, switch_op):
        payload = self.command(
            Gid.Qorvo, OidQorvo.TestTxCw, switch_op.to_bytes(1, "little")
        )
        return Status((int).from_bytes(payload[0:1], "little"))

    def test_pll_lock(self, operation, timeout):
        if operation == 255:
            payload = self.command(Gid.Qorvo, OidQorvo.TestPllLock, [])
        else:
            payload = operation.to_bytes(1, "little")
            payload += timeout.to_bytes(1, "little")
            payload = self.command(Gid.Qorvo, OidQorvo.TestPllLock, payload)
        return Status(payload[0])

    def test_tof(self, start_voltage, end_voltage, code_offset, timeout_delay):
        payload = start_voltage.to_bytes(1, "little")
        payload += end_voltage.to_bytes(1, "little")
        payload += code_offset.to_bytes(1, "little")
        payload = self.command(Gid.Qorvo, OidQorvo.TestTof, payload, timeout_delay)
        return Status((int).from_bytes(payload[0:1], "little"))

    def test_rtc(self, time_out_ms):
        payload = self.command(
            Gid.Qorvo, OidQorvo.TestRtc, time_out_ms.to_bytes(2, "little")
        )
        return Status((int).from_bytes(payload[0:1], "little"))

    def test_mode_calibrations_set(self, params):
        payload = kv_to_bytes(CalibrationParams.defs, params)
        payload = self.command(Gid.Calibration, OidCalibration.Set, payload)
        return (
            Status((int).from_bytes(payload[0:1], "little")),
            struct.unpack("b{}s".format(payload[1]), payload[1:]),
        )

    def test_mode_calibrations_set_single_without_verif(self, key, value_len, value):
        payload = klv_to_bytes(key, value_len, value)
        payload = self.command(Gid.Calibration, OidCalibration.Set, payload)
        status = Status((int).from_bytes(payload[0:1], "little"))
        if status != Status.Ok:
            return status
        else:
            return (
                Status((int).from_bytes(payload[0:1], "little")),
                struct.unpack("b{}s".format(payload[1]), payload[1:]),
            )

    def test_mode_calibrations_get(self, params):
        """deprecated"""
        payload = k_to_bytes(CalibrationParams.defs, params)
        payload = self.command(Gid.Calibration, OidCalibration.Get, payload)
        return (
            Status((int).from_bytes(payload[0:1], "little")),
            (int).from_bytes(payload[1:3], "little"),
            klvs_from_bytes(CalibrationParams.defs, payload[1:]),
        )

    def get_cal(self, params):
        payload = (len(params)).to_bytes(2, "little")
        for k in params:
            payload += len(k).to_bytes(1, "little")
            payload += k.encode("UTF-8")
        get_cal = GetCalibration(
            self.command(Gid.Calibration, OidCalibration.Get, payload)
        )
        return get_cal.status, get_cal.n, get_cal.rtv


Client.extend(Client_extension)


class GetCalibration:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.buffer = Buffer(payload)
        self.decode()

    def decode(self):
        self.decode_fira()
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f"GetCal: {self.buffer.remaining_size()} unhandled remaining bytes."
            )

    def decode_fira(self):
        self.status = "na"
        self.n = "na"
        self.rtv = []
        b = self.buffer
        try:
            self.status = Status(b.pop_uint(1))
            self.n = b.pop_uint(2)
            self.rtv = []
            for k in range(self.n):
                l = b.pop_uint(1)
                if l == 0:
                    continue
                k = b.pop(l).decode()
                s = Status(b.pop_uint(1))
                l = b.pop_uint(1)
                v = b.pop(l)
                self.rtv.append((k, s, l, v))

        except ValueError as v:
            logger.warning(v)

    def __str__(self) -> str:
        is_alone = self.n == 1
        calibrations = []
        for k, s, l, v in self.rtv:
            self.status = s
            v_suffix = ""
            if k not in cal_params.keys():
                v_suffix = f'(and "{k}" unknown to uqt.)'
            if s != Status.Ok:
                v = f"{s.name} ({s}) {v_suffix}"
            elif k not in cal_params.keys():
                pass
            else:
                v = cal_params[k]().from_bytes(v)
            if is_alone:
                calibrations.append(v)
            else:
                calibrations.append(f"{k:<40} : {v}")

        calibrations_str = "\n".join(calibrations)
        return f"""# Get Calibration Info:
        status:              {self.status.name} ({hex(self.status.value)})
        Calibration:\n\n\n
{calibrations_str}
"""


uci_codecs.update(
    {
        (MT.Response, Gid.Calibration, OidCalibration.Get): GetCalibration,
    }
)

# =============================================================================
# UCI Notification Handler
# =============================================================================

# Below: time for UWBMQA-3594 ... should go to Fira
notification_default_handlers.update(
    {
        (Gid.Ranging, OidRanging.Start): lambda x: print(RangingData(x)),
        (Gid.Test, OidTest.Loopback): lambda x: print(LoopBackTestOutput(x)),
        (Gid.Test, OidTest.PeriodicTx): lambda x: print(PeriodicTxTestOutput(x)),
        (Gid.Test, OidTest.SsTwr): lambda x: print(TwrTestOutput(x)),
        (Gid.Test, OidTest.Rx): lambda x: print(RxTestOutput(x)),
        (Gid.Test, OidTest.PerRx): lambda x: print(PerRxTestOutput(x)),
    }
)

notification_default_handlers.update(
    {
        (Gid.Qorvo, OidQorvo.TestDiag): lambda x: print(RangingDiagData(x)),
        (Gid.Qorvo, OidQorvo.SessionDataXferStatusNtf): lambda x: print(
            SessionDataTransferStatus(x)
        ),
        (Gid.Qorvo, OidQorvo.TestDebug): lambda x: print(TestDebugData(x)),
        (Gid.Qorvo, OidQorvo.TestPllLock): lambda x: print(PllLockTestOutput(x)),
        (Gid.Qorvo, OidQorvo.TestRtc): lambda x: print(RtcTestOutput(x)),
        (Gid.Qorvo, OidQorvo.TestTof): lambda x: print(TofTestOutput(x)),
    }
)
