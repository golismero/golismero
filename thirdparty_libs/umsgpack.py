# u-msgpack-python v1.5 - vsergeev at gmail
#
# u-msgpack-python is a lightweight MessagePack serializer and deserializer
# module, compatible with both Python 2 and 3, as well CPython and PyPy
# implementations of Python. u-msgpack-python is fully compliant with the
# latest MessagePack specification.com/msgpack/msgpack/blob/master/spec.md). In
# particular, it supports the new binary, UTF-8 string, and application ext
# types.
#

import struct
import collections
import sys

################################################################################

# Extension type for application code
class Ext:
    def __init__(self, type, data):
        # Application ext type should be 0 <= type <= 127
        if not isinstance(type, int) or not (type >= 0 and type <= 127):
            raise TypeError("ext type out of range")
        # Check data is type bytes
        elif sys.version_info[0] == 3 and not isinstance(data, bytes):
            raise TypeError("ext data is not type \'bytes\'")
        elif sys.version_info[0] == 2 and not isinstance(data, str):
            raise TypeError("ext data is not type \'str\'")
        self.type = type
        self.data = data

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.type == other.type and
                self.data == other.data)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        s = "Ext Object\n"
        s += "   Type: %02x\n" % self.type
        s += "   Data: "
        for i in range(len(self.data)):
            if isinstance(self.data[i], int):
                s += "%02x " % (self.data[i])
            else:
                s += "%02x " % ord(self.data[i])
            if i == 16-1:
                break
        if len(self.data) > 16:
            s += "..."
        return s

################################################################################

# Base Exception classes
class PackException(Exception): pass
class UnpackException(Exception): pass

# Packing error: Object type not supported for packing.
class UnsupportedTypeException(PackException): pass

# Unpacking error: Insufficient data to unpack encoded object.
class InsufficientDataException(UnpackException): pass
# Unpacking error: Invalid string (not UTF-8) encountered.
class InvalidStringException(UnpackException): pass
# Unpacking error: Reserved code encountered.
class ReservedCodeException(UnpackException): pass
# Unpacking error: Unhashable key encountered during map unpacking.
class KeyNotPrimitiveException(UnpackException): pass
# Unpacking error: Duplicate key encountered during map unpacking.
class KeyDuplicateException(UnpackException): pass

################################################################################

# Exported functions and variables set in __init()
packb = None
unpackb = None
compatibility = False

################################################################################

# You may notice struct.pack("B", x) instead of the simpler chr(x) in the code
# below. This is to allow for seamless Python 2 and 3 compatibility, as chr(x)
# has a str return type instead of bytes in Python 3, and struct.pack(...) has
# the right return type in both versions.

def _pack_integer(x):
    if x < 0:
        if x >= -32:
            return struct.pack("b", x)
        elif x >= -2**(8-1):
            return b"\xd0" + struct.pack("b", x)
        elif x >= -2**(16-1):
            return b"\xd1" + struct.pack(">h", x)
        elif x >= -2**(32-1):
            return b"\xd2" + struct.pack(">i", x)
        elif x >= -2**(64-1):
            return b"\xd3" + struct.pack(">q", x)
        else:
            raise UnsupportedTypeException("huge signed int")
    else:
        if x <= 127:
            return struct.pack("B", x)
        elif x <= 2**8-1:
            return b"\xcc" + struct.pack("B", x)
        elif x <= 2**16-1:
            return b"\xcd" + struct.pack(">H", x)
        elif x <= 2**32-1:
            return b"\xce" + struct.pack(">I", x)
        elif x <= 2**64-1:
            return b"\xcf" + struct.pack(">Q", x)
        else:
            raise UnsupportedTypeException("huge unsigned int")

def _pack_nil(x):
    return b"\xc0"

def _pack_boolean(x):
    return b"\xc3" if x else b"\xc2"

def _pack_float(x):
    if _float_size == 64:
        return b"\xcb" + struct.pack(">d", x)
    else:
        return b"\xca" + struct.pack(">f", x)

def _pack_string(x):
    if len(x) <= 31:
        return struct.pack("B", 0xa0 | len(x)) + x.encode('utf-8')
    elif len(x) <= 2**8-1:
        return b"\xd9" + struct.pack("B", len(x)) + x.encode('utf-8')
    elif len(x) <= 2**16-1:
        return b"\xda" + struct.pack(">H", len(x)) + x.encode('utf-8')
    elif len(x) <= 2**32-1:
        return b"\xdb" + struct.pack(">I", len(x)) + x.encode('utf-8')
    else:
        raise UnsupportedTypeException("huge string")

