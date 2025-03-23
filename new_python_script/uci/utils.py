# SPDX-FileCopyrightText: Copyright (c) 2024 Qorvo US, Inc.
# SPDX-License-Identifier: LicenseRef-QORVO-2

"""
This library is handling general data format and conversion
"""

import math
from enum import Enum, EnumMeta
import logging

__all__ = [
    "ExtendableClass",
    "DefaultEnum",
    "DynEnum",
    "DynIntEnum",
    "UciComError",
    "UciComStatus",
    "Buffer",
    "FP",
    "S4_11",
    "Int8",
    "Int16",
    "Int24",
    "Int32",
    "Int48",
    "Int64",
    "Uint8",
    "Uint16",
    "Uint24",
    "Uint32",
    "Uint48",
    "Uint64",
]

log = logging.getLogger()


class DynEnum(Enum):
    """Enum that may be expanded after initial creation."""

    @classmethod
    def as_list(cls):
        return cls._member_names_

    @classmethod
    def as_value_list(cls):
        return cls._member_map_.values()

    @classmethod
    def extend(cls, values):
        """
        Extend with another Enum
        or a dictionarry of key, value pairs
        """
        if type(values) is EnumMeta:
            for k in values._member_names_:
                if k in cls._member_names_:
                    raise KeyError(f"{k} already exists in {cls.__name__}")
                v = values._member_map_[k]
                if v in cls._member_map_.values():
                    raise KeyError(
                        f"{v} duplicate value in {cls.__name__}: {k} and {cls._value2member_map_[v].name}."
                    )
                cls._member_names_.append(k)
                cls._member_map_[k] = v
                cls._value2member_map_[v.value] = v
        else:
            for k, v in values.items():
                if k in cls._member_names_:
                    raise KeyError(f"{k} already exists in {cls.__name__}")
                if v in cls._member_map_.values():
                    raise KeyError(f"{v} duplicate value in {cls.__name__}")
                cls._member_names_.append(k)
                cls._member_map_[k] = v
                cls._value2member_map_[v] = k


class ExtendableClass:
    @classmethod
    def extend(cls, obj):
        """Add a base class"""
        try:
            cls._extension_.append(obj)
        except Exception:
            cls._extension_ = [obj]

    def __new__(cls, *args, **kwargs):
        # create the composed object:
        base_objects = cls._extension_.copy()
        base_objects.reverse()
        base_objects.append(cls)
        cls = type(cls.__name__, tuple(base_objects), {})
        return super().__new__(cls)


class DefaultEnum(Enum):
    """
    This enum is returning the default value unknown
    when requesting an undefined value
    """

    @classmethod
    def _missing_(cls, number):
        log.warning(f"Enum {cls.__name__} value {number} is unknown")
        return cls(cls.Unknown)

    pass


class DynIntEnum(int, DynEnum, DefaultEnum):
    """Integer Enum that may be expanded after initial creation.
    It also handles unknown value conversion (when set ...)
    """


class UciComStatus(DynIntEnum):
    Ok = 0
    UnknownPort = 1
    UnknownProtocol = 2
    TimeoutError = 3
    ProtocolError = 4
    Error = 9


class UciComError(Exception):
    """Raised when there is an error in the UCI protocol"""

    def __init__(self, n=UciComStatus.Error, message=""):
        self.n = n
        self.message = message

    def __str__(self):
        return f"UciComError.{self.n.name} ({hex(self.n)}): {self.message}"


class Buffer:
    """
    Handles poping bytes and converting from a byte stream.
    """

    def __init__(self, value: bytes):
        self.buffer = value
        self.i = 0

    def size(self):
        return len(self.buffer)

    def remaining_size(self):
        return len(self.buffer) - self.i

    def set_index(self, n):
        self.i = n

    def reset_parsing(self):
        self.i = 0

    def pop(self, n=1):
        """Return next data as a stream of bytes
        use -1 to return all the remaining data
        """
        if n == 0:
            return b""
        if n == -1:
            n = len(self.buffer) - self.i
        if n > len(self.buffer) - self.i:
            raise ValueError(f"Wanting {n} bytes. Got only {len(self.buffer)-self.i}")
        v = self.buffer[self.i : self.i + n]
        self.i += n
        return v

    def pop_float(self, is_signed=False, n_int=8, n_fract=0):
        n = (n_int + n_fract + (1 if is_signed else 0)) // 8
        return FP(self.pop(n), is_signed, n_int, n_fract).as_float()

    def pop_uint(self, n):
        return int.from_bytes(self.pop(n), byteorder="little", signed=False)

    def pop_int(self, n):
        return int.from_bytes(self.pop(n), byteorder="little", signed=True)

    def pop_str(self, n):
        return str(self.pop(n), "UTF-8")

    def pop_reverse(self, n=2):
        v = self.pop(n)
        v = reversed(v)
        return bytes(v)


