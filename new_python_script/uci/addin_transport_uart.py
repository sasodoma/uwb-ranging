# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

# Do not put in __all__ your uci Client, new Gids, or other extension objects
# unless you want to block the addin mechanism.

__all__ = []

import os
import serial
import serial.threaded
import serial.tools.list_ports

from .transport import ITransport, logger


class UartTransportProtocol(serial.threaded.Protocol):
    def __init__(self, callback):
        self.transport = None
        self.buffer = bytearray()
        self.cb = callback
        self.is_synchronized = False

    def connection_made(self, tr):
        self.transport = tr

    def connection_lost(self, exc):
        self.transport = None
        self.buffer.clear()

    def check_data(self):
        while True:
            n = len(self.buffer)
            if n < 4:
                return

            mt = (self.buffer[0] & 0xE0) >> 5

            if mt in [0b001, 0b010, 0b011]:
                # Control Packet
                size = self.buffer[3]
            elif mt in [0b000]:
                # Data Packet
                size = self.buffer[2] | self.buffer[3] << 8
            elif mt in [0b100, 0b101]:
                # Control message format for testing
                size = self.buffer[2] | self.buffer[3] << 8
            else:
                # Error -> flush data
                self.buffer = bytearray()
                size = 0
                return

            if n < 4 + size:
                return

            # got a packet
            self.cb()(self.buffer[0 : 4 + size])

            self.buffer = self.buffer[4 + size :]

    def data_received(self, data):
        # logger.debug(f'recv bytes : {data.hex(".")}')
        if not self.is_synchronized:
            # Just arriving in the com!
            if (data[0] & 0xF0) >> 4 in [4, 6, 5, 7]:
                self.is_synchronized = True
            else:
                # We are in the middle of a byte stream...
                logger.debug(f'recv bytes purged: {data.hex(".")}')
                data = b""
        self.buffer.extend(data)

        self.check_data()


class UartTransport(serial.threaded.ReaderThread, ITransport):
    def __init__(self, callback, *args, **kwargs):
        # default to 115200
        if "baudrate" not in kwargs:
            kwargs["baudrate"] = 115200
        if kwargs["port"].startswith("uart:"):
            kwargs["port"] = kwargs["port"][5:]
        if "url" not in kwargs:
            kwargs["url"] = kwargs.pop("port")

        super().__init__(
            serial.serial_for_url(*args, **kwargs),
            lambda: UartTransportProtocol(callback),
        )

        self.start()
        self.connect()

    def __del__(self):
        if os.name != "nt":
            self.serial.cancel_read()
            self.close()

    @staticmethod
    def handle(port):
        if os.path.islink(port):
            # handle links in /dev
            port = os.path.realpath(port)

        return port.startswith("uart:") or port in [
            x.device for x in serial.tools.list_ports.grep(port)
        ]
