# Copyright (c) 2022 Qorvo US, Inc.

import logging
import os
import select
import threading
from abc import ABCMeta, abstractmethod

import serial
import serial.threaded
import serial.tools.list_ports

logger = logging.getLogger(__name__)


class Factory(ABCMeta):
    __transports__ = []

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(cls.mro()) > 2:
            cls.register()

    def __del__(cls):
        if len(cls.mro()) > 2:
            cls.unregister()

    def register(cls):
        if cls in Factory.__transports__:
            raise ValueError(f'{cls} already registered')
        Factory.__transports__.append(cls)

    def unregister(cls):
        if cls not in Factory.__transports__:
            raise ValueError(f'{cls} not registered')
        Factory.__transports__.remove(cls)

    @staticmethod
    def get(callback, *args, **kwargs):
        port = kwargs['port']

        for tr in Factory.__transports__:
            if tr.handle(port):
                return tr(callback, *args, **kwargs)

        raise ValueError(f'Unsupported port {port}')


class ITransport(metaclass=Factory):
    """Abstract class for Transport. To define a new transport one needs
    to create a class heriting from it."""
    @abstractmethod
    def __init__(self, callback, *args, **kwargs):
        """A transport must provide a callback parameter to __init__.  The
        callback is used to receive an UCI packet like: def
        callback(packet):
            pass
        """
        raise NotImplementedError

    @abstractmethod
    def write(self, packet):
        """Write a UCI packet using the transport."""
        raise NotImplementedError

    @abstractmethod
    def close(self):
        """Close the transport."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def handle(port):
        """Static method used by the transport to tell the factory it can
        handle 'port' transport."""
        raise NotImplementedError


class UartTransportProtocol(serial.threaded.Protocol):
    def __init__(self, callback):
        self.transport = None
        self.buffer = bytearray()
        self.cb = callback

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

            size = self.buffer[3]
            if n < 4 + size:
                return

            # got a packet
            self.cb(self.buffer[0:4+size])

            self.buffer = self.buffer[4+size:]

    def data_received(self, data):
        self.buffer.extend(data)

        self.check_data()


class UartTransport(serial.threaded.ReaderThread, ITransport):
    def __init__(self, callback, *args, **kwargs):
        # default to 115200
        if 'baudrate' not in kwargs:
            kwargs['baudrate'] = 115200
        if 'url' not in kwargs:
            kwargs['url'] = kwargs.pop('port')

        super().__init__(serial.serial_for_url(*args, **kwargs),
                         lambda: UartTransportProtocol(callback))

        self.start()
        self.connect()

    def close(self):
        super().close()

    @staticmethod
    def handle(port):
        if os.path.islink(port):
            # handle links in /dev
            port = os.path.realpath(port)

        return port in [x.device for x in serial.tools.list_ports.grep(port)]


class DevTransport(ITransport):
    def __init__(self, callback, *args, **kwargs):
        self.device = os.open(kwargs['port'], os.O_RDWR)
        self.cb = callback

        (self.rpipe, self.wpipe) = os.pipe()

        self.reader_thread = threading.Thread(
            target=self.reader_fn, daemon=True)
        self.reader_thread.start()

    def reader_fn(self):
        poller = select.poll()

        poller.register(self.rpipe, select.POLLIN)
        poller.register(self.device, select.POLLIN)

        while True:
            for (fd, _) in poller.poll():
                if fd == self.rpipe:
                    return

                packet = os.read(fd, 4 + 255)
                self.cb(packet)

    def write(self, packet):
        os.write(self.device, packet)

    def close(self):
        os.close(self.rpipe)
        os.close(self.wpipe)
        self.reader_thread.join()
        os.close(self.device)

    @staticmethod
    def handle(port):
        return port == '/dev/uci'


try:
    import uci.hsspi as hsspi
except ImportError:
    logger.warning('HSSPITransport not registered')
else:
    class HSSPITransport(hsspi.HsspiTransportProtocol, ITransport):
        def __init__(self, callback, *args, **kwargs):
            # default to 1000000
            if 'frequency' not in kwargs:
                kwargs['frequency'] = 1000000

            super().__init__(*args, **kwargs)

            self.set_msg_handler(callback)
            self.start()

        def write(self, packet):
            super().write(hsspi.UL_UCI, packet)

        def close(self):
            pass

        @staticmethod
        def handle(port):
            return port[:7] == 'ftdi://'
