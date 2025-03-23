# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

__all__ = ["caps", "UnsupportedCap"]

from .fira_enums import CapsParameters


class SharedData:
    dt_anchor_supported = False
    dt_tag_supported = False


class MacFiraVersionRange:
    def __init__(self, value):
        self.lower_major_version = value[0]
        self.lower_minor_maintenance_version = value[1]
        self.higher_major_version = value[2]
        self.higher_minor_maintenance_version = value[3]

        self.lower_version = (
            f"{self.lower_major_version}.{self.lower_minor_maintenance_version}"
        )
        self.higher_version = (
            f"{self.higher_major_version}.{self.higher_minor_maintenance_version}"
        )

    def __str__(self):
        return f"Supported MAC version range: {self.lower_version} to {self.higher_version}\n"


class PhyFiraVersionRange:
    def __init__(self, value):
        self.lower_major_version = value[0]
        self.lower_minor_maintenance_version = value[1]
        self.higher_major_version = value[2]
        self.higher_minor_maintenance_version = value[3]

        self.lower_version = (
            f"{self.lower_major_version}.{self.lower_minor_maintenance_version}"
        )
        self.higher_version = (
            f"{self.higher_major_version}.{self.higher_minor_maintenance_version}"
        )

    def __str__(self):
        return f"Supported PHY version range: {self.lower_version} to {self.higher_version}\n"


class DeviceType:
    def __init__(self, value):
        self.name = CapsParameters.DEVICE_TYPE.name
        _capability_flags = value[0]
        self.controller_supported = bool(_capability_flags & 0x01)
        self.controlee_supported = bool(_capability_flags & 0x02)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    Controller: {'Supported' if self.controller_supported else 'Not supported'}\n"
            f"    Controlee: {'Supported' if self.controlee_supported else 'Not supported'}\n"
        )


class DeviceRoles:
    def __init__(self, value):
        self.name = CapsParameters.DEVICE_ROLES.name
        _capability_flags = int.from_bytes(value, "little")

        self.responder_supported = bool(_capability_flags & 0x01)
        self.initiator_supported = bool(_capability_flags & 0x02)
        self.advertiser_supported = bool(_capability_flags & 0x20)
        self.observer_supported = bool(_capability_flags & 0x40)
        SharedData.dt_anchor_supported = bool(_capability_flags & 0x80)
        SharedData.dt_tag_supported = bool(_capability_flags & 0x100)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    Responder: {'Supported' if self.responder_supported else 'Not supported'}\n"
            f"    Initiator: {'Supported' if self.initiator_supported else 'Not supported'}\n"
            f"    Advertiser: {'Supported' if self.advertiser_supported else 'Not supported'}\n"
            f"    Observer: {'Supported' if self.observer_supported else 'Not supported'}\n"
            f"    DT-Anchor: {'Supported' if SharedData.dt_anchor_supported else 'Not supported'}\n"
            f"    DT-Tag: {'Supported' if SharedData.dt_tag_supported else 'Not supported'}\n"
        )


class RangingMethod:
    def __init__(self, value):
        self.name = CapsParameters.RANGING_METHOD.name
        _capability_flags = int.from_bytes(value, "little")

        self.owr_ul_tdoa_supported = bool(_capability_flags & 0x01)
        self.ss_twr_deferred_supported = bool(_capability_flags & 0x02)
        self.ds_twr_deferred_supported = bool(_capability_flags & 0x04)
        self.ss_twr_non_deferred_supported = bool(_capability_flags & 0x08)
        self.ds_twr_non_deferred_supported = bool(_capability_flags & 0x10)
        self.owr_dl_tdoa_supported = bool(_capability_flags & 0x20)
        self.owr_aoa_measurement_supported = bool(_capability_flags & 0x40)
        self.ess_twr_non_deferred_contention_supported = bool(_capability_flags & 0x80)
        self.ads_twr_contention_supported = bool(_capability_flags & 0x100)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    OWR UL-TDOA: {'Supported' if self.owr_ul_tdoa_supported else 'Not supported'}\n"
            f"    SS-TWR with Deferred Mode: {'Supported' if self.ss_twr_deferred_supported else 'Not supported'}\n"
            f"    DS-TWR with Deferred Mode: {'Supported' if self.ds_twr_deferred_supported else 'Not supported'}\n"
            f"    SS-TWR with Non-deferred Mode: {'Supported' if self.ss_twr_non_deferred_supported else 'Not supported'}\n"
            f"    DS-TWR with Non-deferred Mode: {'Supported' if self.ds_twr_non_deferred_supported else 'Not supported'}\n"
            f"    OWR DL-TDOA: {'Supported' if self.owr_dl_tdoa_supported else 'Not supported'}\n"
            f"    OWR for AOA Measurement: {'Supported' if self.owr_aoa_measurement_supported else 'Not supported'}\n"
            "    eSS-TWR with Non-deferred Mode for Contention-based ranging: "
            f"{'Supported' if self.ess_twr_non_deferred_contention_supported else 'Not supported'}\n"
            "    aDS-TWR for Contention-based ranging: "
            f"{'Supported' if self.ads_twr_contention_supported else 'Not supported'}\n"
        )