def _pack_binary(x):
    if len(x) <= 2**8-1:
        return b"\xc4" + struct.pack("B", len(x)) + x
    elif len(x) <= 2**16-1:
        return b"\xc5" + struct.pack(">H", len(x)) + x
    elif len(x) <= 2**32-1:
        return b"\xc6" + struct.pack(">I", len(x)) + x
    else:
        raise UnsupportedTypeException("huge binary string")

def _pack_oldspec_raw(x):
    if len(x) <= 31:
        return struct.pack("B", 0xa0 | len(x)) + x
    elif len(x) <= 2**16-1:
        return b"\xda" + struct.pack(">H", len(x)) + x
    elif len(x) <= 2**32-1:
        return b"\xdb" + struct.pack(">I", len(x)) + x
    else:
        raise UnsupportedTypeException("huge raw string")

def _pack_ext(x):
    if len(x.data) == 1:
        return b"\xd4" + struct.pack("B", x.type & 0xff) + x.data
    elif len(x.data) == 2:
        return b"\xd5" + struct.pack("B", x.type & 0xff) + x.data
    elif len(x.data) == 4:
        return b"\xd6" + struct.pack("B", x.type & 0xff) + x.data
    elif len(x.data) == 8:
        return b"\xd7" + struct.pack("B", x.type & 0xff) + x.data
    elif len(x.data) == 16:
        return b"\xd8" + struct.pack("B", x.type & 0xff) + x.data
    elif len(x.data) <= 2**8-1:
        return b"\xc7" + struct.pack("BB", len(x.data), x.type & 0xff) + x.data
    elif len(x.data) <= 2**16-1:
        return b"\xc8" + struct.pack(">HB", len(x.data), x.type & 0xff) + x.data
    elif len(x.data) <= 2**32-1:
        return b"\xc9" + struct.pack(">IB", len(x.data), x.type & 0xff) + x.data
    else:
        raise UnsupportedTypeException("huge ext data")

def _pack_array(x):
    if len(x) <= 15:
        s = struct.pack("B", 0x90 | len(x))
    elif len(x) <= 2**16-1:
        s = b"\xdc" + struct.pack(">H", len(x))
    elif len(x) <= 2**32-1:
        s = b"\xdd" + struct.pack(">I", len(x))
    else:
        raise UnsupportedTypeException("huge array")

    for e in x:
        s += packb(e)

    return s

def _pack_map(x):
    if len(x) <= 15:
        s = struct.pack("B", 0x80 | len(x))
    elif len(x) <= 2**16-1:
        s = b"\xde" + struct.pack(">H", len(x))
    elif len(x) <= 2**32-1:
        s = b"\xdf" + struct.pack(">I", len(x))
    else:
        raise UnsupportedTypeException("huge array")

    for k,v in x.items():
        s += packb(k)
        s += packb(v)

    return s

# Pack for Python 2, with 'unicode' type, 'str' type, and 'long' type
def _packb2(x):
    global compatibility

    if x is None:
        return _pack_nil(x)
    elif isinstance(x, bool):
        return _pack_boolean(x)
    elif isinstance(x, int) or isinstance(x, long):
        return _pack_integer(x)
    elif isinstance(x, float):
        return _pack_float(x)
    elif compatibility and isinstance(x, unicode):
        return _pack_oldspec_raw(bytes(x))
    elif compatibility and isinstance(x, bytes):
        return _pack_oldspec_raw(x)
    elif isinstance(x, unicode):
        return _pack_string(x)
    elif isinstance(x, str):
        return _pack_binary(x)
    elif isinstance(x, list) or isinstance(x, tuple):
        return _pack_array(x)
    elif isinstance(x, dict):
        return _pack_map(x)
    elif isinstance(x, Ext):
        return _pack_ext(x)
    else:
        raise UnsupportedTypeException("unsupported type: %s" % str(type(x)))

