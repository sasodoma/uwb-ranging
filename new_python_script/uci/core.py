# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

import logging
import weakref
import queue

from . import transport
from .utils import UciComStatus, UciComError, DynIntEnum

logger = logging.getLogger(__name__)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s",
    datefmt="%H:%M:%S",
)


class MT(DynIntEnum):
    DataPacket = 0
    Command = 1
    Response = 2
    Notif = 3
    Unknown = 255


class PBF(DynIntEnum):
    Final = 0
    NextExpected = 1
    Unknown = 255


class DPF(DynIntEnum):
    DataMessageSnd = 1
    DataMessageRcv = 2
    RadarDataMessage = 15
    Unknown = 255


# Utility functions for arguments encoding/decoding


def get_length(defs, v):
    for value, length in defs:
        if value == v:
            return length

    raise ValueError("BadType")


def tvs_to_bytes(defs, tvs):
    payload = (len(tvs)).to_bytes(1, "little")
    for t, v in tvs:
        lengths = get_length(defs, t)

        payload += (t).to_bytes(1, "little")

        if isinstance(v, list):
            length = lengths[0] if isinstance(lengths, list) else lengths
            payload += (len(v) * length).to_bytes(1, "little")
            for s in v:
                payload += (s).to_bytes(length, "little")
        elif isinstance(v, dict):
            length = lengths[0]
            payload += (length).to_bytes(1, "little")
            for i, key in enumerate(v.keys()):
                payload += (v[key]).to_bytes(lengths[1][i], "little")
        else:
            if isinstance(lengths, list):
                length = lengths[1] if len(v) == 32 else lengths[0]
            else:
                length = lengths
            payload += (length).to_bytes(1, "little")
            if isinstance(v, bytes):
                if len(v) != length:
                    raise ValueError("BadLength")
                payload += v
            else:
                try:
                    payload += (v).to_bytes(length, "little")
                except Exception as e:
                    raise ValueError(f'Unable to set param "{t.name}" to  {v}: {e}.')

    return payload


def tlvs_from_bytes(enum_class, payload):
    res = []
    n = payload[0]
    p = 1

    for i in range(n):
        (t, l, v) = (payload[p], payload[p + 1], None)

        try:
            l_elem = get_length(enum_class.defs, t)
            if isinstance(l_elem, list):
                l_elem = l
        except (AttributeError, ValueError):
            l_elem = l
        p += 2

        if l_elem == l:
            v = (int).from_bytes(payload[p : p + l], "little")
        elif (l % l_elem) == 0:
            nb_elem = int(l / l_elem)
            v = []

            for i in range(nb_elem):
                v.append(
                    (int).from_bytes(
                        payload[p + i * l_elem : p + (i + 1) * l_elem], "little"
                    )
                )
        else:
            raise ValueError("BadLength")

        p += l

        try:
            res.append((enum_class(t), l_elem, v))
        except ValueError:
            res.append((t, l_elem, v))

    return res


def list_to_bytes(elems):
    payload = (len(elems)).to_bytes(1, "little")

    for e in elems:
        payload += (e).to_bytes(1, "little")

    return payload


def list_from_bytes(status_class, payload):
    res = []
    if len(payload) == 0:
        raise ValueError("Paylod is empty")

    number_ts_pairs = payload[0]

    # Check if number of key valued pairs equals payload size
    if 2 * number_ts_pairs != (len(payload) - 1):
        raise ValueError(
            f" Payload length from command, {number_ts_pairs}, "
            + f"is not the same as calculated length {(len(payload) - 1) / 2}"
        )
    for i in range(1, 2 * number_ts_pairs, 2):
        (t, s) = (payload[i], payload[i + 1])
        try:
            res.append((t, status_class(s)))
        except ValueError:
            res.append((t, s))

    return res


