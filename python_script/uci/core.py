# Copyright (c) 2021 Qorvo US, Inc.

import logging
import queue

import uci.transport

logger = logging.getLogger(__name__)

# Utility functions for arguments encoding/decoding


def to_str(packet):
    return ''.join([format(x, '02x') for x in packet])


def get_length(defs, v):
    for (value, length) in defs:
        if value == v:
            return length

    raise ValueError('BadType')


def tvs_to_bytes(defs, tvs):
    payload = (len(tvs)).to_bytes(1, 'little')

    for (t, v) in tvs:
        length = get_length(defs, t)

        payload += (t).to_bytes(1, 'little')

        if type(v) == list:
            payload += (len(v) * length).to_bytes(1, 'little')
            for s in v:
                payload += (s).to_bytes(length, 'little')
        else:
            payload += (length).to_bytes(1, 'little')
            payload += (v).to_bytes(length, 'little')

    return payload


def tlvs_from_bytes(enum_class, payload):
    res = []
    n = payload[0]
    p = 1

    for i in range(n):
        (t, l, v) = (payload[p], payload[p+1], None)

        try:
            l_elem = get_length(enum_class.defs, t)
        except (AttributeError, ValueError):
            l_elem = l
        p += 2

        if l_elem == l:
            v = (int).from_bytes(payload[p:p + l], 'little')
        elif (l % l_elem) == 0:
            nb_elem = int(l / l_elem)
            v = []

            for i in range(nb_elem):
                v.append((int).from_bytes(
                    payload[p + i * l_elem:p + (i + 1) * l_elem], 'little'))
        else:
            raise ValueError('BadLength')

        p += l

        try:
            res.append((enum_class(t), l_elem, v))
        except ValueError:
            res.append((t, l_elem, v))

    return res


def list_to_bytes(elems):
    payload = (len(elems)).to_bytes(1, 'little')

    for e in elems:
        payload += (e).to_bytes(1, 'little')

    return payload


def list_from_bytes(status_class, payload):
    res = []
    if len(payload) == 0:
        raise ValueError("Paylod is empty")

    number_ts_pairs = payload[0]

    # Check if number of key valued pairs equals payload size
    if (2*number_ts_pairs != (len(payload) - 1)):
        raise ValueError(
            f" Payload length from command, {number_ts_pairs}, " +
            f"is not the same as calculated length {(len(payload) - 1) / 2}")
    for i in range(1, 2 * number_ts_pairs, 2):
        (t, s) = (payload[i], payload[i+1])
        try:
            res.append((t, status_class(s)))
        except ValueError:
            res.append((t, s))

    return res


class ProtocolError(Exception):
    """Raised when there is an error in the UCI protocol"""
    pass


class Client():
    def __init__(self, *args, **kwargs):
        self.msg = None
        self.wq = queue.Queue()
        self.notif_handlers = kwargs.pop('notif_handlers', None)

        self.transport = uci.transport.Factory.get(
            self.packet_received, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.transport.close()

    def set_handlers(self, handlers):
        self.notif_handlers = handlers

    def send_packet(self, mt, gid, oid, pbf, payload):
        header = bytearray([mt << 5 | pbf << 4 | gid, oid, 0, len(payload)])
        msg = header + bytearray(payload)

        logger.debug(f'send: {to_str(msg)}')

        self.transport.write(msg)

    def packet_received(self, packet):
        logger.debug(f'recv: {to_str(packet)}')

        header = packet[0:4]
        payload = bytearray(packet[4:])

        mt = (header[0] & 0xe0) >> 5
        bpf = (header[0] & 0x10) >> 4
        gid = (header[0] & 0x0f)
        oid = header[1]

        # check msg
        if self.msg:
            if (mt, gid, oid) != self.msg[0:3]:
                raise ProtocolError('Bad packet sequence')

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
            raise ProtocolError('mt is only 3 bits long')
        if gid.bit_length() > 4:
            raise ProtocolError('gid is only 4 bits long')
        if oid.bit_length() > 6:
            raise ProtocolError('oid is only 6 bits long')

        while True:
            pbf = 0
            n = total_len - p

            if n > 255:
                n = 255
                pbf = 1

            self.send_packet(mt, gid, oid, pbf, payload[p:p + n])
            p += n

            if p == total_len:
                break

    def message_received(self):
        (mt, gid, oid, payload) = self.msg

        if mt == 3:
            if self.notif_handlers and (gid, oid) in self.notif_handlers:
                try:
                    self.notif_handlers[(gid, oid)](payload)
                except Exception as e:
                    logger.error(f'notif_handlers[({gid}, {oid})] raise: {e}')
            else:
                logger.info(
                    f'notif: {gid}, {oid}: {to_str(payload)}')
        elif mt == 2:
            self.wq.put((gid, oid, payload))

    def command(self, gid, oid, payload):
        self.send_message(1, gid, oid, payload)

        try:
            (rgid, roid, payload) = self.wq.get(timeout=2)
        except queue.Empty as exc:
            msg = 'No response from the device (2s timeout)'
            logger.critical(msg)
            raise ProtocolError(msg) from exc

        if (rgid, roid) != (gid, oid):
            raise ProtocolError('response does not match command (gid, oid)')

        return payload
