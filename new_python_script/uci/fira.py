# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

from . import fira_app
from . import fira_conf
from . import fira_msg
from . import fira_enums
from . import utils
from . import fira_cap

from colorama import Fore, Style, init

import logging
from . import core
from .utils import *

from .fira_app import *
from .fira_conf import *
from .fira_msg import *
from .fira_enums import *
from .fira_cap import *

__all__ = [
    "Client",
    "notification_default_handlers",
    "UciComError",
    "UciComStatus",
    "uci_codecs",
]
__all__.extend(fira_app.__all__)
__all__.extend(fira_conf.__all__)
__all__.extend(fira_msg.__all__)
__all__.extend(fira_enums.__all__)
__all__.extend(utils.__all__)
__all__.extend(fira_cap.__all__)

init()
logger = logging.getLogger()


# =============================================================================
# Helpers
# =============================================================================


def ts_from_bytes(enum_classes, payload):
    res = []
    n = payload[0]
    p = 1

    for i in range(n):
        (t, s) = (payload[p], payload[p + 1])
        p += 2
        res.append(((enum_classes[0])(t), (enum_classes[1])(s)))

    return res


# =============================================================================
# Client
# =============================================================================


class Client(ExtendableClass):
    pass


Client.extend(core.Client)


class Client_extension:
    def __init__(self, *args, **kwargs):
        handlers = notification_default_handlers
        handlers.update(kwargs.get("notif_handlers", {}))
        kwargs["notif_handlers"] = handlers

        self.data_handler = {"default": lambda sid, x: print(sid, x.hex("."))}
        self.data_handler.update(kwargs.get("data_handler", {}))

        self.mac_size = 2  # in bytes
        super().__init__(*args, **kwargs)

    def reset(self):
        payload = self.command(Gid.Core, OidCore.Reset, b"\x00")
        return Status((int).from_bytes(payload[0:1], "little"))

    def get_device_info(self):
        rtv = DeviceInfo(self.command(Gid.Core, OidCore.GetDeviceInfo, b""))
        return rtv.status, rtv

    def get_caps(self):
        rtv = Caps(self.command(Gid.Core, OidCore.GetCaps, b""))
        return rtv.status, rtv

    def get_ranging_count(self, sid):
        payload = sid.to_bytes(4, "little")
        payload = self.command(Gid.Ranging, OidRanging.GetCount, payload)
        rts = Status(int.from_bytes(payload[0:1], "little"))
        rtv = int.from_bytes(payload[1:5], "little") if rts == Status.Ok else None
        return rts, rtv

    def set_config(self, tvs):
        payload = core.tvs_to_bytes(Config.defs, tvs)

        payload = self.command(Gid.Core, OidCore.SetConfig, payload)

        return (
            Status((int).from_bytes(payload[0:1], "little")),
            core.list_from_bytes(Status, payload[1:]),
        )

    def get_config(self, params):
        payload = core.list_to_bytes(params)

        payload = self.command(Gid.Core, OidCore.GetConfig, payload)

        return (
            Status((int).from_bytes(payload[0:1], "little")),
            core.tlvs_from_bytes(Config, payload[1:]),
        )

    def get_time(self):
        """Get the uwb device time in us."""
        payload = self.command(Gid.Core, OidCore.GetTime, b"")

        return (
            Status((int).from_bytes(payload[0:1], "little")),
            (int).from_bytes(payload[1:9], "little"),
        )

    def session_init(self, sid, stype, data_handler=None):
        if data_handler:
            self.data_handler[sid] = data_handler
        payload = (sid).to_bytes(4, "little")
        payload += (stype).to_bytes(1, "little")

        session_data = SessionData(self.command(Gid.Session, OidSession.Init, payload))
        return session_data.status, session_data.session_handle

    def session_deinit(self, sid):
        if sid in self.data_handler:
            self.handler.pop(sid)
        payload = sid.to_bytes(4, "little")

        payload = self.command(Gid.Session, 1, payload)
        return Status((int).from_bytes(payload[0:1], "little"))

    def session_set_app_config(self, sid, params):
        payload = (sid).to_bytes(4, "little")

        payload += core.tvs_to_bytes(App.defs, params)

        payload = self.command(Gid.Session, OidSession.SetAppConfig, payload)
        b = Buffer(payload)
        status = Status(b.pop_uint(1))
        if status != Status.Ok:
            msg = ""
            n = b.pop_uint(1)
            if n != 0:
                msg = " Wrong configuration:\n"
            for i in range(n):
                p = b.pop_uint(1)
                try:
                    p_name = App(p).name
                except AttributeError:
                    p_name = "Unknown"
                p_str = f"{p_name} ({hex(p)}):"
                s = Status(b.pop_uint(1))
                msg += f"    {p_str:<35} {s.name}({s.value})\n"
            return (status, msg)
        else:
            return (
                status,
                "",
            )

    def session_send_data(self, sid, dest_address, data_sequence_number, data):
        payload = sid.to_bytes(4, "little")
        payload += dest_address.to_bytes(8, "little")
        payload += data_sequence_number.to_bytes(2, "little")
        payload += len(data).to_bytes(2, "little")
        payload += data
        self.send_data(payload)

    def session_get_app_config(self, sid, params):
        payload = (sid).to_bytes(4, "little")
        payload += core.list_to_bytes(params)

        payload = self.command(Gid.Session, OidSession.GetAppConfig, payload)

        return (
            Status((int).from_bytes(payload[0:1], "little")),
            core.tlvs_from_bytes(App, payload[1:]),
        )

    def session_get_conf(self, sid, params):
        """temp before UWBMQA-2536"""
        payload = (sid).to_bytes(4, "little")
        payload += core.list_to_bytes(params)

        payload = self.command(Gid.Session, OidSession.GetAppConfig, payload)

        b = Buffer(payload)
        status = Status(b.pop_uint(1))
        n = b.pop_uint(1)
        msg = ""
        for i in range(n):
            p = b.pop_uint(1)
            if p in vars(App).values():
                p_name = App(p).name
            else:
                p_name = "Unknown"
            p_str = f"{p_name} ({hex(p)}):"
            length = b.pop_uint(1)
            v = b.pop_uint(length)
            msg += f"    {p_str:<35} {hex(v)}\n"
        return (status, msg)

    def session_get_count(self):
        payload = self.command(Gid.Session, OidSession.GetCount, b"")

        return (
            Status((int).from_bytes(payload[0:1], "little")),
            (int).from_bytes(payload[1:2], "little"),
        )

    def session_get_state(self, sid):
        payload = (sid).to_bytes(4, "little")

        payload = self.command(Gid.Session, OidSession.GetState, payload)

        return (
            Status((int).from_bytes(payload[0:1], "little")),
            SessionState((int).from_bytes(payload[1:2], "little")),
        )

    def ranging_start(self, sid):
        payload = sid.to_bytes(4, "little")
        payload = self.command(Gid.Ranging, OidRanging.Start, payload)
        return Status((int).from_bytes(payload[0:1], "little"))

    def ranging_stop(self, sid):

        payload = sid.to_bytes(4, "little")
        payload = self.command(Gid.Ranging, OidRanging.Stop, payload)
        return Status((int).from_bytes(payload[0:1], "little"))

    def session_update_multicast_list(self, sid, action, controlee_list):
        """
        Dynamically update the multicast list of Controlees.
        Implement the SESSION_UPDATE_CONTROLLER_MULTICAST_LIST functionality.
        as described in Generic UCI 2.0.0_0.9r11 specification.
        controlee_list is a list with below format:
            [MacId_1, ssID_1, ssKey_1 ..., MacId_n, ssID_n, ssKey_n]
            with:
                Mac_Id_i : short address (Uint16)  of the newly added/removed Controlee
                ssID_i   : Controlee specific sub-session ID (Uint32) generated by the Application layer
                    may be set to 0 if action is delete
                ssKey_n  : 0/16/or 32 bytes long sub-session Key as a (0/16/or 32 bytes bytestream)
        Returns the status
        """
        n_controlee = len(controlee_list) // 3
        if (n_controlee * 3) != len(controlee_list):
            raise SyntaxError(
                f"session_update_multicast_list(): controlee_list syntax error. Got {controlee_list!r}"
            )
        payload = sid.to_bytes(4, "little")
        payload += action.to_bytes(1, "little")
        payload += n_controlee.to_bytes(1, "little")
        for i in range(n_controlee):
            payload += controlee_list[3 * i].to_bytes(2, "little")
            payload += controlee_list[3 * i + 1].to_bytes(4, "little")
            ssk = controlee_list[3 * i + 2]
            if (ssk != 0) and (ssk != b""):
                payload += ssk
        payload = self.command(Gid.Session, OidSession.UpdateMulticastList, payload)
        rtv = UpdateMulticastListResp(payload)
        return (
            rtv.status,
            rtv,
        )

    def session_update_dt_anchor_ranging_rounds(self, sid, round_list):
        """
        Implement the functionality to set DT anchor role and destination MAC addresses per round.

        For the provided Session Id, define the Anchor role per round and set the desired destination MAC addresses.
        round_list is a list of three elements with the following format:
        [(round_idx_1, role_1, [dest_mac_1_1, slots_1_1]) , ... (round_idx_n, role_n, dest_mac_n, slots_n)]
        with role_i = 1 if initiator else 0 if responder
        n is expected to be in 1 .. DT_ANCHOR_MAX_ACTIVE_RR

        dest_mac_list is a list of slot_spec :
        [ ( [(dest_mac_1_1, slots_1_1), ... (dest_mac_1_n, slots_1_n) )
        ...
        ( [(dest_mac_m_1, slots_m_1), ... (dest_mac_m_n, slots_m_n) ]
        In the above, for a given i, slots_i_j may be empty (all or none):
        The dest MAC related slot is then guessed using the position in the list.
        """
        payload = (sid).to_bytes(4, "little") + (len(round_list)).to_bytes(1, "little")
        for ranging_round in round_list:
            payload += ranging_round[0].to_bytes(1, "little")
            payload += ranging_round[1].to_bytes(1, "little")
            if ranging_round[1] == 1:
                n_dest = 0
                slots = []
                macs = b""
                is_slot_n_missing = False
                for mac_slot in ranging_round[2]:
                    n_dest += 1
                    mac, *slot = mac_slot
                    macs += mac.to_bytes(self.mac_size, "little")
                    if slot == []:
                        is_slot_n_missing = True
                    else:
                        slots.append(slot[0])
                if is_slot_n_missing:
                    logger.warning(
                        "Slot number is not defined for at least one of the responders.\n"
                        "Responders slots will be implicitly obtained from the order of the DST_MAC_ADDRESS list !"
                    )
                    slots = [0]
                else:
                    slots = [1] + slots
                payload += bytes([n_dest])
                payload += macs
                payload += bytes(slots)

        payload = self.command(Gid.Session, OidSession.SetAnchorRangingRounds, payload)

        status = Status((int).from_bytes(payload[0:1], "little"))
        if payload[1:1] == 0:
            rtv = []
            print(bytearray(rtv).hex("."))
        else:
            rtv = list(payload[2:])
            print(bytearray(rtv).hex("."))
        return status, rtv

    def session_set_dt_tag_activity(self, sid, active_round_list):
        """
        Implement the SESSION_UPDATE_DT_TAG_RANGING_ROUNDS functionality.
        For the provided Session Id, define the ranging Round index
        when the tag are required to listen to anchors.
        active_round_list is a list of round index

        Returns the status & possible list of Round_indexes that could not be activated
        """
        payload = (
            (sid).to_bytes(4, "little")
            + bytes([len(active_round_list)])
            + bytes(active_round_list)
        )
        payload = self.command(Gid.Session, OidSession.SetTagActivity, payload)
        status = Status((int).from_bytes(payload[0:1], "little"))
        if payload[1:1] == 0:
            rtv = []
        else:
            rtv = list(payload[2:])
        return status, rtv

    def test_config_set(self, sid, params):
        payload = TestConfigSetReq(session_handle=sid, params=params).to_bytes()
        rtv = TestConfigSetResp(self.command(Gid.Test, OidTest.ConfigSet, payload))
        return rtv.status, rtv

    def test_config_get(self, sid=TestModeSessionId, params=[]):
        payload = TestConfigGetReq(session_handle=0, params=params).to_bytes()
        rtv = TestConfigGetResp(self.command(Gid.Test, OidTest.ConfigGet, payload))
        return rtv.status, rtv

    def test_periodic_tx(self, payload):
        payload = self.command(Gid.Test, OidTest.PeriodicTx, payload)

        return Status((int).from_bytes(payload[0:1], "little"))

    def test_per_rx(self, payload):
        payload = self.command(Gid.Test, OidTest.PerRx, payload)

        return Status((int).from_bytes(payload[0:1], "little"))

    def test_rx(self):
        payload = self.command(Gid.Test, OidTest.Rx, b"")

        return Status((int).from_bytes(payload[0:1], "little"))

    def test_loopback(self, payload):
        payload = self.command(Gid.Test, OidTest.Loopback, payload)

        return Status((int).from_bytes(payload[0:1], "little"))

    def test_stop_session(self):
        payload = self.command(Gid.Test, OidTest.StopSession, b"")

        return Status((int).from_bytes(payload[0:1], "little"))

    def test_ss_twr(self):
        payload = self.command(Gid.Test, OidTest.SsTwr, b"")

        return Status((int).from_bytes(payload[0:1], "little"))