# Pack for Python 3, with unicode 'str' type, 'bytes' type, and no 'long' type
def _packb3(x):
    global compatibility

    if x is None:
        return _pack_nil(x)
    elif isinstance(x, bool):
        return _pack_boolean(x)
    elif isinstance(x, int):
        return _pack_integer(x)
    elif isinstance(x, float):
        return _pack_float(x)
    elif compatibility and isinstance(x, str):
        return _pack_oldspec_raw(x.encode('utf-8'))
    elif compatibility and isinstance(x, bytes):
        return _pack_oldspec_raw(x)
    elif isinstance(x, str):
        return _pack_string(x)
    elif isinstance(x, bytes):
        return _pack_binary(x)
    elif isinstance(x, list) or isinstance(x, tuple):
        return _pack_array(x)
    elif isinstance(x, dict):
        return _pack_map(x)
    elif isinstance(x, Ext):
        return _pack_ext(x)
    else:
        raise UnsupportedTypeException("unsupported type: %s" % str(type(x)))

################################################################################

def _unpack_integer(code, read_fn):
    if (ord(code) & 0xe0) == 0xe0:
        return struct.unpack("b", code)[0]
    elif code == b'\xd0':
        return struct.unpack("b", read_fn(1))[0]
    elif code == b'\xd1':
        return struct.unpack(">h", read_fn(2))[0]
    elif code == b'\xd2':
        return struct.unpack(">i", read_fn(4))[0]
    elif code == b'\xd3':
        return struct.unpack(">q", read_fn(8))[0]
    elif (ord(code) & 0x80) == 0x00:
        return struct.unpack("B", code)[0]
    elif code == b'\xcc':
        return struct.unpack("B", read_fn(1))[0]
    elif code == b'\xcd':
        return struct.unpack(">H", read_fn(2))[0]
    elif code == b'\xce':
        return struct.unpack(">I", read_fn(4))[0]
    elif code == b'\xcf':
        return struct.unpack(">Q", read_fn(8))[0]
    raise Exception("logic error, not int: 0x%02x" % ord(code))

def _unpack_reserved(code, read_fn):
    if code == b'\xc1':
        raise ReservedCodeException("encountered reserved code: 0x%02x" % ord(code))
    raise Exception("logic error, not reserved code: 0x%02x" % ord(code))

def _unpack_nil(code, read_fn):
    if code == b'\xc0':
        return None
    raise Exception("logic error, not nil: 0x%02x" % ord(code))

def _unpack_boolean(code, read_fn):
    if code == b'\xc2':
        return False
    elif code == b'\xc3':
        return True
    raise Exception("logic error, not boolean: 0x%02x" % ord(code))

def _unpack_float(code, read_fn):
    if code == b'\xca':
        return struct.unpack(">f", read_fn(4))[0]
    elif code == b'\xcb':
        return struct.unpack(">d", read_fn(8))[0]
    raise Exception("logic error, not float: 0x%02x" % ord(code))

def _unpack_string(code, read_fn):
    if (ord(code) & 0xe0) == 0xa0:
        length = ord(code) & ~0xe0
    elif code == b'\xd9':
        length = struct.unpack("B", read_fn(1))[0]
    elif code == b'\xda':
        length = struct.unpack(">H", read_fn(2))[0]
    elif code == b'\xdb':
        length = struct.unpack(">I", read_fn(4))[0]
    else:
        raise Exception("logic error, not string: 0x%02x" % ord(code))

    # Always return raw bytes in compatibility mode
    global compatibility
    if compatibility:
        return read_fn(length)

    try:
        return bytes.decode(read_fn(length), 'utf-8')
    except UnicodeDecodeError:
        raise InvalidStringException("unpacked string is not utf-8")

def _unpack_binary(code, read_fn):
    if code == b'\xc4':
        length = struct.unpack("B", read_fn(1))[0]
    elif code == b'\xc5':
        length = struct.unpack(">H", read_fn(2))[0]
    elif code == b'\xc6':
        length = struct.unpack(">I", read_fn(4))[0]
    else:
        raise Exception("logic error, not binary: 0x%02x" % ord(code))

    return read_fn(length)

def _unpack_ext(code, read_fn):
    if code == b'\xd4':
        length = 1
    elif code == b'\xd5':
        length = 2
    elif code == b'\xd6':
        length = 4
    elif code == b'\xd7':
        length = 8
    elif code == b'\xd8':
        length = 16
    elif code == b'\xc7':
        length = struct.unpack("B", read_fn(1))[0]
    elif code == b'\xc8':
        length = struct.unpack(">H", read_fn(2))[0]
    elif code == b'\xc9':
        length = struct.unpack(">I", read_fn(4))[0]
    else:
        raise Exception("logic error, not ext: 0x%02x" % ord(code))

    return Ext(ord(read_fn(1)), read_fn(length))

