# Copyright (c) 2021 Qorvo US, Inc.
import enum
import struct
import typing

from colorama import Fore, Style, init

import uci.core as core

init()


def _decode_q_format(number_integer_bits: int, number_frac_bits: int,
                     value: bytes, signed: bool = True) -> float:
    if signed:
        SIGN_POSITION = number_integer_bits + number_frac_bits - 1
        INTEGER_MASK = 2 ** (number_integer_bits - 1) - 1
        INTEGER_POSITION = number_frac_bits
        SIGN_VALUE = 2**(number_integer_bits - 1)
        FRACTIONAL_MASK = 2 ** (number_frac_bits) - 1
        FRACTIONAL_POSITION = 0

        encoded_value = int.from_bytes(value, 'little')
        # check sign
        sign = bool((encoded_value & (1 << SIGN_POSITION)))
        # get integer part using a mask
        integer_part = (encoded_value &
                        (INTEGER_MASK << INTEGER_POSITION)) >> INTEGER_POSITION
        # substract the value of the sign bit
        signed_value = integer_part if not sign else integer_part - SIGN_VALUE
        # extract fractional part
        fractional_part = (encoded_value &
                           (FRACTIONAL_MASK << FRACTIONAL_POSITION)
                           ) >> FRACTIONAL_POSITION
        # normalize fractional part
        fractional_value = fractional_part / 2.0**INTEGER_POSITION
        # return whole value
        return signed_value + fractional_value
    else:
        INTEGER_MASK = 2 ** (number_integer_bits) - 1
        INTEGER_POSITION = number_frac_bits
        FRACTIONAL_MASK = 2 ** (number_frac_bits) - 1
        FRACTIONAL_POSITION = 0

        encoded_value = int.from_bytes(value, 'little')
        # get integer part using a mask
        integer_part = (encoded_value &
                        (INTEGER_MASK << INTEGER_POSITION)) >> INTEGER_POSITION
        # extract fractional part
        fractional_part = (encoded_value &
                           (FRACTIONAL_MASK << FRACTIONAL_POSITION)
                           ) >> FRACTIONAL_POSITION
        # normalize fractional part
        fractional_value = fractional_part / 2.0**INTEGER_POSITION
        # return whole value
        return integer_part + fractional_value


def byte_slice() -> typing.Generator:
    """
    Returns a gemerator for slices used to select sublists at a variable step
    """
    position = 0
    step = 0
    while True:
        new_step = yield slice(position, position + step)
        position = position + step
        if new_step is not None:
            step = new_step


class IndexHandler:
    """Handler used to sequence read from lists"""
    def __init__(self):
        self.reset()

    def reset(self):
        """Resets index to 0"""
        self.gen = byte_slice()
        next(self.gen)

    def next(self, nr_of_bytes: int) -> slice:
        """
        Return a slice spanning from the current index to index + nr_of_bytes
        """
        return self.gen.send(nr_of_bytes)


class PayloadHandler:
    """Handler used to sequence read from a bytes type structure"""
    def __init__(self, payload: bytes, endianess='little'):
        self.select_bytes = IndexHandler()
        self.payload = payload
        self.endianess = endianess

    def get_next_field(self, field_length: int) -> int:
        """
        Int dencode a bitfield of length field_length starting from the
        current index
        """
        return int.from_bytes(self.payload[
            self.select_bytes.next(field_length)], self.endianess)

    def get_next_string(self, string_size: int) -> str:
        """
        UTF-8 decode a bitfield of length string_size starting from the current
        index
        """
        return self.payload[self.select_bytes.next(string_size)]\
            .decode('utf-8')

    def get_bytes(self, field_length: int) -> bytes:
        """
        Return a bitfield of length field_length starting from the current
        index
        """
        return self.payload[self.select_bytes.next(field_length)]

# TODO: GIds and OIDs are missing (are they needed outside?)


class Gid(enum.IntEnum):
    UciCore = 0x00
    UwbSessionConfig = 0x01
    UwbRangingSessionControl = 0x02
    Se = 0x09  # Proprietary Group
    TestDbgNtf = 0x0b  # Proprietary Group
    UwbCalibration = 0x0c  # Proprietary Group
    Test = 0x0d
    TestExtra = 0x0e  # Proprietary Group
    UwbConfigManager = 0x0f