Client.extend(Client_extension)


# =============================================================================
# UCI Notification Handler
# =============================================================================


def show_device_state(payload):
    state = (int).from_bytes(payload[0:4], "little")
    print(f"{Fore.RED}Device -> {DeviceState(state).name}", end="")
    print(Style.RESET_ALL)


def show_session_state(payload):
    (sid, status, reason) = (
        (int).from_bytes(payload[0:4], "little"),
        (int).from_bytes(payload[4:5], "little"),
        (int).from_bytes(payload[5:6], "little"),
    )
    print(
        f"{Fore.GREEN}Session {sid} -> {SessionState(status).name} ({SessionStateChangeReason(reason).name})",
        end="",
    )
    print(Style.RESET_ALL)


# Below should be here;  time for UWBMQA-3594 ...
# ~ notification_default_handlers={
# ~ (Gid.Ranging, OidRanging.Start): lambda x: print(RangingData(x)),
# ~ (Gid.Test, OidTest.Loopback): lambda x: print(LoopBackTestOutput(x)),
# ~ (Gid.Test, OidTest.PeriodicTx): lambda x: print(PeriodicTxTestOutput(x)),
# ~ (Gid.Test, OidTest.SsTwr): lambda x: print(TwrTestOutput(x)),
# ~ (Gid.Test, OidTest.Rx): lambda x: print(RxTestOutput(x)),
# ~ (Gid.Test, OidTest.PerRx): lambda x: print(PerRxTestOutput(x)),
# ~ ('default','default'): lambda gid,oid, x: print(f'Warning: Unexpected notification: {NotImplementedData(gid, oid, x)}')
# ~ }

notification_default_handlers = {
    (Gid.Core, OidCore.DeviceStatus): show_device_state,
    (Gid.Session, OidSession.Status): show_session_state,
    (Gid.Session, OidSession.UpdateMulticastList): lambda x: print(
        MulticastControleeList(x)
    ),
    (Gid.Ranging, OidRanging.DataCredit): lambda x: print(SessionDataCredit(x)),
    (Gid.Ranging, OidRanging.DataTransferStatus): lambda x: print(
        SessionDataTransfertStatus(x)
    ),
    ("default", "default"): lambda gid, oid, x: print(
        f"Warning: Unexpected notification: {NotImplementedData(gid, oid, x)}"
    ),
}