class StsConfig:
    def __init__(self, value):
        self.name = CapsParameters.STS_CONFIG.name
        _capability_flags = int.from_bytes(value, "little")

        self.static_sts_supported = bool(_capability_flags & 0x01)
        self.dynamic_sts_supported = bool(_capability_flags & 0x02)
        self.dynamic_sts_responder_subsession_supported = bool(_capability_flags & 0x04)
        self.provisioned_sts_supported = bool(_capability_flags & 0x08)
        self.provisioned_sts_responder_subsession_supported = bool(
            _capability_flags & 0x10
        )

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    Static STS: {'Supported' if self.static_sts_supported else 'Not supported'}\n"
            f"    Dynamic STS: {'Supported' if self.dynamic_sts_supported else 'Not supported'}\n"
            "    Dynamic STS for Responder Specific Sub-Session Key: "
            f"{'Supported' if self.dynamic_sts_responder_subsession_supported else 'Not supported'}\n"
            f"    Provisioned STS: {'Supported' if self.provisioned_sts_supported else 'Not supported'}\n"
            "    Provisioned STS for Responder Specific Sub-Session Key: "
            f"{'Supported' if self.provisioned_sts_responder_subsession_supported else 'Not supported'}\n"
        )


class MultiNodeMode:
    def __init__(self, value):
        self.name = CapsParameters.MULTI_NODE_MODE.name

        _capability_flags = value[0]

        self.unicast_supported = bool(_capability_flags & 0x01)
        self.one_to_many_supported = bool(_capability_flags & 0x02)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    Single device to Single device (Unicast): {'Supported' if self.unicast_supported else 'Not supported'}\n"
            f"    One to Many: {'Supported' if self.one_to_many_supported else 'Not supported'}\n"
        )


class RangingTime:
    def __init__(self, value):
        self.name = CapsParameters.RANGING_TIME_STRUCT.name

        _capability_flags = value[0]

        self.rfu_supported = bool(_capability_flags & 0x01)
        self.block_based_scheduling_supported = bool(_capability_flags & 0x02)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    RFU: {'Supported' if self.rfu_supported else 'Not supported'}\n"
            f"    Block Based Scheduling: {'Supported' if self.block_based_scheduling_supported else 'Not supported'}\n"
        )


class ScheduleMode:
    def __init__(self, value):
        self.name = CapsParameters.SCHEDULE_MODE.name

        _capability_flags = value[0]

        self.contention_based_ranging_supported = bool(_capability_flags & 0x01)
        self.time_scheduled_ranging_supported = bool(_capability_flags & 0x02)
        self.hybrid_ranging_supported = bool(_capability_flags & 0x04)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    Contention based ranging: {'Supported' if self.contention_based_ranging_supported else 'Not supported'}\n"
            f"    Time scheduled ranging: {'Supported' if self.time_scheduled_ranging_supported else 'Not supported'}\n"
            f"    Hybrid ranging: {'Supported' if self.hybrid_ranging_supported else 'Not supported'}\n"
        )


class HoppingMode:
    def __init__(self, value):
        self.name = CapsParameters.HOPPING_MODE.name
        _capability_flags = value[0]
        self.preference_of_hopping_supported = bool(_capability_flags & 0x01)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    Preference of hopping: {'Supported' if self.preference_of_hopping_supported else 'Not supported'}\n"
        )


class BlockStriding:
    def __init__(self, value):
        self.name = CapsParameters.BLOCK_STRIDING.name
        _capability_flags = value[0]
        self.preference_of_block_striding_supported = bool(_capability_flags & 0x01)

    def __str__(self):
        return (
            f"{self.name}\n"
            "    Preference of Block Striding: "
            f"{'Supported' if self.preference_of_block_striding_supported else 'Not supported'}\n"
        )