class Status(enum.IntEnum):
    Ok = 0x0,
    Rejected = 0x01,
    Failed = 0x02,
    SyntaxErr = 0x03,
    InvalidParam = 0x04,
    InvalidRange = 0x05,
    InvalidMessageSize = 0x06,
    UnknownGid = 0x07,
    UnknownOid = 0x08,
    ReadOnly = 0x09,
    CommandRetry = 0x0a,
    ErrorSessionNotExist = 0x11,
    ErrorSessionDuplicate = 0x12,
    ErrorSessionActive = 0x13,
    ErrorMaxSessionsExceeded = 0x14,
    ErrorSessionNotConfigured = 0x15,
    ErrorActiveSessionsOngoing = 0x16,
    ErrorMulticastListFull = 0x17,
    ErrorAddressNotFound = 0x18,
    ErrorAddressAlreadyPresent = 0x19,
    RangingTxFailed = 0x20,
    RangingRxTimeout = 0x21,
    RangingRxPhyDecFailed = 0x22,
    RangingRxPhyToaFailed = 0x23,
    RangingRxPhyStsFailed = 0x24,
    RangingRxMacDecFailed = 0x25,
    RangingRxMacIeDecFailed = 0x26,
    RangingRxMacIeMissing = 0x27,


class Device(enum.IntEnum):
    State = 0x0
    LowPowerMode = 0x1
    ChannelNumber = 0xA0


Device.defs = [
    (Device.State, 1),
    (Device.LowPowerMode, 1),
    (Device.ChannelNumber, 1),
]


class DeviceState(enum.IntEnum):
    Ready = 0x01,
    Active = 0x02,
    Error = 0xff,


class App(enum.IntEnum):
    DeviceType = 0x00,
    RangingRoundUsage = 0x01,
    StsConfig = 0x02,
    MultiNodeMode = 0x03,
    ChannelNumber = 0x04,
    NumberOfControlees = 0x05,
    DeviceMacAddress = 0x06,
    DstMacAddress = 0x07,
    SlotDuration = 0x08,
    RangingInterval = 0x09,
    StsIndex = 0x0a,
    MacFcsType = 0x0b,
    RangingRoundControl = 0x0c,
    AoaResultReq = 0x0d,
    RangeDataNtfConfig = 0x0e,
    RangeDataNtfProximityNear = 0x0f,
    RangeDataNtfProximityFar = 0x10,
    DeviceRole = 0x11,
    RframeConfig = 0x12,
    PreambleCodeIndex = 0x14,
    SfdId = 0x15,
    PsduDataRate = 0x16,
    PreambleDuration = 0x17,
    RangingTimeStruct = 0x1a,
    SlotsPerRr = 0x1b,
    TxAdaptivePayloadPower = 0x1c,
    ResponderSlotIndex = 0x1e,
    PrfMode = 0x1f,
    ScheduleMode = 0x22,
    KeyRotation = 0x23,
    KeyRotationRate = 0x24,
    SessionPriority = 0x25,
    MacAddressMode = 0x26,
    VendorId = 0x27,
    StaticStsIv = 0x28,
    NumberOfStsSegments = 0x29,
    MaxRrRetry = 0x2a,
    UwbInitiationTime = 0x2b,
    HoppingMode = 0x2c,
    BlockStrideLength = 0x2d,
    ResultReportConfig = 0x2e,
    InBandTerminationAttemptCount = 0x2f,
    SubSessionId = 0x30,
    BprfPhrDataRate = 0x31
    MaxNumberOfMeasurements = 0x32,
    StsLength = 0x35,
    RssiReporting = 0x36,
    RxAntennaSelection = 0xe6,
    TxAntennaSelection = 0xe7,
    EnableDiagnostics = 0xe8,
    DiagsFrameReportsFields = 0xe9


