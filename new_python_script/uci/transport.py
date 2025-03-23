# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

import logging
from abc import ABCMeta, abstractmethod
from .utils import UciComStatus, UciComError

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
            raise ValueError(f"{cls} already registered")
        Factory.__transports__.append(cls)

    def unregister(cls):
        if cls not in Factory.__transports__:
            raise ValueError(f"{cls} not registered")
        Factory.__transports__.remove(cls)

    @staticmethod
    def get(callback, *args, **kwargs):
        port = kwargs["port"]

        for tr in Factory.__transports__:
            if tr.handle(port):
                return tr(callback, *args, **kwargs)

        raise UciComError(UciComStatus.UnknownPort, f'"{port}" is not supported')


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