class FP:
    """
    Represents a Fixed Point type.

    Built from a float, integer or bytes value
    At build, handle spec errors: sign, overflow, spec multiple of 8 bits.

    Warning regarding the variable type used to build the fixed-point value:
    FP(30.0, a, b, c) != FP(30, a, b, c)
    - FP(<int>, a, b, c)   : the int is expected to be already a fixed-point representation
    - FP(<float>, a, b, c) : the float will be converted to the provided fixed-point spec.
    In other words:
        FP(30,   a, b, c).as_int()   != int(30)
        FP(30,   a, b, c).as_float() != float(30)
        FP(30.0, a, b, c).as_int()   == int(30)
        FP(30.0, a, b, c).as_float() == float(30)

    """

    def __init__(
        self,
        value=0,
        is_signed=False,
        n_int=8,
        n_fract=0,
        ignore_nbits_error=False,
        byteorder="little",
    ):
        self.is_signed = is_signed
        self.n_int = n_int
        self.n_fract = n_fract
        self.value = bytearray()  # Internal repr: little-endian byte stream
        self.nbits = n_int + n_fract + (1 if is_signed else 0)
        if not ignore_nbits_error and ((self.nbits % 8) != 0):
            raise ValueError(f'"{self.nbits}" bits not a multiple of 8.')
        if isinstance(value, int):
            self.from_int(value, byteorder)
        elif isinstance(value, bytes) or isinstance(value, bytearray):
            self.from_bytes(value, byteorder)
        elif isinstance(value, float):
            self.from_float(value, byteorder)
        else:
            raise ValueError(
                f'Cannot build a fixed point from "{value!r}". Expecting a float, int, or bytes.'
            )

    def from_float(self, value, byteorder="little"):
        """
        build from a natural (float) value
        """
        if (not self.is_signed) and (value < 0):
            raise ValueError(f'"{value}": negative value for unsigned int!')
        if value > ((1 << self.n_int) - 1):
            raise ValueError(f'"{value}": Overflow error.')
        v = round(value * (1 << self.n_fract))
        self.value = v.to_bytes(
            math.ceil(self.nbits / 8), byteorder=byteorder, signed=self.is_signed
        )
        return self

    def as_float(self):
        """
        Return a (natural) float from the internal representation.
        """
        v = int.from_bytes(self.value, byteorder="little", signed=self.is_signed)
        return v / (1 << self.n_fract)

    def from_int(self, value, byteorder="little"):
        """
        build from an integer representation of a fixed point
        """
        if value < 0:
            raise ValueError(
                f'Provided value is expected to be positive (got "{value}")!'
            )
        self.value = value.to_bytes(
            math.ceil(self.nbits / 8), byteorder=byteorder, signed=False
        )
        return self

    def as_int(self):
        """
        Return as a (fixed point coded) integer
        """
        return int.from_bytes(self.value, byteorder="little", signed=True)

    def as_uint(self):
        """
        Return as a (fixed point coded) unsigned integer
        """
        return int.from_bytes(self.value, byteorder="little", signed=False)

    def to_bytes(self, length=-1, byteorder="little"):
        """
        Return as a byte stream.
        length == -1 : the default length is used.
        """
        if byteorder == "little":
            v = self.value
        else:
            v = self.value[::-1]
        if length != -1:
            b = b"\x00" if self.as_float() >= 0 else b"\xff"
            if byteorder == "little":
                v = v + b * (length - len(v))
            else:
                v = b * (length - len(v)) + v
        return v

    def from_bytes(self, value: bytes, byteorder="little"):
        """
        Build from a byte stream.
        """
        if len(value) * 8 != self.nbits:
            raise ValueError(
                f"Byte stream is expected to be {self.nbits} bits long. Got {len(value)*4} bits"
            )
        if byteorder == "little":
            self.value = value
        else:
            self.value = self.value[::-1]
        self.value = value
        return self

    def as_hex(self):
        """
        Return as a (fixed point coded) hexadecimal int.
        """
        return "0x" + self.to_bytes(byteorder="big").hex()

    def __str__(self):
        return str(self.as_float())

    def __repr__(self):
        return f"FP({self.__str__()},{1 if self.is_signed else 0},{self.n_int},{self.n_fract})"