App.defs = [
    (App.DeviceType, 1),
    (App.RangingRoundUsage, 1),
    (App.StsConfig, 1),
    (App.MultiNodeMode, 1),
    (App.ChannelNumber, 1),
    (App.NumberOfControlees, 1),
    (App.DeviceMacAddress, 2),  # or 8?
    (App.DstMacAddress, 2),  # or 8
    (App.SlotDuration, 2),
    (App.RangingInterval, 4),
    (App.StsIndex, 4),
    (App.MacFcsType, 1),
    (App.RangingRoundControl, 1),
    (App.AoaResultReq, 1),
    (App.RangeDataNtfConfig, 1),
    (App.RangeDataNtfProximityNear, 2),
    (App.RangeDataNtfProximityFar, 2),
    (App.DeviceRole, 1),
    (App.RframeConfig, 1),
    (App.PreambleCodeIndex, 1),
    (App.SfdId, 1),
    (App.PsduDataRate, 1),
    (App.PreambleDuration, 1),
    (App.RangingTimeStruct, 1),
    (App.SlotsPerRr, 1),
    (App.TxAdaptivePayloadPower, 1),
    (App.ResponderSlotIndex, 1),
    (App.PrfMode, 1),
    (App.ScheduleMode, 1),
    (App.KeyRotation, 1),
    (App.KeyRotationRate, 1),
    (App.SessionPriority, 1),
    (App.MacAddressMode, 1),
    (App.VendorId, 2),
    (App.StaticStsIv, 6),
    (App.NumberOfStsSegments, 1),
    (App.MaxRrRetry, 2),
    (App.UwbInitiationTime, 4),
    (App.HoppingMode, 1),
    (App.BlockStrideLength, 1),
    (App.ResultReportConfig, 1),
    (App.InBandTerminationAttemptCount, 1),
    (App.SubSessionId, 4),
    (App.BprfPhrDataRate, 1),
    (App.MaxNumberOfMeasurements, 2),
    (App.StsLength, 1),
    (App.RssiReporting, 1),
    (App.RxAntennaSelection, 1),
    (App.TxAntennaSelection, 1),
    (App.EnableDiagnostics, 1),
    (App.DiagsFrameReportsFields, 1)
]


class TestParam(enum.IntEnum):
    NumPackets = 0x00,
    TGap = 0x1,
    TStart = 0x2,
    TWin = 0x3,
    RandomizePsdu = 0x04,
    PhrRangingBit = 0x05,
    RMarkerTxStart = 0x06,
    RMarkerRxStart = 0x07,
    StsIndexAutoIncr = 0x08,


TestParam.defs = [
    (TestParam.NumPackets, 4),
    (TestParam.TGap, 4),
    (TestParam.TStart, 4),
    (TestParam.TWin, 4),
    (TestParam.RandomizePsdu, 1),
    (TestParam.PhrRangingBit, 1),
    (TestParam.RMarkerTxStart, 4),
    (TestParam.RMarkerRxStart, 4),
    (TestParam.StsIndexAutoIncr, 1),
]


class State(enum.IntEnum):
    Init = 0x0,
    DeInit = 0x1,
    Active = 0x2,
    Idle = 0x3,


class Reason(enum.IntEnum):
    StateChangeWithSessionManagementCommands = 0x0,
    MaxRangingRoundRetryCountReached = 0x1,
    ErrorSlotLengthNotSupported = 0x20,
    ErrorInsufficientSlotsPerRR = 0x21,
    ErrorMacAddressModeNotSupported = 0x22,
    ErrorInvalidRangingInterval = 0x23,
    ErrorInvalidStsConfig = 0x24,
    ErrorInvalidRFrameConfig = 0x25,


class CMD:
    """Interface for command"""

    def encode(self):
        raise NotImplementedError

    def send(self, client: core.Client) -> bytes:
        return client.command(self.GID, self.OID, self.encode())


class NTF:
    """Interface for notification"""
    pass


class RSP:
    """Interface for responce"""

    def __init__(self):
        raise NotImplementedError


class RANGE_START_CMD(CMD):
    """
    Starts range session
    """
    GID = Gid.UwbRangingSessionControl
    OID = 0x0

    def __init__(self, sid: int):
        self.payload = sid.to_bytes(4, 'little')

    def encode(self) -> bytes:
        return self.payload


