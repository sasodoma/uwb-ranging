# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library is defining some FIRA specific enums
"""

# It is safe to import the full library to have access to all UCI-related Data

import logging
from .utils import *

__all__ = [
    "Gid",
    "OidCore",
    "OidSession",
    "OidRanging",
    "OidTest",
    "DlTdoa",
    "SessionType",
    "TestModeSessionId",
    "Status",
    "DeviceType",
    "DeviceRole",
    "SessionState",
    "SessionStateChangeReason",
    "RfFrame",
    "DeviceState",
    "IsTrue",
    "IsEnabled",
    "FrameStatusMask",
    "AoaType",
    "RangingRound",
    "Node",
    "StsConfig",
    "MulticastControleeStatus",
    "MulticastControlee",
    "CapsParameters",
]

logger = logging.getLogger()


# =============================================================================
# Core Enums
# =============================================================================


class Gid(DynIntEnum):
    Core = 0x00
    Session = 0x01
    Ranging = 0x02
    Test = 0x0D


class OidCore(DynIntEnum):
    Reset = 0x00
    DeviceStatus = 0x01
    GetDeviceInfo = 0x02
    GetCaps = 0x03
    SetConfig = 0x04
    GetConfig = 0x05
    GenericError = 0x07
    GetTime = 0x08


class OidSession(DynIntEnum):
    Init = 0x00
    Deinit = 0x01
    Status = 0x02
    SetAppConfig = 0x03
    GetAppConfig = 0x04
    GetCount = 0x05
    GetState = 0x06
    UpdateMulticastList = 0x07  # SESSION_UPDATE_CONTROLLER_MULTICAST_LIST_
    SetAnchorRangingRounds = 0x08  # SESSION_UPDATE_DT_ANCHOR_RANGING_ROUNDS
    SetTagActivity = 0x09  # SESSION_UPDATE_DT_TAG_RANGING_ROUNDS
    GetDataSize = 0xB
    UpdateHus = 0xC


class OidRanging(DynIntEnum):
    Start = 0x00  # and data NTF
    Stop = 0x01
    GetCount = 0x03
    DataCredit = 0x04
    DataTransferStatus = 0x05


class OidTest(DynIntEnum):
    ConfigSet = 0x00
    ConfigGet = 0x01
    PeriodicTx = 0x02
    PerRx = 0x03
    Rx = 0x05
    Loopback = 0x06
    StopSession = 0x07
    SsTwr = 0x08


class Status(DynIntEnum):
    # Generic Status Codes:
    Ok = 0x0
    Rejected = 0x01
    Failed = 0x02
    SyntaxErr = 0x03
    InvalidParam = 0x04
    InvalidRange = 0x05
    InvalidMessageSize = 0x06
    UnknownGid = 0x07
    UnknownOid = 0x08
    ReadOnly = 0x09
    CommandRetry = 0x0A
    # RFU 0x0b - 0x0f
    # UWB Session Specific Status Codes:
    ErrorSessionNotExist = 0x11
    ErrorSessionDuplicate = 0x12
    ErrorSessionActive = 0x13
    ErrorMaxSessionsExceeded = 0x14
    ErrorSessionNotConfigured = 0x15
    ErrorActiveSessionsOngoing = 0x16
    ErrorMulticastListFull = 0x17
    # RFU 0x18 - 0x19
    ErrorUwbInitializationTimeTooOld = 0x1A
    RangingNegativeDistance = 0x1B
    # UWB Ranging Session Specific Status Codes
    RangingTxFailed = 0x20
    RangingRxTimeout = 0x21
    RangingRxPhyDecFailed = 0x22
    RangingRxPhyToaFailed = 0x23
    RangingRxPhyStsFailed = 0x24
    RangingRxMacDecFailed = 0x25
    RangingRxMacIeDecFailed = 0x26
    RangingRxMacIeMissing = 0x27
    ErrorRoundIndexNotActivated = 0x28
    ErrorNumberOfActiveRoundExceeded = 0x29
    ErrorDlTdoaDeviceAddressNotMatchingInReplyTimeList = 0x2A
    # RFU 0x2b - 0x4f
    # Proprietary Status Codes 0x50 - 0xff
    ErrorSeBusy = 0x50
    ErrorCccLifeCycle = 0x51
    Unknown = 0xFF


class MulticastControlee(DynIntEnum):
    """Enum used by SESSION_UPDATE_CONTROLLER_MULTICAST_LIST_CMD"""

    Add = 0x00  # Add the Controlee to the multicast list
    Delete = 0x01  # Delete the Controlee from the multicast list
    AddWithShortSkey = 0x02  # Add the Controlee with its 16-octet Sub-Session Key
    AddWithLongSkey = 0x03  # Add the Controlee with its 32-octet Sub-Session Key
    # 0x04 to 0xFF = RFU
    Unknown = -1


class MulticastControleeStatus(DynIntEnum):
    """Enum used by SESSION_UPDATE_CONTROLLER_MULTICAST_LIST_NTF"""

    Ok = 0x00
    ListFull = 0x01
    KeyFetchFailure = 0x02
    SubSectionIDNotFound = 0x03
    SubDectionKeyNotFound = 0x04
    SubDectionKeyNotApplicable = 0x05
    SessionKeyNotFound = 0x06
    AddressNotFound = 0x07
    AddressAlreadyPresent = 0x08
    # 0x09 - 0x1F : RFU
    Unknown = -1


class SessionType(DynIntEnum):
    Ranging = 0x00
    RangingAndData = 0x01
    Data = 0x02
    RangingPhase = 0x03
    DataPhase = 0x04
    RangingAndDataPhase = 0x05
    HusPrimarySession = 0x9F
    DeviceTestMode = 0xD0
    Unknown = 0x100


TestModeSessionId = 0


class SessionState(DynIntEnum):
    Init = 0x0
    DeInit = 0x1
    Active = 0x2
    Idle = 0x3
    Unknown = -1


# DEVICE_TYPE
# (in line with Fira UCI Generic Technical Specification 2.0.0-0.9r2 p94)
class DeviceType(DynIntEnum):
    Controlee = 0x00
    Controller = 0x01
    Unknown = 0xFF


# RANGING_ROUND_USAGE
# (in line with Fira UCI Generic Technical Specification 2.0.0-0.9r2 p94)
class RangingRound(DynIntEnum):
    OwrUltdoa = 0x00
    SsTwrDeferred = 0x01
    DsTwrDeferred = 0x02
    SsTwr = 0x03
    DsTwr = 0x04
    OwrDltdoa = 0x05
    OwrAoa = 0x06
    EssTwr = 0x07
    AdssTwr = 0x08
    Unknown = 0xFF


# STS_CONFIG
# (in line with Fira UCI Generic Technical Specification 2.0.0-0.9r2 p94)
class StsConfig(DynIntEnum):
    Static = 0x00
    Dynamic = 0x01
    DynamicWithKey = 0x02
    Provisioned = 0x03
    ProvisionedWithKey = 0x04
    Unknown = 0xFF


# MULTI_NODE_MODE
# (in line with Fira UCI Generic Technical Specification 2.0.0-0.9r2 p95)
class Node(DynIntEnum):
    Unicast = 0x00
    OneToMAny = 0x01
    ManyToMAny = 0x02
    Unknown = 0xFF


# RFRAME_CONFIG
# (in line with Fira UCI Generic Technical Specification 2.0.0-0.9r2 p101)
class RfFrame(DynIntEnum):
    Sp0 = 0x00
    Sp1 = 0x01
    Qp3 = 0x03
    Unknown = 0xFF


# DL_TDOA_RANGING_METHOD
# (in line with Fira UCI Generic Technical Specification 2.0.0-0.9r2 p118)
class DlTdoa(DynIntEnum):
    SsTwr = 0x00
    DsTwr = 0x01


class SessionStateChangeReason(DynIntEnum):
    StateChangeWithSessionManagementCommands = 0x0
    MaxRangingRoundRetryCountReached = 0x01
    MaxNumberOfMeasurementReached = 0x02
    SessionSuspendedDueToInbandSignal = 0x03
    SessionResumedDueToInbandSignal = 0x04
    SessionStoppedDueToInbandSignal = 0x05
    # From 0x06 to 0x1c, Reserved for Future Use.
    ErrorInvalidUlTdoaRandomWindow = 0x1D
    ErrorMinRframesPerRrNotSupported = 0x1E
    ErrorInterFrameIntervalNotSupported = 0x1F
    ErrorSlotLengthNotSupported = 0x20
    ErrorInsufficientSlotsPerRR = 0x21
    ErrorMacAddressModeNotSupported = 0x22
    ErrorInvalidRangingDuration = 0x23
    ErrorInvalidStsConfig = 0x24
    ErrorInvalidRFrameConfig = 0x25
    ErrorHusNotEnoughSlots = 0x26
    ErrorHusCfpPhaseTooShort = 0x27
    ErrorHusCapPhaseTooShort = 0x28
    ErrorHusOthers = 0x29
    ErrorSessionKeyNotFound = 0x2A
    ErrorSubSessionKeyNotFound = 0x2B
    ErrorInvalidPreambleCodeIndex = 0x2C
    ErrorInvalidSfdId = 0x2D
    ErrorInvalidPsduDataRate = 0x2E
    ErrorInvalidPhrDataRate = 0x2F
    ErrorInvalidPreambleDuration = 0x30
    ErrorInvalidStsLength = 0x31
    ErrorInvalidNumOfStsSegments = 0x32
    ErrorInvalidNumOfControlees = 0x33
    ErrorMaxRangingReplyTimeExceeded = 0x34
    ErrorInvalidDstAddressList = 0x35
    ErrorInvalidOrNotFoundSubSessionId = 0x36
    ErrorInvalidResultReportConfig = 0x37
    ErrorInvalidRangingRoundControlConfig = 0x38
    ErrorInvalidRangingRoundUsage = 0x39
    ErrorInvalidMultiNodeMode = 0x3A
    ErrorRdsFetchFailure = 0x3B
    ErrorRefSessionDoesNotExist = 0x3C
    ErrorRefSessionRangingDurationMismatch = 0x3D
    ErrorRefSessionInvalidTimeOffsetTime = 0x3E
    ErrorRefSessionLost = 0x3F
    ErrorDtAnchorRangingRoundsNotConfigured = 0x40
    ErrorDtTagRangingRoundsNotConfigured = 0x41
    ErrorUwbInitiationTimeExpired = 0x42
    # From 0x43 to 0x7f, Reserved for Future Use.
    # From 0x80 to 0xff, it is vendor specific.
    ErrorInvalidChannelWithAoa = 0x80
    ErrorStoppedDueToOtherSessionConflict = 0x81
    ErrorRegulationUwbOff = 0x82
    # All internal reason codes should be put at the end of the range
    # intended for vendor specific values (decrementing from 0xff).
    ErrorMaxStsReached = 0xF2
    ErrorRadarMeasurementTimeReached = 0xF3
    ErrorInvalidDeviceRole = 0xF4
    ErrorNoMem = 0xF5
    ErrorDriverDown = 0xF7
    ErrorInvalidProximityRange = 0xF8
    ErrorInvalidFrameInterval = 0xF9
    ErrorInvalidCapSizeRange = 0xFA
    ErrorInvalidScheduleMode = 0xFB
    ErrorInvalidPrfMode = 0xFC
    ErrorStartConfig = 0xFE
    ErrorRdsBusy = 0xFF


class DeviceState(DynIntEnum):
    Ready = 0x01
    Active = 0x02
    Error = 0xFF
    Unknown = 0xFFFF


# DEVICE_ROLE
# (in line with Fira UCI Generic Technical Specification 2.0.0-0.9r2 p101)
class DeviceRole(DynIntEnum):
    Responder = 0x00
    Initiator = 0x01
    UtSyncAnchor = 0x02
    UtAnchor = 0x03
    UtTag = 0x04
    Advertiser = 0x05
    Observer = 0x06
    DtAnchor = 0x07
    DtTag = 0x08
    Unknown = 0xFF


class IsEnabled(DynIntEnum):
    no = 0
    yes = 1
    Unknown = 0xFF


class IsTrue(DynIntEnum):
    no = 0
    yes = 1
    Unknown = 0xFF


class FrameStatusMask(DynIntEnum):
    FrameProcessedOk = 1
    WifiActivationDuringFrame = 2
    Unknown = 0xFF


class AoaType(DynIntEnum):
    XAxis = 0x00
    YAxis = 0x01
    ZAxis = 0x02
    LastAxis = 0x03
    Unknown = 0xFF


class CapsParameters(DynIntEnum):
    MAX_MESSAGE_SIZE = 0x00
    MAX_DATA_PACKET_PAYLOAD_SIZE = 0x01
    FIRA_PHY_VERSION_RANGE = 0x02
    FIRA_MAC_VERSION_RANGE = 0x03
    DEVICE_TYPE = 0x04
    DEVICE_ROLES = 0x05
    RANGING_METHOD = 0x06
    STS_CONFIG = 0x07
    MULTI_NODE_MODE = 0x08
    RANGING_TIME_STRUCT = 0x09
    SCHEDULE_MODE = 0x0A
    HOPPING_MODE = 0x0B
    BLOCK_STRIDING = 0x0C
    UWB_INITIATION_TIME = 0x0D
    CHANNELS = 0x0E
    RFRAME_CONFIG = 0x0F
    CC_CONSTRAINT_LENGTH = 0x10
    BPRF_PARAMETER_SETS = 0x11
    HPRF_PARAMETER_SETS = 0x12
    AOA_SUPPORT = 0x13
    EXTENDED_MAC_ADDRESS = 0x14
    Assigned = 0x15
    SESSION_KEY_LENGTH = 0x16
    DT_ANCHOR_MAX_ACTIVE_RR = 0x17
    DT_TAG_MAX_ACTIVE_RR = 0x18
    DT_TAG_BLOCK_SKIPPING = 0x19
    Unknown = 0xFF