class Integer:
    """
    Represents an Integer Type.
    Built from a  (hex, octal, orbinary) integer, a byte string or bytes value.
    Warning regarding the variable type used to build the Integer value:
    Integer(-2,     1, is_signed=true)  ok (-2 == b'\xfe)
    Integer(254,    1, is_signed=true)  ko: will raise an overflow error
    Integer(0xfe,   1, is_signed=true)  ko: will raise an overflow error (0xfe == 254)
    Integer('0xfe',   1, is_signed=true)  ok (-2 == b'\xfe)
    Integer(b'\xfe, 1, is_signed=true)  ok (-2 == b'\xfe)
    Integer(255,    1, is_signed=false) ok
    Integer('0b11111111', 1, is_signed=true)  ko (-2 == 0xff)
    At build, handle spec errors: sign, overflow, etc...
    """

    def __init__(self, value=0, n_bytes=1, is_signed=False):
        self.is_signed = is_signed
        self.n_bytes = n_bytes
        if is_signed:
            self.min = -(2 ** (8 * n_bytes - 1))
            self.max = 2 ** (8 * n_bytes - 1) - 1
        else:
            self.min = 0
            self.max = 2 ** (8 * n_bytes) - 1
        self.set(value)

    def set(self, value):
        if isinstance(value, int):  # Natural format
            self.value = value  # Internal repr: integer
        elif isinstance(value, str):  # Byte format in 'natural' endian (MSB first)
            # Handle possible byte values in different bases
            # with signed handling
            try:
                value_int = value.replace(" ", "").replace(":", "").replace(".", "")
                if value_int.startswith("0"):
                    value_int = eval(value_int)
                else:
                    value_int = eval("0x" + value_int)
            except Exception:
                raise ValueError(f"{value}: unexpected value for Integer.")
            try:
                value_byte = value_int.to_bytes(self.n_bytes, "little", signed=False)
                self.value = int.from_bytes(value_byte, "little", signed=self.is_signed)
            except Exception:
                raise ValueError(
                    f"Overflow Error: unable to encode {value!r} on a {self.n_bytes} bytes"
                    f'{" signed" if self.is_signed else "unsigned"} Integer.'
                )
        elif isinstance(value, bytes) or isinstance(
            value, bytearray
        ):  # Bytestream format
            self.value = int.from_bytes(value, "little", signed=self.is_signed)
        else:
            raise ValueError(
                f"Integer is expecting an integer representation. Got {value}."
            )
        if not (self.min <= self.value <= self.max):
            raise ValueError(
                f"Overflow Error: unable to encode {value!r} on a {self.n_bytes} bytes"
                f'{" signed" if self.is_signed else "unsigned"} Integer.'
            )

    def from_bytes(self, value: bytes, byteorder="little"):
        self.set(int.from_bytes(value, byteorder, signed=self.is_signed))
        return self

    def to_bytes(self, length=-1, byteorder="little"):
        """
        Return as a byte stream.
        length == -1 : the default length is used.
        """
        if length == -1:
            length = self.n_bytes
        if length > self.n_bytes:
            raise ValueError(
                f"Unable to convert a {self.n_bytes}  bytes Integer to a {length}  bytes Bytestream."
            )
        return self.value.to_bytes(
            length=length, byteorder=byteorder, signed=self.is_signed
        )

    def __hex__(self):
        return self.to_bytes().hex(".")

    def as_hex(self, sep="."):
        return self.to_bytes().hex(sep)

    def __len__(self):
        return self.n_bytes

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f'Integer({self.__str__()}, n_bytes={self.n_bytes}, is_signed={"True" if self.is_signed else "False"})'


class Int8(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=1, is_signed=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Int16(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=2, is_signed=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Int24(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=3, is_signed=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Int32(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=4, is_signed=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Int48(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=6, is_signed=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Int64(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=8, is_signed=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Uint8(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=1, is_signed=False)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Uint16(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=2, is_signed=False)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Uint24(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=3, is_signed=False)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Uint32(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=4, is_signed=False)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Uint48(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=6, is_signed=False)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class Uint64(Integer):
    def __init__(self, value=0):
        super().__init__(value, n_bytes=8, is_signed=False)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__str__()})"


class S4_11(FP):
    """
    2 bytes S4,11 fixed point integer.
    """

    def __len__(self):
        return 2

    def __init__(self, value=0):
        FP.__init__(self, value, True, 4, 11)

    def __repr__(self):
        return f"S4_11({self.__str__()})"


if __name__ == "__main__":
    pass