class UwbInitTime:
    def __init__(self, value):
        self.name = CapsParameters.UWB_INITIATION_TIME.name
        self.preference_of_block_striding_supported = bool(value[0] & 0x01)

    def __str__(self):
        return (
            f"{self.name}\n"
            "    UWB Initiation Time configuration: "
            f"{'Supported' if self.preference_of_block_striding_supported else 'Not supported'}\n"
        )


class Channels:
    def __init__(self, value):
        self.name = CapsParameters.CHANNELS.name
        self.channel_flags_supported = []

        for i in range(8):
            channel_flag = value[0] & (1 << i)
            channel_supported = bool(channel_flag)
            self.channel_flags_supported.append(channel_supported)

    def __str__(self):
        output = f"{self.name}\n" f"Channel flags:\n"
        channel_numbers = [5, 6, 8, 9, 10, 12, 13, 14]
        for i, channel_supported in enumerate(self.channel_flags_supported):
            output += f"    Channel {channel_numbers[i]}: {'Supported' if channel_supported else 'Not supported'}\n"
        return output


class RframeConfig:
    def __init__(self, value):
        self.name = CapsParameters.RFRAME_CONFIG.name
        self.sp_flags_supported = []
        for i in range(4):
            sp_flag = value[0] & (1 << i)
            sp_supported = bool(sp_flag)
            self.sp_flags_supported.append(sp_supported)

    def __str__(self):
        output = f"{self.name}\n" f"SP flags:\n"
        for i, sp_supported in enumerate(self.sp_flags_supported):
            output += f"    SP{i}: {'Supported' if sp_supported else 'Not supported'}\n"
        return output


class CcConstraintLength:
    def __init__(self, value):
        self.name = CapsParameters.CC_CONSTRAINT_LENGTH.name
        self.k3_supported = bool(value[0] & 0x01)
        self.k7_supported = bool(value[0] & 0x02)

    def __str__(self):
        output = (
            f"{self.name}\n"
            f"    k = 3 Supported: {'YES' if self.k3_supported else 'NO'}\n"
        )
        output += f"    k = 7 Supported: {'YES' if self.k7_supported else 'NO'}\n"
        return output


class BprfParameterSets:
    def __init__(self, value):
        self.name = CapsParameters.BPRF_PARAMETER_SETS.name
        self.bprf_flags_supported = [bool(value[0] & (1 << i)) for i in range(6)]

    def __str__(self):
        output = f"{self.name}\n"
        for i, bprf_supported in enumerate(self.bprf_flags_supported, 1):
            output += f"    BPRF Set {i}: {'Supported' if bprf_supported else 'Not supported'}\n"
        return output


class HprfParameterSets:
    def __init__(self, value):
        self.name = CapsParameters.HPRF_PARAMETER_SETS.name
        self.hprf_flags_supported = []
        for byte_idx in range(5):
            for bit_idx in range(8):
                hprf_flag = value[byte_idx] & (1 << bit_idx)
                hprf_supported = bool(hprf_flag)
                self.hprf_flags_supported.append(hprf_supported)

    def __str__(self):
        output = f"{self.name}\n"
        for i, hprf_supported in enumerate(self.hprf_flags_supported, 1):
            output += f"    HPRF Set {i}: {'Supported' if hprf_supported else 'Not supported'}\n"
        return output


class AoaSupport:
    def __init__(self, value):
        self.name = CapsParameters.AOA_SUPPORT.name
        _capability_flags = value[0]
        self.azimuth_90_supported = bool(_capability_flags & 0x01)
        self.azimuth_180_supported = bool(_capability_flags & 0x02)
        self.elevation_supported = bool(_capability_flags & 0x04)
        self.fom_supported = bool(_capability_flags & 0x08)

    def __str__(self):
        output = f"{self.name}\n"
        output += f"    Azimuth AoA -90   to 90  : {'Supported' if self.azimuth_90_supported else 'Not supported'}\n"
        output += f"    Azimuth AoA -180   to 180  : {'Supported' if self.azimuth_180_supported else 'Not supported'}\n"
        output += f"    Elevation AoA: {'Supported' if self.elevation_supported else 'Not supported'}\n"
        output += (
            f"    AoA FOM: {'Supported' if self.fom_supported else 'Not supported'}\n"
        )
        return output


class ExtendedMacAddress:
    def __init__(self, value):
        self.name = CapsParameters.EXTENDED_MAC_ADDRESS.name
        self.extended_mac_address_supported = bool(value[0] & 0x01)

    def __str__(self):
        return (
            f"{self.name}\n"
            f"    The Extended MAC address is {'supported' if self.extended_mac_address_supported else 'not supported'}.\n"
        )