class RANGE_START_RSP(RSP):
    """
    Responds with the proper status indicating
    the range session has been started successfully
    """
    EXPECTED_PAYLOAD_LENGTH = 1

    def __init__(self, payload: bytes):
        if len(payload) != self.EXPECTED_PAYLOAD_LENGTH:
            raise OverflowError('Payload size expected to be exactly '
                                f'{self.EXPECTED_PAYLOAD_LENGTH} bytes,'
                                f' found {len(payload)}')
        self.Status = Status(payload[0])

    def __str__(self) -> str:
        return f'<{type(self).__name__}: ' +\
            f'Status : {self.Status.name} ({hex(self.Status.value)})>'

    def __repr__(self) -> str:
        return self.__str__()


class RANGE_STOP_CMD(CMD):
    """
    Stops the ongoing range session
    """
    GID = Gid.UwbRangingSessionControl
    OID = 0x1

    def __init__(self, sid: int):
        self.payload = sid.to_bytes(4, 'little')

    def encode(self) -> bytes:
        return self.payload


class RANGE_STOP_RSP(RSP):
    """
    Responds with the proper status indicating the
    range session has been stopped successfully
    """
    EXPECTED_PAYLOAD_LENGTH = 1

    def __init__(self, payload: bytes):
        if len(payload) != self.EXPECTED_PAYLOAD_LENGTH:
            raise OverflowError('Payload size expected to be exactly '
                                f'{self.EXPECTED_PAYLOAD_LENGTH} bytes,'
                                f' found {len(payload)}')
        self.Status = Status(payload[0])

    def __str__(self) -> str:
        return f'<{type(self).__name__}: ' + \
               f'Status : {self.Status.name} ({hex(self.Status.value)})>'

    def __repr__(self) -> str:
        return self.__str__()


