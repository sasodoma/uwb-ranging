# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library is handling FIRA Session parameter definition
"""

from .utils import DynIntEnum

__all__ = ["App", "TestParam"]


class App(DynIntEnum):
    DeviceType = 0x00
    RangingRoundUsage = 0x01
    StsConfig = 0x02
    MultiNodeMode = 0x03
    ChannelNumber = 0x04
    NumberOfControlees = 0x05
    DeviceMacAddress = 0x06
    DstMacAddress = 0x07
    SlotDuration = 0x08
    RangingInterval = 0x09  # now called RangingDuration
    StsIndex = 0x0A
    MacFcsType = 0x0B
    RangingRoundControl = 0x0C
    AoaResultReq = 0x0D
    RangeDataNtfConfig = 0x0E
    RangeDataNtfProximityNear = 0x0F
    RangeDataNtfProximityFar = 0x10
    DeviceRole = 0x11
    RframeConfig = 0x12
    RssiReporting = 0x13
    PreambleCodeIndex = 0x14
    SfdId = 0x15
    PsduDataRate = 0x16
    PreambleDuration = 0x17
    LinkLayerMode = 0x18
    DataRepetitionCount = 0x19  # RFU reserved for DATA_REPETITION_COUNT
    RangingTimeStruct = 0x1A
    SlotsPerRr = 0x1B
    SessionInfoNtfBoundAoa = 0x1D
    # 0x1d RFU reserved for RANGE_DATA_NTF_BOUND_AOA
    ResponderSlotIndex = 0x1E
    PrfMode = 0x1F
    CapSizeRange = 0x20  # for Contention based
    # 0x21 RFU reserved for TX_WINDOW_SIZE
    ScheduleMode = 0x22
    KeyRotation = 0x23
    KeyRotationRate = 0x24
    SessionPriority = 0x25
    MacAddressMode = 0x26
    VendorId = 0x27
    StaticStsIv = 0x28
    NumberOfStsSegments = 0x29
    MaxRrRetry = 0x2A
    UwbInitiationTime = 0x2B
    HoppingMode = 0x2C
    BlockStrideLength = 0x2D
    ResultReportConfig = 0x2E
    InBandTerminationAttemptCount = 0x2F
    SubSessionId = 0x30
    BprfPhrDataRate = 0x31
    MaxNumberOfMeasurements = 0x32
    UlTdoaTxInterval = 0x33
    UlTdoaRandomWindow = 0x34
    StsLength = 0x35
    UlTdoaDeviceId = 0x38
    UlTdoaTxTimestamp = 0x39
    MinFramesPerRr = 0x3A
    MtuSize = 0x3B
    InterFrameInterval = 0x3C
    DlTdoaTxTimestampConf = 0x3E
    DlTdoaHopCount = 0x3F
    DlTdoaAnchorCfo = 0x40
    DlTdoaAnchorLocation = 0x41
    DlTdoaTxActiveRangingRounds = 0x42
    DlTdoaBlockStriding = 0x43
    DlTdoaTimeReferenceAnchor = 0x44
    SessionKey = 0x45
    SubSessionKey = 0x46
    SessionDataTransferStatusNtfConfig = 0x47
    DlTdoaResponderTof = 0x49
    OwrAoaMeasurementNtfPeriod = 0x4D
    HopModeKey = 0xA0
    CccUwbTime0 = 0xA1
    SelectedProtVer = 0xA3
    SelectedUwbConfigId = 0xA4
    SelectedShapeCombo = 0xA5
    URSK_TTL = 0xA6
    CccStsIndex = 0xA8
    DlTdoaRangingMethod = 0x3D
    Mac_mode = 0xA9
    Ursk = 0xAA
    # Proprietary 0xe3  0xff


App.defs = [
    (App.CapSizeRange, 2),
    (App.DlTdoaTimeReferenceAnchor, 1),
    (App.DlTdoaBlockStriding, 1),
    (App.DlTdoaTxActiveRangingRounds, 1),
    (App.DlTdoaAnchorLocation, 1),  # could also be 11 or 13
    (App.DlTdoaAnchorCfo, 1),
    (App.DlTdoaTxTimestampConf, 1),
    (App.DlTdoaRangingMethod, 1),
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
    (App.SelectedUwbConfigId, 2),
    (App.PsduDataRate, 1),
    (App.PreambleDuration, 1),
    (App.LinkLayerMode, 1),
    (App.DataRepetitionCount, 1),
    (App.RangingTimeStruct, 1),
    (App.SlotsPerRr, 1),
    (App.SessionInfoNtfBoundAoa, 8),
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
    (App.UwbInitiationTime, 8),
    (App.HoppingMode, 1),
    (App.BlockStrideLength, 1),
    (App.ResultReportConfig, 1),
    (App.InBandTerminationAttemptCount, 1),
    (App.SubSessionId, 4),
    (App.BprfPhrDataRate, 1),
    (App.MaxNumberOfMeasurements, 2),
    (App.UlTdoaTxInterval, 4),
    (App.UlTdoaRandomWindow, 4),
    (App.StsLength, 1),
    (App.UlTdoaDeviceId, 1),
    (App.UlTdoaTxTimestamp, 1),
    (App.RssiReporting, 1),
    (App.SessionKey, [16, 32]),
    (App.SubSessionKey, 16),  # could be 32 (!)
    (App.SessionDataTransferStatusNtfConfig, 1),
    (App.HopModeKey, 16),
    (App.CccUwbTime0, 8),
    (App.SelectedProtVer, 2),
    (App.SelectedShapeCombo, 1),
    (App.URSK_TTL, 2),
    (App.MinFramesPerRr, 1),
    (App.CccStsIndex, 4),
    (App.MtuSize, 2),
    (App.InterFrameInterval, 1),
    (App.DlTdoaHopCount, 1),
    (App.DlTdoaResponderTof, 1),
    (App.OwrAoaMeasurementNtfPeriod, 1),
    (App.Mac_mode, 1),
    (App.Ursk, 32),
]


class TestParam(DynIntEnum):
    NumPackets = 0x00
    TGap = 0x1
    TStart = 0x2
    TWin = 0x3
    RandomizePsdu = 0x04
    PhrRangingBit = 0x05
    RMarkerTxStart = 0x06
    RMarkerRxStart = 0x07
    StsIndexAutoIncr = 0x08
    Unknown = 0xFF


TestParam.defs = {
    TestParam.NumPackets: 4,
    TestParam.TGap: 4,
    TestParam.TStart: 4,
    TestParam.TWin: 4,
    TestParam.RandomizePsdu: 1,
    TestParam.PhrRangingBit: 1,
    TestParam.RMarkerTxStart: 4,
    TestParam.RMarkerRxStart: 4,
    TestParam.StsIndexAutoIncr: 1,
}