class SessionKeyLength:
    def __init__(self, value):
        self.name = CapsParameters.SESSION_KEY_LENGTH.name
        self.dynamic_sts_256_bits_supported = bool(value[0] & 0x01)
        self.provisioned_sts_256_bits_supported = bool(value[0] & 0x02)

    def __str__(self):
        return (
            f"{self.name}\n"
            "    256 bits key length for Dynamic STS: "
            f"{'Supported' if self.dynamic_sts_256_bits_supported else 'Not supported'}\n"
            "    256 bits key length for Provisioned STS: "
            f"{'Supported' if self.provisioned_sts_256_bits_supported else 'Not supported'}\n"
        )


class DtAnchorMax:
    def __init__(self, value):
        if SharedData.dt_anchor_supported:
            self.max_active_ranging_rounds = value[0] & 0x7F
        else:
            self.max_active_ranging_rounds = None

    def __str__(self):
        return (
            ""
            if self.max_active_ranging_rounds is None
            else f"Maximum number of active ranging rounds supported by DT-Anchor: {self.max_active_ranging_rounds}\n"
        )


class DtTagMax:
    def __init__(self, value):
        if SharedData.dt_tag_supported:
            self.dt_tag_max_active_rr = value[0] & 0xFF
        else:
            self.dt_tag_max_active_rr = None

    def __str__(self):
        return (
            ""
            if self.dt_tag_max_active_rr is None
            else f"Maximum number of active ranging rounds supported by DT-Tag: {self.dt_tag_max_active_rr}\n"
        )


class DtTagBlockSkipping:
    def __init__(self, value):
        if SharedData.dt_tag_supported:
            self.dt_tag_block_skipping = value[0] & 0xFF
        else:
            self.dt_tag_block_skipping = None

    def __str__(self):
        return (
            ""
            if self.dt_tag_block_skipping is None
            else f"DT-Tag block skipping: {'Supported' if self.dt_tag_block_skipping else 'Not supported'}\n"
        )


class MaxMessageSize:
    def __init__(self, value):
        self.integer_value = int.from_bytes(value, byteorder="little")

    def __str__(self):
        return f"\nMaximum size of UCI Data Messages the UWBS can receive: {self.integer_value}\n"


class MaxDataPacketPayload:
    def __init__(self, value):
        self.integer_value = int.from_bytes(value, byteorder="little")

    def __str__(self):
        return f"Maximum UCI Data Packet Payload Size the UWBS can receive: {self.integer_value}\n"


class UnsupportedCap:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

    def __str__(self):
        return f"Unsupported capability {hex(self.tag)} : {self.value.hex('.')}  "


caps = {
    CapsParameters.MAX_MESSAGE_SIZE: MaxMessageSize,
    CapsParameters.MAX_DATA_PACKET_PAYLOAD_SIZE: MaxDataPacketPayload,
    CapsParameters.FIRA_PHY_VERSION_RANGE: PhyFiraVersionRange,
    CapsParameters.FIRA_MAC_VERSION_RANGE: MacFiraVersionRange,
    CapsParameters.DEVICE_TYPE: DeviceType,
    CapsParameters.DEVICE_ROLES: DeviceRoles,
    CapsParameters.RANGING_METHOD: RangingMethod,
    CapsParameters.STS_CONFIG: StsConfig,
    CapsParameters.MULTI_NODE_MODE: MultiNodeMode,
    CapsParameters.RANGING_TIME_STRUCT: RangingTime,
    CapsParameters.SCHEDULE_MODE: ScheduleMode,
    CapsParameters.HOPPING_MODE: HoppingMode,
    CapsParameters.BLOCK_STRIDING: BlockStriding,
    CapsParameters.UWB_INITIATION_TIME: UwbInitTime,
    CapsParameters.CHANNELS: Channels,
    CapsParameters.RFRAME_CONFIG: RframeConfig,
    CapsParameters.CC_CONSTRAINT_LENGTH: CcConstraintLength,
    CapsParameters.BPRF_PARAMETER_SETS: BprfParameterSets,
    CapsParameters.HPRF_PARAMETER_SETS: HprfParameterSets,
    CapsParameters.AOA_SUPPORT: AoaSupport,
    CapsParameters.EXTENDED_MAC_ADDRESS: ExtendedMacAddress,
    CapsParameters.SESSION_KEY_LENGTH: SessionKeyLength,
    CapsParameters.DT_ANCHOR_MAX_ACTIVE_RR: DtAnchorMax,
    CapsParameters.DT_TAG_MAX_ACTIVE_RR: DtTagMax,
    CapsParameters.DT_TAG_BLOCK_SKIPPING: DtTagBlockSkipping,
}