class RANGE_DATA_NTF(NTF):
    """
    Interpret range data notification received during Radar session is ongoing
    """
    GID = Gid.UwbRangingSessionControl
    OID = 0x0
    MIN_EXPECTED_PAYLOAD_SIZE = 50

    def __init__(self, payload: bytes):

        payload_size = len(payload)
        if payload_size < self.MIN_EXPECTED_PAYLOAD_SIZE:
            raise ValueError('Payload expected to contain minimum'
                             f'{self.MIN_EXPECTED_PAYLOAD_SIZE} B, got '
                             f'{payload_size} B')

        handlePayload = PayloadHandler(payload)
        self.SequenceNumber = handlePayload.get_next_field(4)
        self.SessionID = handlePayload.get_next_field(4)
        self.RCRIndication = handlePayload.get_next_field(1)
        self.CurrentRangingInterval = handlePayload.get_next_field(4)
        self.RangingMeasurementType = handlePayload.get_next_field(1)
        self.RFU1 = handlePayload.get_bytes(1)
        self.MACAddressingModeIndicator = handlePayload.get_next_field(1)
        self.RFU2 = handlePayload.get_bytes(8)
        self.NumberofRangingMeasurements = handlePayload.get_next_field(1)

        self.RangingMeasurements = []
        for i in range(self.NumberofRangingMeasurements):
            p = 25 + i * 31
            self.MACAddress = int.from_bytes(payload[p:p + 2], 'little')
            self.Status = Status(int.from_bytes(
                payload[p + 2:p + 3], 'little'))
            self.NLoS = int.from_bytes(payload[p + 3:p + 4], 'little')
            self.Distance = int.from_bytes(payload[p + 4:p + 6], 'little')

            self.bAoAAzimuth = payload[p + 6:p + 8]
            self.AoAAzimuth = self.get_AoA_Azimuth()
            self.AoAAzimuthFOM = int.from_bytes(payload[p + 8:p + 9], 'little')
            self.bAoAElevation = payload[p + 9:p + 11]
            self.AoAElevation = self.get_AoA_Elevation()
            self.AoAElevationFOM = int.from_bytes(
                payload[p + 11:p + 12], 'little')
            self.bAoADestinationAzimuth = payload[p + 12:p + 14]
            self.AoADestinationAzimuth = self.get_AoA_Destination_Azimuth()
            self.AoADestinationAzimuthFOM = int.from_bytes(
                payload[p + 14:p + 15], 'little')
            self.bAoADestinationElevation = payload[p + 15:p + 17]
            self.AoADestinationElevation = self.get_AoA_Destination_Elevation()
            self.AoADestinationElevationFOM = int.from_bytes(
                payload[p + 17:p + 18], 'little')
            self.SlotIndex = int.from_bytes(payload[p + 18:p + 19], 'little')
            self.bRSSI = payload[p + 19:p + 20]
            self.RSSI = self.get_RSSI()
            self.RFU3 = int.from_bytes(payload[p + 20:], 'little')

            self.range_measurement = {'MACAddress': self.MACAddress,
                                      'Status': self.Status,
                                      'Distance': self.Distance,
                                      'AoAAzimuth': self.AoAAzimuth,
                                      'AoAAzimuthFOM': self.AoAAzimuthFOM,
                                      'AoAElevation': self.AoAElevation,
                                      'AoAElevationFOM': self.AoAElevationFOM,
                                      'AoADestinationAzimuth':
                                          self.AoADestinationAzimuth,
                                      'AoADestinationAzimuthFOM':
                                          self.AoADestinationAzimuthFOM,
                                      'AoADestinationElevation':
                                          self.AoADestinationElevation,
                                      'AoADestinationElevationFOM':
                                          self.AoADestinationElevationFOM,
                                          'RSSI':
                                          self.RSSI
                                      }
            self.RangingMeasurements.append(self.range_measurement)

    def get_AoA_Azimuth(self) -> float:
        return _decode_q_format(9, 7, self.bAoAAzimuth)

    def get_AoA_Elevation(self) -> float:
        return _decode_q_format(9, 7, self.bAoAElevation)

    def get_AoA_Destination_Azimuth(self) -> float:
        return _decode_q_format(9, 7, self.bAoADestinationAzimuth)

    def get_AoA_Destination_Elevation(self) -> float:
        return _decode_q_format(9, 7, self.bAoADestinationElevation)

    def get_RSSI(self) -> float:
        return _decode_q_format(7, 1, self.bRSSI, False)

    def __str__(self) -> str:
        return f'<{type(self).__name__}: ' + \
               f'SequenceNumber : {self.SequenceNumber} ' + \
               f'SessionID : {self.SessionID} ' + \
               f'MACAddress : {self.MACAddress} ' + \
               f'Status : {self.Status.name} ' + \
               f'Distance : {self.Distance} ' + \
               f'AoAAzimuth : {self.AoAAzimuth} ' + \
               f'({self.bAoAAzimuth.hex()}), ' + \
               f'AoAAzimuthFOM : {self.AoAAzimuthFOM} ' + \
               f'AoAElevation : {self.AoAElevation} ' + \
               f'({self.bAoAElevation.hex()}), ' + \
               f'AoAElevationFOM : {self.AoAElevationFOM} ' + \
               f'AoADestinationAzimuth : {self.AoADestinationAzimuth} ' + \
               f'({self.bAoADestinationAzimuth.hex()}), ' + \
               f'AoADestinationAzimuthFOM : ' \
               f'{self.AoADestinationAzimuthFOM} ' + \
               f'AoADestinationElevation : {self.AoADestinationElevation} ' + \
               f'({self.bAoADestinationElevation.hex()})' + \
               f'AoADestinationElevationFOM : ' \
               f'{self.AoADestinationElevationFOM}>' + \
                f'RSSI : -{self.RSSI} '

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def __dict__(self) -> dict:
        self.range_measurements = {'SequenceNumber': self.SequenceNumber,
                                   'SessionID': self.SessionID,
                                   'CurrentRangingInterval':
                                       self.CurrentRangingInterval,
                                   'RangingMeasurementType':
                                       self.RangingMeasurementType,
                                   'MACAddressingModeIndicator':
                                       self.MACAddressingModeIndicator,
                                   'NumberofRangingMeasurements':
                                       self.NumberofRangingMeasurements,
                                   'RangingMeasurements':
                                       self.RangingMeasurements}
        return self.range_measurements


def show_device_state(payload):
    state = (int).from_bytes(payload[0:4], 'little')

    print(Fore.RED + 'Device →', DeviceState(state), end='')
    print(Style.RESET_ALL)