class Client:
    def __init__(self, *args, **kwargs):
        self.msg = None
        self.wq = queue.Queue()
        self.notif_handlers = kwargs.pop("notif_handlers", None)
        self.data_handlers = kwargs.pop("data_handlers", None)
        self.transport = weakref.ref(
            transport.Factory.get(
                weakref.WeakMethod(self.data_received), *args, **kwargs
            )
        )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        if hasattr(self, "transport"):
            if self.transport():
                self.transport().close()

    def set_handlers(self, handlers):
        self.notif_handlers = handlers

    def send_packet(self, mt, gid, oid, pbf, payload):
        header = bytearray([mt << 5 | pbf << 4 | gid, oid, 0, len(payload)])

        msg = header + bytearray(payload)

        logger.debug(f'send: {msg.hex(".")}')
        self.transport().write(msg)

    def data_received(self, data):
        logger.debug(f'data_recv: {data.hex(".")}')

        while len(data) > 0:
            header = data[0:4]
            mt = (header[0] & 0xE0) >> 5

            if mt == MT.DataPacket:
                payload_length = int.from_bytes(header[2:4], byteorder="little")
            else:
                payload_length = header[3]

            packet = bytearray(data[0 : 4 + payload_length])
            data = bytearray(data[4 + payload_length :])

            self.packet_received(packet)

    def packet_received(self, packet):
        logger.debug(f'packet_recv: {packet.hex(".")}')
        header = packet[0:4]
        payload = bytearray(packet[4:])

        mt = (header[0] & 0xE0) >> 5
        bpf = (header[0] & 0x10) >> 4
        gid = header[0] & 0x0F
        oid = header[1]

        # check msg
        if self.msg:
            if (mt, gid, oid) != self.msg[0:3]:
                raise UciComError(UciComStatus.ProtocolError, "Bad packet sequence")

            self.msg[3].extend(payload)
        else:
            self.msg = (mt, gid, oid, payload)

        if not bpf:
            # message is complete
            self.message_received()
            self.msg = None

    def send_message(self, mt, gid, oid, payload):
        total_len = len(payload)
        p = 0

        if mt.bit_length() > 3:
            raise UciComError(UciComStatus.ProtocolError, "mt is only 3 bits long")
        if gid.bit_length() > 4:
            raise UciComError(UciComStatus.ProtocolError, "gid is only 4 bits long")
        if oid.bit_length() > 6:
            raise UciComError(UciComStatus.ProtocolError, "oid is only 6 bits long")

        while True:
            pbf = 0
            n = total_len - p

            if n > 250:
                n = 250
                pbf = 1

            self.send_packet(mt, gid, oid, pbf, payload[p : p + n])
            p += n

            if p == total_len:
                break

    def message_received(self):
        (mt, gid, oid, payload) = self.msg

        if mt == MT.Notif:
            if self.notif_handlers and (gid, oid) in self.notif_handlers:
                try:
                    self.notif_handlers[(gid, oid)](payload)
                except Exception as e:
                    print(e)
                    logger.error(
                        f'Error: notif_handler "{(self.notif_handlers[(gid, oid)]).__qualname__}" @(gid={gid}, oid={oid}) \
                        raises: {e!r}'
                    )
            elif ("default", "default") in self.notif_handlers:
                try:
                    self.notif_handlers[("default", "default")](gid, oid, payload)
                except Exception as e:
                    logger.error(
                        f'Error: notif_handlers[("default","default")] raise: {e!r}'
                    )
            else:
                logger.info(f"notif: {gid}, {oid}: {payload.hex()}")
        elif mt == MT.Response:
            self.wq.put((gid, oid, payload))
        elif mt == MT.DataPacket:
            # Same bytes for GID (Control Message) and DPF (Data Message)
            dpf = gid

            if self.data_handlers and (dpf) in self.data_handlers:
                try:
                    self.data_handlers[(dpf)](payload)
                except Exception as e:
                    logger.error(
                        f'Error: data_handlers "{(self.data_handlers[(dpf)]).__qualname__}" @(dpf={dpf}) raises: {e!r}'
                    )
            elif "default" in self.data_handlers:
                try:
                    self.data_handlers["default"](payload)
                except Exception as e:
                    logger.error(
                        f'Error: notif_handlers[("default","default")] raise: {e!r}'
                    )
            else:
                logger.info(f'data: {dpf}: {payload.hex(".")}')

    def command(self, gid, oid, payload, timeout_delay=4):
        self.send_message(MT.Command, gid, oid, payload)

        try:
            (rgid, roid, payload) = self.wq.get(timeout=timeout_delay)
        except queue.Empty as exc:
            msg = f"No response from the device ({timeout_delay}s timeout)"
            raise UciComError(UciComStatus.TimeoutError, msg) from exc

        if (rgid, roid) != (gid, oid):
            raise UciComError(
                UciComStatus.ProtocolError,
                f"response ({rgid}, {roid}) does not match command ({gid}, {oid})",
            )

        return payload

    def send_data(self, payload):
        self.send_message(MT.DataPacket, DPF.DataMessageSnd, 0, payload)
