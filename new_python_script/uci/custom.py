# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-1

"""
This library contains the part of Qorvo vendor UCI customization which
is incompatible with other customer-specific customization.
"""

# Do not put in __all__ your uci Client, new Gids, or other extension objects
# unless you want to block the addin mechanism.

import logging
from .utils import DynIntEnum
from .fira import *
from .custom_params import *

__all__ = ["OidUwbConfigManager"]

logger = logging.getLogger()

# =============================================================================
# Additional Qorvo Enum
# =============================================================================


class Gid_extension(DynIntEnum):
    UwbConfigManager = 0x0F


Gid.extend(Gid_extension)


class OidUwbConfigManager(DynIntEnum):
    Reset = 0x00


class Client_extension:
    def reset_calibration(self, timeout=4):
        payload = self.command(
            Gid.UwbConfigManager, OidUwbConfigManager.Reset, b"", timeout
        )
        return Status((int).from_bytes(payload[0:1], "little"))


Client.extend(Client_extension)

# =============================================================================
# UCI Data Customization
# =============================================================================


class DeviceInfo_custom:
    """
    This class is extending the CORE_GET_DEVICE_INFO_RSP data
    adding Qorvo-specific vendor fields.
    """

    def decode(self):
        self.decode_fira()
        self.decode_qorvo()
        if self.buffer.remaining_size() != 0:
            logger.warning(
                f"DeviceInfo: {self.buffer.remaining_size()} unhandled remaining bytes."
            )

    def decode_qorvo(self):
        self.qmf_version_major = "na"
        self.qmf_version_minor = "na"
        self.qmf_version_patch = "na"
        self.qmf_version_rc = "na"
        self.build_job = "na"
        self.oem_version_major = "na"
        self.oem_version_minor = "na"
        self.oem_version_revision = "na"
        self.soc_id = "na"
        self.device_id = "na"
        self.packaging_id = "na"
        self.vendor_size = 0
        b = self.buffer
        try:
            self.vendor_size = b.pop_uint(1)
            logger.debug(f"Vendor size: {self.vendor_size} bytes.")
            if self.vendor_size == 52:
                self.qmf_version_major = b.pop_uint(1)
                self.qmf_version_minor = b.pop_uint(1)
                self.qmf_version_patch = b.pop_uint(1)
                self.qmf_version_rc = b.pop_uint(1)
                self.build_job = b.pop_uint(8)
                self.oem_version_major = b.pop_uint(1)
                self.oem_version_minor = b.pop_uint(1)
                self.oem_version_revision = b.pop_uint(1)
            elif self.vendor_size != 0:
                self.qmf_version_major = b.pop_uint(1)
                self.qmf_version_minor = b.pop_uint(1)
                self.qmf_version_rc = b.pop_uint(1)
                self.build_job = b.pop_uint(8)
                self.oem_version_major = b.pop_uint(1)
                self.oem_version_minor = b.pop_uint(1)
                self.oem_version_revision = b.pop_uint(1)
            if b.remaining_size() != 0:
                self.soc_id = b.pop(32).hex()
                self.soc_id = str(self.soc_id).rstrip("0")
            if b.remaining_size() != 0:
                self.device_id = b.pop_uint(4)
                self.device_id = str(hex(self.device_id)[2:])
            if b.remaining_size() != 0:
                self.packaging_id = b.pop_uint(1)
        except ValueError as v:
            logger.warning(v)

    def __str__(self) -> str:
        rtv = super().__str__()

        if self.vendor_size == 52:
            qmf_version_str = f"{self.qmf_version_major}.{self.qmf_version_minor}.{self.qmf_version_patch}"
        else:
            qmf_version_str = f"{self.qmf_version_major}.{self.qmf_version_minor}"
        rtv += f"""
        QMF version:         {qmf_version_str}
        OEM version:         {self.oem_version_major}.{self.oem_version_minor}.{self.oem_version_revision}
        build job:           {self.build_job if self.build_job != 0 else 'na'}
        soc id:              {self.soc_id}
        device id:           {self.device_id}"""
        if "deca04" in self.device_id:
            rtv += f"""\n        packaging id:        {('sip' if self.packaging_id else 'soc')
                                                       if type(self.packaging_id) is int else 'na'}"""

        return rtv


DeviceInfo.extend(DeviceInfo_custom)

# =============================================================================
# UCI Message Extension
# =============================================================================

uci_codecs.update(
    {
        (MT.Command, Gid.UwbConfigManager, OidUwbConfigManager.Reset): default_codec(
            "Reset Device", no_data=True
        ),
        (MT.Response, Gid.UwbConfigManager, OidUwbConfigManager.Reset): default_codec(
            "Reset Device", status_only=True
        ),
    }
)