def show_session_state(payload):
    (sid, status, reason) = ((int).from_bytes(payload[0:4], 'little'),
                             (int).from_bytes(payload[4:5], 'little'),
                             (int).from_bytes(payload[5:6], 'little'))

    print(Fore.GREEN + 'Session', sid, '→', State(
        status), '(', Reason(reason), ')', end='')
    print(Style.RESET_ALL)


def show_ranging(payload):
    (index, sid) = ((int).from_bytes(payload[0:4], 'little'),
                    (int).from_bytes(payload[4:8], 'little'))

    print(Fore.BLUE + 'Ranging index', index, 'session', sid, '→', end=' ')

    n = (int).from_bytes(payload[24:25], 'little')
    for i in range(n):
        p = 25 + i * 31
        (saddr, status, dist, aoa_azimuth, aoa_azimuth_fom) = (
            (int).from_bytes(payload[p: p + 2], "little"),
            (int).from_bytes(payload[p + 2: p + 3], "little"),
            (int).from_bytes(payload[p + 4: p + 6], "little"),
            (int).from_bytes(payload[p + 6: p + 8], "little"),
            (int).from_bytes(payload[p + 8: p + 9], "little"),
        )
        print(
            "saddr", hex(saddr),
            "status", Status(status),
            "distance", dist,
            "aoa_azimuth", aoa_azimuth,
            "aoa_azimuth_fom", aoa_azimuth_fom,
            end=" | ",
        )
    print(Style.RESET_ALL)


def show_range_data_ntf(payload):
    try:
        decoded_ntf = RANGE_DATA_NTF(payload)
    except Exception as exp:
        ntf_message = f'<{RANGE_DATA_NTF.__name__} - decode ' + \
                      f'error: >> {exp} << for payload {payload}>'
    else:
        ntf_message = f'{decoded_ntf}'
    print(f'{Fore.MAGENTA}' + ntf_message + Style.RESET_ALL)


def show_test(payload):
    status = (int).from_bytes(payload[0:1], 'little')

    print(Fore.MAGENTA + 'test notif', Status(status),
          [hex(x) for x in payload[1:]], end='')
    print(Style.RESET_ALL)