def _unpack_array(code, read_fn):
    if (ord(code) & 0xf0) == 0x90:
        length = (ord(code) & ~0xf0)
    elif code == b'\xdc':
        length = struct.unpack(">H", read_fn(2))[0]
    elif code == b'\xdd':
        length = struct.unpack(">I", read_fn(4))[0]
    else:
        raise Exception("logic error, not array: 0x%02x" % ord(code))

    return [_unpackb(read_fn) for i in range(length)]

def _unpack_map(code, read_fn):
    if (ord(code) & 0xf0) == 0x80:
        length = (ord(code) & ~0xf0)
    elif code == b'\xde':
        length = struct.unpack(">H", read_fn(2))[0]
    elif code == b'\xdf':
        length = struct.unpack(">I", read_fn(4))[0]
    else:
        raise Exception("logic error, not map: 0x%02x" % ord(code))

    d = {}
    for i in range(length):
        # Unpack key
        k = _unpackb(read_fn)

        if not isinstance(k, collections.Hashable):
            raise KeyNotPrimitiveException("encountered non-primitive key type: %s" % str(type(k)))
        elif k in d:
            raise KeyDuplicateException("encountered duplicate key: %s, %s" % (str(k), str(type(k))))

        # Unpack value
        v = _unpackb(read_fn)

        d[k] = v
    return d

########################################

def _byte_reader(s):
    i = [0]
    def read_fn(n):
        if (i[0]+n > len(s)):
            raise InsufficientDataException()
        substring = s[i[0]:i[0]+n]
        i[0] += n
        return substring
    return read_fn

def _unpackb(read_fn):
    code = read_fn(1)
    return _unpack_dispatch_table[code](code, read_fn)

# For Python 2, expects a str object
def _unpackb2(s):
    if not isinstance(s, str):
        raise TypeError("packed data is not type 'str'")
    read_fn = _byte_reader(s)
    return _unpackb(read_fn)

# For Python 3, expects a bytes object
def _unpackb3(s):
    if not isinstance(s, bytes):
        raise TypeError("packed data is not type 'bytes'")
    read_fn = _byte_reader(s)
    return _unpackb(read_fn)

################################################################################

def __init():
    global packb
    global unpackb
    global compatibility
    global _float_size
    global _unpack_dispatch_table

    # Compatibility mode for handling strings/bytes with the old specification
    compatibility = False

    # Auto-detect system float precision
    if sys.float_info.mant_dig == 53:
        _float_size = 64
    else:
        _float_size = 32

    # Map packb and unpackb to the appropriate version
    if sys.version_info[0] == 3:
        packb = _packb3
        unpackb = _unpackb3
    else:
        packb = _packb2
        unpackb = _unpackb2

    # Build a dispatch table for fast lookup of unpacking function

    _unpack_dispatch_table = {}
    # Fix uint
    for code in range(0, 0x7f+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_integer
    # Fix map
    for code in range(0x80, 0x8f+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_map
    # Fix array
    for code in range(0x90, 0x9f+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_array
    # Fix str
    for code in range(0xa0, 0xbf+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_string
    # Nil
    _unpack_dispatch_table[b'\xc0'] = _unpack_nil
    # Reserved
    _unpack_dispatch_table[b'\xc1'] = _unpack_reserved
    # Boolean
    _unpack_dispatch_table[b'\xc2'] = _unpack_boolean
    _unpack_dispatch_table[b'\xc3'] = _unpack_boolean
    # Bin
    for code in range(0xc4, 0xc6+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_binary
    # Ext
    for code in range(0xc7, 0xc9+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_ext
    # Float
    _unpack_dispatch_table[b'\xca'] = _unpack_float
    _unpack_dispatch_table[b'\xcb'] = _unpack_float
    # Uint
    for code in range(0xcc, 0xcf+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_integer
    # Int
    for code in range(0xd0, 0xd3+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_integer
    # Fixext
    for code in range(0xd4, 0xd8+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_ext
    # String
    for code in range(0xd9, 0xdb+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_string
    # Array
    _unpack_dispatch_table[b'\xdc'] = _unpack_array
    _unpack_dispatch_table[b'\xdd'] = _unpack_array
    # Map
    _unpack_dispatch_table[b'\xde'] = _unpack_map
    _unpack_dispatch_table[b'\xdf'] = _unpack_map
    # Negative fixint
    for code in range(0xe0, 0xff+1):
        _unpack_dispatch_table[struct.pack("B", code)] = _unpack_integer

__init()