class Client(core.Client):
    def __init__(self, *args, **kwargs):
        handlers = {
            (Gid.UciCore, 0x1): show_device_state,
            (Gid.UwbSessionConfig, 0x2): show_session_state,
            (Gid.UwbRangingSessionControl, 0x0): show_range_data_ntf,
        }
        handlers.update(kwargs.get('notif_handlers', {}))
        kwargs["notif_handlers"] = handlers
        super().__init__(*args, **kwargs)

    def reset_calibration(self):
        payload = self.command(Gid.UwbConfigManager, 0, b'')
        return Status((int).from_bytes(payload[0:1], 'little'))

    def reset(self, reason):
        payload = (reason).to_bytes(1, 'little')

        payload = self.command(Gid.UciCore, 0, payload)

        return Status((int).from_bytes(payload[0:1], 'little'))

    def info(self):
        payload = self.command(Gid.UciCore, 2, b'')

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            (int).from_bytes(payload[1:3], 'little'),
            (int).from_bytes(payload[3:5], 'little'),
            (int).from_bytes(payload[5:7], 'little'),
            (int).from_bytes(payload[7:9], 'little'),
            (int).from_bytes(payload[9:10], 'little'),
            struct.unpack(str(payload[9]) + 'B', payload[10:]),
        )

    def get_caps(self):
        payload = self.command(Gid.UciCore, 3, b'')
        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            (int).from_bytes(payload[1:2], 'little'),
        )

    def set_config(self, tvs):
        payload = core.tvs_to_bytes(Device.defs, tvs)

        payload = self.command(Gid.UciCore, 4, payload)

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            core.list_from_bytes(Status, payload[1:])
        )

    def get_config(self, params):
        payload = core.list_to_bytes(params)

        payload = self.command(Gid.UciCore, 5, payload)

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            core.tlvs_from_bytes(Device, payload[1:])
        )

    def session_init(self, sid, stype):
        payload = (sid).to_bytes(4, 'little')
        payload += (stype).to_bytes(1, 'little')

        payload = self.command(Gid.UwbSessionConfig, 0, payload)
        return Status((int).from_bytes(payload[0:1], 'little'))

    def session_deinit(self, sid):
        payload = (sid).to_bytes(4, 'little')

        payload = self.command(Gid.UwbSessionConfig, 1, payload)
        return Status((int).from_bytes(payload[0:1], 'little'))

    def session_set_app_config(self, sid, params):
        payload = (sid).to_bytes(4, 'little')

        payload += core.tvs_to_bytes(App.defs, params)

        payload = self.command(Gid.UwbSessionConfig, 3, payload)

        if Status((int).from_bytes(payload[0:1], 'little')) != 2:
            return (
                Status((int).from_bytes(payload[0:1], 'little')),
                core.list_from_bytes(Status, payload[1:]),
            )
        else:
            return(
                Status((int).from_bytes(payload[0:1], 'little')),
                [],
            )

    def session_get_app_config(self, sid, params):
        payload = (sid).to_bytes(4, 'little')
        payload += core.list_to_bytes(params)

        payload = self.command(Gid.UwbSessionConfig, 4, payload)

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            core.tlvs_from_bytes(App, payload[1:])
        )

    def session_get_count(self):
        payload = self.command(Gid.UwbSessionConfig, 5, b'')

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            (int).from_bytes(payload[1:2], 'little')
        )

    def session_get_state(self, sid):
        payload = (sid).to_bytes(4, 'little')

        payload = self.command(Gid.UwbSessionConfig, 6, payload)

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            State((int).from_bytes(payload[1:2], 'little'))
        )

    def session_start(self, sid):
        cmd = RANGE_START_CMD(sid)
        rsp = cmd.send(self)
        return RANGE_START_RSP(rsp)

    def session_stop(self, sid):
        cmd = RANGE_STOP_CMD(sid)
        rsp = cmd.send(self)
        return RANGE_STOP_RSP(rsp)

    # Deprecated for future ussage. Replaced by session_start_cmd()
    def session_start_basic(self, sid):
        payload = (sid).to_bytes(4, 'little')

        payload = self.command(Gid.UwbRangingSessionControl, 0, payload)
        return Status((int).from_bytes(payload[0:1], 'little'))

    # Deprecated for future ussage. Replaced by session_stop_cmd()
    def session_stop_basic(self, sid):
        payload = (sid).to_bytes(4, 'little')

        payload = self.command(Gid.UwbRangingSessionControl, 1, payload)
        return Status((int).from_bytes(payload[0:1], 'little'))

    # Deprecated for future ussage, test commands available in test_v1_1 client
    def test_config_set(self, sid, params):
        payload = (sid).to_bytes(4, 'little')

        payload += core.tvs_to_bytes(TestParam.defs, params)

        payload = self.command(Gid.Test, 0, payload)

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            core.list_from_bytes(Status, payload[1:]),
        )

    def test_config_get(self, sid, params):
        payload = (sid).to_bytes(4, 'little')

        payload += core.list_to_bytes(params)

        payload = self.command(Gid.Test, 1, payload)

        return (
            Status((int).from_bytes(payload[0:1], 'little')),
            core.tlvs_from_bytes(TestParam, payload[1:]),
        )

    def test_periodic_tx(self, payload):
        payload = self.command(Gid.Test, 2, payload)

        return Status((int).from_bytes(payload[0:1], 'little'))

    def test_per_rx(self, payload):
        payload = self.command(Gid.Test, 3, payload)

        return Status((int).from_bytes(payload[0:1], 'little'))

    def test_rx(self):
        payload = self.command(Gid.Test, 5, b'')

        return Status((int).from_bytes(payload[0:1], 'little'))

    def test_loopback(self, payload):
        payload = self.command(Gid.Test, 6, payload)

        return Status((int).from_bytes(payload[0:1], 'little'))

    def test_stop_session(self):
        payload = self.command(Gid.Test, 7, b'')

        return Status((int).from_bytes(payload[0:1], 'little'))

    def test_ss_twr(self):
        payload = self.command(Gid.Test, 8, b'')

        return Status((int).from_bytes(payload[0:1], 'little'))
