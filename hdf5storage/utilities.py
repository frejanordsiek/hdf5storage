# Copyright (c) 2013-2016, Freja Nordsiek
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" Module of functions to set and delete HDF5 attributes.

"""

import sys
import collections
import copy
import random

# In old versions of Python, everyting in collections.abc was in
# collections.
try:
    import collections.abc
except ImportError:
    collections.abc = collections

try:
    from pkg_resources import parse_version
except:
    from distutils.version import StrictVersion as parse_version\

import numpy as np
import h5py


# We need to determine if h5py is one of the versions that cannot read
# the MATLAB_fields Attribute in the normal fashion so that we can
# handle it specially.
_cant_read_matlab_fields = (
    parse_version(h5py.__version__)
    < parse_version('2.3'))
_handle_matlab_fields_specially = (
    parse_version(h5py.__version__)
    in (parse_version('3.0'),
        parse_version('3.1')))

if _handle_matlab_fields_specially:
    import ctypes
    import h5py._objects


# Determine if numpy.ndarrays and scalars have a tobytes method or
# not. If they don't, then the tostring method must be used instead.
_numpy_has_tobytes = hasattr(np.array([1]), 'tobytes')


def numpy_to_bytes(obj):
    """ Get the raw bytes of a numpy object's data.

    Calls the ``tobytes`` method on `obj` for new versions of ``numpy``
    where the method exists, and ``tostring`` for old versions of
    ``numpy`` where it does not.

    Parameters
    ----------
    obj : numpy.generic or numpy.ndarray
        Numpy scalar or array.

    Returns
    -------
    data : bytes
        The raw data.

    """
    if _numpy_has_tobytes:
        return obj.tobytes()
    else:
        return obj.tostring()


def read_matlab_fields_attribute(attrs):
    """ Reads the ``MATLAB_fields`` Attribute.

    On some versions of ``h5py``, the ``MATLAB_fields`` Attribute cannot
    be read in the standard way and must instead be read in a more
    manual fashion. This function reads the Attribute by the proper
    method.

    Parameters
    ----------
    attrs : h5py.AttributeManager
        The Attribute manager to read from.

    Returns
    -------
    value : numpy.ndarray or None
        The value of the ``MATLAB_fields`` Attribute, or ``None`` if it
        isn't available or its format is invalid.

    Raises
    ------
    TypeError
        If an argument has the wrong type.

    """
    if not isinstance(attrs, h5py.AttributeManager):
        raise TypeError('attrs must be a h5py.AttributeManager.')
    if not _handle_matlab_fields_specially:
        return attrs.get('MATLAB_fields')
    if _cant_read_matlab_fields or 'MATLAB_fields' not in attrs:
        return None
    # The following method is loosely based on the method provided by
    # takluyver at
    # https://github.com/h5py/h5py/issues/1817#issuecomment-781385699
    #
    # but has been improved by reading it directly as (size_t, void*)
    # pairs uint64s instead of using struct.unpack, and avoiding making
    # intermediate copies of the data by copying directly to the output
    # array.
    with h5py._objects.phil:
        attr_id = attrs.get_id('MATLAB_fields')
        dt = np.dtype([('length', np.uintp), ('pointer', np.intp)])
        raw_buf = np.empty(attr_id.shape, dtype=dt)
        attr_id.read(raw_buf, mtype=attr_id.get_type())
        attr = np.empty(raw_buf.shape, dtype='object')
        for i, (length, ptr) in enumerate(raw_buf.flat):
            at = np.empty(length, dtype='S1')
            ctypes.memmove(at.ctypes.data, int(ptr), int(length))
            attr.flat[i] = at
        return attr


def read_all_attributes_into(attrs, out):
    """ Reads all Attributes into a MutableMapping (dict-like)

    Reads all Attributes into the MutableMapping (dict-like) out,
    including the special handling of the ``MATLAB_fields`` Attribute on
    versions of ``h5py`` where it cannot be read in the standard
    fashion.

    Parameters
    ----------
    attrs : h5py.AttributeManager
        The Attribute manager to read from.
    out : MutableMapping
        The MutableMapping (dict-like) to write the Attributes into.

    Raises
    ------
    TypeError
        If an argument has the wrong type.

    See Also
    --------
    read_matlab_fields_attribute

    """
    if not isinstance(attrs, h5py.AttributeManager):
        raise TypeError('attrs must be a h5py.AttributeManager.')
    if not isinstance(out, (dict, collections.defaultdict,
                            collections.abc.MutableMapping)):
        raise TypeError('out must be a MutableMapping.')
    if not _handle_matlab_fields_specially \
            or 'MATLAB_fields' not in attrs:
        out.update(attrs.items())
    else:
        for k in attrs:
            if k != 'MATLAB_fields':
                out[k] = attrs[k]
            else:
                out[k] = read_matlab_fields_attribute(attrs)


def does_dtype_have_a_zero_shape(dt):
    """ Determine whether a dtype (or its fields) have zero shape.

    Determines whether the given ``numpy.dtype`` has a shape with a zero
    element or if one of its fields does, or if one of its fields'
    fields does, and so on recursively. The following dtypes do not have
    zero shape.

    * ``'uint8'``
    * ``[('a', 'int32'), ('blah', 'float16', (3, 3))]``
    * ``[('a', [('b', 'complex64')], (2, 1, 3))]``

    But the following do

    * ``('uint8', (1, 0))``
    * ``[('a', 'int32'), ('blah', 'float16', (3, 0))]``
    * ``[('a', [('b', 'complex64')], (2, 0, 3))]``

    Parameters
    ----------
    dt : numpy.dtype
        The dtype to check.

    Returns
    -------
    yesno : bool
        Whether `dt` or one of its fields has a shape with at least one
        element that is zero.

    Raises
    ------
    TypeError
        If `dt` is not a ``numpy.dtype``.

    """
    components = [dt]
    while 0 != len(components):
        c = components.pop()
        if 0 in c.shape:
            return True
        if c.names is not None:
            components.extend([v[0] for v in c.fields.values()])
        if c.base != c:
            components.append(c.base)
    return False


def next_unused_name_in_group(grp, length):
    """ Gives a name that isn't used in a Group.

    Generates a name of the desired length that is not a Dataset or
    Group in the given group. Note, if length is not large enough and
    `grp` is full enough, there may be no available names meaning that
    this function will hang.

    Parameters
    ----------
    grp : h5py.Group or h5py.File
        The HDF5 Group (or File if at '/') to generate an unused name
        in.
    length : int
        Number of characters the name should be.

    Returns
    -------
    str
        A name that isn't already an existing Dataset or Group in
        `grp`.

    """
    # While
    #
    # ltrs = string.ascii_letters + string.digits
    # name = ''.join([random.choice(ltrs) for i in range(length)])
    #
    # seems intuitive, its performance is abysmal compared to
    #
    # '%0{0}x'.format(length) % random.getrandbits(length * 4)
    #
    # The difference is a factor of 20. Idea from
    #
    # https://stackoverflow.com/questions/2782229/most-lightweight-way-
    #   to-create-a-random-string-and-a-random-hexadecimal-number/
    #   35161595#35161595
    fmt = '%0{0}x'.format(length)
    name = fmt % random.getrandbits(length * 4)
    while name in grp:
        name = fmt % random.getrandbits(length * 4)
    return name


def convert_numpy_str_to_uint16(data):
    """ Converts a numpy.unicode\\_ to UTF-16 in numpy.uint16 form.

    Convert a ``numpy.unicode_`` or an array of them (they are UTF-32
    strings) to UTF-16 in the equivalent array of ``numpy.uint16``. The
    conversion will throw an exception if any characters cannot be
    converted to UTF-16. Strings are expanded along rows (across columns)
    so a 2x3x4 array of 10 element strings will get turned into a 2x30x4
    array of uint16's if every UTF-32 character converts easily to a
    UTF-16 singlet, as opposed to a UTF-16 doublet.

    Parameters
    ----------
    data : numpy.unicode\\_ or numpy.ndarray of numpy.unicode\\_
        The string or array of them to convert.

    Returns
    -------
    array : numpy.ndarray of numpy.uint16
        The result of the conversion.

    Raises
    ------
    UnicodeEncodeError
        If a UTF-32 character has no UTF-16 representation.

    See Also
    --------
    convert_numpy_str_to_uint32
    convert_to_numpy_str

    """
    # An empty string should be an empty uint16
    if data.nbytes == 0:
        return np.uint16([])

    # We need to use the UTF-16 codec for our endianness. Using the
    # right one means we don't have to worry about removing the BOM.
    if sys.byteorder == 'little':
        codec = 'UTF-16LE'
    else:
        codec = 'UTF-16BE'

    # numpy.char.encode can do the conversion element wise. Then, we
    # just have convert to uin16 with the appropriate dimensions. The
    # dimensions are gotten from the shape of the converted data with
    # the number of column increased by the number of words (pair of
    # bytes) in the strings.
    cdata = np.char.encode(np.atleast_1d(data), codec)
    shape = list(cdata.shape)
    shape[-1] *= (cdata.dtype.itemsize // 2)
    return np.ndarray(shape=shape, dtype='uint16',
                      buffer=numpy_to_bytes(cdata))


def convert_numpy_str_to_uint32(data):
    """ Converts a numpy.str\\_ to its numpy.uint32 representation.

    Convert a ``numpy.str`` or an array of them (they are UTF-32
    strings) into the equivalent array of ``numpy.uint32`` that is byte
    for byte identical. Strings are expanded along rows (across columns)
    so a 2x3x4 array of 10 element strings will get turned into a 2x30x4
    array of uint32's.

    Parameters
    ----------
    data : numpy.str\\_ or numpy.ndarray of numpy.str\\_
        The string or array of them to convert.

    Returns
    -------
    numpy.ndarray of numpy.uint32
        The result of the conversion.

    See Also
    --------
    convert_numpy_str_to_uint16
    decode_to_numpy_str

    """
    if data.nbytes == 0:
        # An empty string should be an empty uint32.
        return np.uint32([])
    else:
        # We need to calculate the new shape from the current shape,
        # which will have to be expanded along the rows to fit all the
        # characters (the dtype.itemsize gets the number of bytes in
        # each string, which is just 4 times the number of
        # characters. Then it is a mstter of getting a view of the
        # string (in flattened form so that it is contiguous) as uint32
        # and then reshaping it.
        shape = list(np.atleast_1d(data).shape)
        shape[-1] *= data.dtype.itemsize//4
        return data.flatten().view(np.uint32).reshape(tuple(shape))

def convert_to_str(data):
    """ Decodes data to the Python 3.x str (Python 2.x unicode) type.

    Decodes `data` to a Python 3.x ``str`` (Python 2.x ``unicode``). If
    it can't be decoded, it is returned as is. Unsigned integers, Python
    ``bytes``, and Numpy strings (``numpy.str_`` and
    ``numpy.bytes_``). Python 3.x ``bytes``, Python 2.x ``str``, and
    ``numpy.bytes_`` are assumed to be encoded in UTF-8.

    Parameters
    ----------
    data : some type
        Data decode into an ``str`` string.

    Returns
    -------
    str or data
        If `data` can be decoded into a ``str``, the decoded version is
        returned. Otherwise, `data` is returned unchanged.

    See Also
    --------
    convert_to_numpy_str
    convert_to_numpy_bytes

    """
    # How the conversion is done depends on the exact  underlying
    # type. Numpy types are handled separately. For uint types, it is
    # assumed to be stored as UTF-8, UTF-16, or UTF-32 depending on the
    # size when converting to an str. numpy.string_ is just like
    # converting a bytes. numpy.unicode has to be encoded into bytes
    # before it can be decoded back into an str. bytes is decoded
    # assuming it is in UTF-8. Otherwise, data has to be returned as is.

    if isinstance(data, (np.ndarray, np.uint8, np.uint16, np.uint32,
                  np.bytes_, np.unicode_)):
        if data.dtype.name == 'uint8':
            return numpy_to_bytes(data.flatten()).decode('UTF-8')
        elif data.dtype.name == 'uint16':
            return numpy_to_bytes(data.flatten()).decode('UTF-16')
        elif data.dtype.name == 'uint32':
            return numpy_to_bytes(data.flatten()).decode('UTF-32')
        elif data.dtype.char == 'S':
            return data.decode('UTF-8')
        else:
            if isinstance(data, np.ndarray):
                return numpy_to_bytes(data.flatten()).decode('UTF-32')
            else:
                return data.encode('UTF-32').decode('UTF-32')

    if isinstance(data, bytes):
        return data.decode('UTF-8')
    else:
        return data


def convert_to_numpy_str(data, length=None):
    """ Decodes data to Numpy unicode string (str\\_).

    Decodes `data` to Numpy unicode string (UTF-32), which is
    ``numpy.str_``, or an array of them. If it can't be decoded, it is
    returned as is. Unsigned integers, Python string types (``str``,
    ``bytes``), and ``numpy.bytes_`` are supported. If it is an array of
    ``numpy.bytes_``, an array of those all converted to ``numpy.str_``
    is returned. Python 3.x ``bytes``, Python 2.x ``str``, and
    ``numpy.bytes_`` are assumed to be encoded in UTF-8.

    For an array of unsigned integers, it may be desirable to make an
    array with strings of some specified length as opposed to an array
    of the same size with each element being a one element string. This
    naturally arises when converting strings to unsigned integer types
    in the first place, so it needs to be reversible.  The `length`
    parameter specifies how many to group together into a string
    (desired string length). For 1d arrays, this is along its only
    dimension. For higher dimensional arrays, it is done along each row
    (across columns). So, for a 3x10x5 input array of uints and a
    `length` of 5, the output array would be a 3x2x5 of 5 element
    strings.

    Parameters
    ----------
    data : some type
        Data decode into a Numpy unicode string.
    length : int or None, optional
        The number of consecutive elements (in the case of unsigned
        integer `data`) to compose each string in the output array from.
        ``None`` indicates the full amount for a 1d array or the number
        of columns (full length of row) for a higher dimension array.

    Returns
    -------
    numpy.str\\_ or numpy.ndarray of numpy.str\\_ or data
        If `data` can be decoded into a ``numpy.str_`` or a
        ``numpy.ndarray`` of them, the decoded version is returned.
        Otherwise, `data` is returned unchanged.

    See Also
    --------
    convert_to_str
    convert_to_numpy_bytes
    numpy.str_

    """
    # The method of conversion depends on its type.
    if isinstance(data, np.unicode_) or (isinstance(data, np.ndarray) \
            and data.dtype.char == 'U'):
        # It is already an np.str_ or array of them, so nothing needs to
        # be done.
        return data
    elif (sys.hexversion >= 0x03000000 and isinstance(data, str)) \
           or (sys.hexversion < 0x03000000 \
           and isinstance(data, unicode)):
        # Easily converted through constructor.
        return np.unicode_(data)
    elif isinstance(data, (bytes, bytearray, np.bytes_)):
        # All of them can be decoded and then passed through the
        # constructor.
        return np.unicode_(data.decode('UTF-8'))
    elif isinstance(data, (np.uint8, np.uint16)):
        # They are single UTF-8 or UTF-16 scalars, and are easily
        # converted to a UTF-8 string and then passed through the
        # constructor.
        return np.unicode_(convert_to_str(data))
    elif isinstance(data, np.uint32):
        # It is just the uint32 version of the character, so it just
        # needs to be have the dtype essentially changed by having its
        # bytes read into ndarray.
        return np.ndarray(shape=tuple(), dtype='U1',
                          buffer=numpy_to_bytes(data.flatten()))[()]
    elif isinstance(data, np.ndarray) and data.dtype.char == 'S':
        # We just need to convert it elementwise.
        new_data = np.zeros(shape=data.shape,
                            dtype='U' + str(data.dtype.itemsize))
        for index, x in np.ndenumerate(data):
            new_data[index] = np.unicode_(x.decode('UTF-8'))
        return new_data
    elif isinstance(data, np.ndarray) \
            and data.dtype.name in ('uint8', 'uint16', 'uint32'):
        # It is an ndarray of some uint type. How it is converted
        # depends on its shape. If its shape is just (), then it is just
        # a scalar wrapped in an array, which can be converted by
        # recursing the scalar value back into this function.
        shape = list(data.shape)
        if len(shape) == 0:
            return convert_to_numpy_str(data[()])

        # As there are more than one element, it gets a bit more
        # complicated. We need to take the subarrays of the specified
        # length along columns (1D arrays will be treated as row arrays
        # here), each of those converted to an str_ scalar (normal
        # string) and stuffed into a new array.
        #
        # If the length was not given, it needs to be set to full. Then
        # the shape of the new array needs to be calculated (divide the
        # appropriate dimension, which depends on the number of
        # dimentions).
        if len(shape) == 1:
            if length is None:
                length = shape[0]
            new_shape = (shape[0]//length,)
        else:
            if length is None:
                length = shape[-1]
            new_shape = copy.deepcopy(shape)
            new_shape[-1] //= length

        # The new array can be made as all zeros (nulls) with enough
        # padding to hold everything (dtype='UL' where 'L' is the
        # length). It will start out as a 1d array and be reshaped into
        # the proper shape later (makes indexing easier).
        new_data = np.zeros(shape=(np.prod(new_shape),),
                            dtype='U'+str(length))

        # With data flattened into a 1d array, we just need to take
        # length sized chunks, convert them (if they are uint8 or 16,
        # then decode to str first, if they are uint32, put them as an
        # input buffer for an ndarray of type 'U').
        data = data.flatten()
        for i in range(0, new_data.shape[0]):
            chunk = data[(i*length):((i+1)*length)]
            if data.dtype.name == 'uint32':
                new_data[i] = np.ndarray(
                    shape=tuple(),
                    dtype=new_data.dtype,
                    buffer=numpy_to_bytes(chunk))[()]
            else:
                new_data[i] = np.unicode_(convert_to_str(chunk))

        # Only thing is left is to reshape it.
        return new_data.reshape(tuple(new_shape))
    else:
        # Couldn't figure out what it is, so nothing can be done but
        # return it as is.
        return data


def convert_to_numpy_bytes(data, length=None):
    """ Decodes data to Numpy UTF-8 econded string (bytes\\_).

    Decodes `data` to a Numpy UTF-8 encoded string, which is
    ``numpy.bytes_``, or an array of them in which case it will be ASCII
    encoded instead. If it can't be decoded, it is returned as
    is. Unsigned integers, Python string types (``str``, ``bytes``), and
    ``numpy.str_`` (UTF-32) are supported.

    For an array of unsigned integers, it may be desirable to make an
    array with strings of some specified length as opposed to an array
    of the same size with each element being a one element string. This
    naturally arises when converting strings to unsigned integer types
    in the first place, so it needs to be reversible.  The `length`
    parameter specifies how many to group together into a string
    (desired string length). For 1d arrays, this is along its only
    dimension. For higher dimensional arrays, it is done along each row
    (across columns). So, for a 3x10x5 input array of uints and a
    `length` of 5, the output array would be a 3x2x5 of 5 element
    strings.

    Parameters
    ----------
    data : some type
        Data decode into a Numpy UTF-8 encoded string/s.
    length : int or None, optional
        The number of consecutive elements (in the case of unsigned
        integer `data`) to compose each string in the output array from.
        ``None`` indicates the full amount for a 1d array or the number
        of columns (full length of row) for a higher dimension array.

    Returns
    -------
    numpy.bytes\\_ or numpy.ndarray of numpy.bytes\\_ or data
        If `data` can be decoded into a ``numpy.bytes_`` or a
        ``numpy.ndarray`` of them, the decoded version is returned.
        Otherwise, `data` is returned unchanged.

    See Also
    --------
    convert_to_str
    convert_to_numpy_str
    numpy.bytes_

    """
    # The method of conversion depends on its type.
    if isinstance(data, np.bytes_) or (isinstance(data, np.ndarray) \
            and data.dtype.char == 'S'):
        # It is already an np.bytes_ or array of them, so nothing needs
        # to be done.
        return data
    elif isinstance(data, (bytes, bytearray)):
        # Easily converted through constructor.
        return np.bytes_(data)
    elif (sys.hexversion >= 0x03000000 and isinstance(data, str)) \
            or (sys.hexversion < 0x03000000 \
            and isinstance(data, unicode)):
        return np.bytes_(data.encode('UTF-8'))
    elif isinstance(data, (np.uint16, np.uint32)):
        # They are single UTF-16 or UTF-32 scalars, and are easily
        # converted to a UTF-8 string and then passed through the
        # constructor.
        return np.bytes_(convert_to_str(data).encode('UTF-8'))
    elif isinstance(data, np.uint8):
        # It is just the uint8 version of the character, so it just
        # needs to be have the dtype essentially changed by having its
        # bytes read into ndarray.
        return np.ndarray(shape=tuple(), dtype='S1',
                          buffer=numpy_to_bytes(data.flatten()))[()]
    elif isinstance(data, np.ndarray) and data.dtype.char == 'U':
        # We just need to convert it elementwise.
        new_data = np.zeros(shape=data.shape,
                            dtype='S' + str(data.dtype.itemsize))
        for index, x in np.ndenumerate(data):
            new_data[index] = np.bytes_(x.encode('UTF-8'))
        return new_data
    elif isinstance(data, np.ndarray) \
            and data.dtype.name in ('uint8', 'uint16', 'uint32'):
        # It is an ndarray of some uint type. How it is converted
        # depends on its shape. If its shape is just (), then it is just
        # a scalar wrapped in an array, which can be converted by
        # recursing the scalar value back into this function.
        shape = list(data.shape)
        if len(shape) == 0:
            return convert_to_numpy_bytes(data[()])

        # As there are more than one element, it gets a bit more
        # complicated. We need to take the subarrays of the specified
        # length along columns (1D arrays will be treated as row arrays
        # here), each of those converted to an str_ scalar (normal
        # string) and stuffed into a new array.
        #
        # If the length was not given, it needs to be set to full. Then
        # the shape of the new array needs to be calculated (divide the
        # appropriate dimension, which depends on the number of
        # dimentions).
        if len(shape) == 1:
            if length is None:
                length2 = shape[0]
                new_shape = (shape[0],)
            else:
                length2 = length
                new_shape = (shape[0]//length2,)
        else:
            if length is None:
                length2 = shape[-1]
            else:
                length2 = length
            new_shape = copy.deepcopy(shape)
            new_shape[-1] //= length2

        # The new array can be made as all zeros (nulls) with enough
        # padding to hold everything (dtype='UL' where 'L' is the
        # length). It will start out as a 1d array and be reshaped into
        # the proper shape later (makes indexing easier).
        new_data = np.zeros(shape=(np.prod(new_shape),),
                            dtype='S'+str(length2))

        # With data flattened into a 1d array, we just need to take
        # length sized chunks, convert them (if they are uint8 or 16,
        # then decode to str first, if they are uint32, put them as an
        # input buffer for an ndarray of type 'U').
        data = data.flatten()
        for i in range(0, new_data.shape[0]):
            chunk = data[(i*length2):((i+1)*length2)]
            if data.dtype.name == 'uint8':
                new_data[i] = np.ndarray(
                    shape=tuple(),
                    dtype=new_data.dtype,
                    buffer=numpy_to_bytes(chunk))[()]
            else:
                new_data[i] = np.bytes_( \
                    convert_to_str(chunk).encode('UTF-8'))

        # Only thing is left is to reshape it.
        return new_data.reshape(tuple(new_shape))
    else:
        # Couldn't figure out what it is, so nothing can be done but
        # return it as is.
        return data


def decode_complex(data, complex_names=(None, None)):
    """ Decodes possibly complex data read from an HDF5 file.

    Decodes possibly complex datasets read from an HDF5 file. HDF5
    doesn't have a native complex type, so they are stored as
    H5T_COMPOUND types with fields such as 'r' and 'i' for the real and
    imaginary parts. As there is no standardization for field names, the
    field names have to be given explicitly, or the fieldnames in `data`
    analyzed for proper decoding to figure out the names. A variety of
    reasonably expected combinations of field names are checked and used
    if available to decode. If decoding is not possible, it is returned
    as is.

    Parameters
    ----------
    data : arraylike
        The data read from an HDF5 file, that might be complex, to
        decode into the proper Numpy complex type.
    complex_names : tuple of 2 str and/or Nones, optional
        ``tuple`` of the names to use (in order) for the real and
        imaginary fields. A ``None`` indicates that various common
        field names should be tried.

    Returns
    -------
    decoded data or data
        If `data` can be decoded into a complex type, the decoded
        complex version is returned. Otherwise, `data` is returned
        unchanged.

    See Also
    --------
    encode_complex

    Notes
    -----
    Currently looks for real field names of ``('r', 're', 'real')`` and
    imaginary field names of ``('i', 'im', 'imag', 'imaginary')``
    ignoring case.

    """
    # Now, complex types are stored in HDF5 files as an H5T_COMPOUND type
    # with fields along the lines of ('r', 're', 'real') and ('i', 'im',
    # 'imag', 'imaginary') for the real and imaginary parts, which most
    # likely won't be properly extracted back into making a Python
    # complex type unless the proper h5py configuration is set. Since we
    # can't depend on it being set and adjusting it is hazardous (the
    # setting is global), it is best to just decode it manually. These
    # fields are obtained from the fields of its dtype. Obviously, if
    # there are no fields, then there is nothing to do.
    if data.dtype.fields is None:
        return data

    fields = list(data.dtype.fields)

    # If there aren't exactly two fields, then it can't be complex.
    if len(fields) != 2:
        return data

    # We need to grab the field names for the real and imaginary
    # parts. This will be done by seeing which list, if any, each field
    # is and setting variables to the proper name if it is in it (they
    # are initialized to None so that we know if one isn't found).

    real_fields = ['r', 're', 'real']
    imag_fields = ['i', 'im', 'imag', 'imaginary']

    cnames = list(complex_names)
    for s in fields:
        if s.lower() in real_fields:
            cnames[0] = s
        elif s.lower() in imag_fields:
            cnames[1] = s

    # If the real and imaginary fields were found, construct the complex
    # form from the fields. This is done by finding the complex type
    # that they cast to, making an array, and then setting the
    # parts. Otherwise, return what we were given because it isn't in
    # the right form.
    if cnames[0] is not None and cnames[1] is not None:
        cdata = np.result_type(data[cnames[0]].dtype, \
            data[cnames[1]].dtype, 'complex64').type(data[cnames[0]])
        cdata.imag = data[cnames[1]]
        return cdata
    else:
        return data


def encode_complex(data, complex_names):
    """ Encodes complex data to having arbitrary complex field names.

    Encodes complex `data` to have the real and imaginary field names
    given in `complex_numbers`. This is needed because the field names
    have to be set so that it can be written to an HDF5 file with the
    right field names (HDF5 doesn't have a native complex type, so
    H5T_COMPOUND have to be used).

    Parameters
    ----------
    data : arraylike
        The data to encode as a complex type with the desired real and
        imaginary part field names.
    complex_names : tuple of 2 str
        ``tuple`` of the names to use (in order) for the real and
        imaginary fields.

    Returns
    -------
    encoded data
        `data` encoded into having the specified field names for the
        real and imaginary parts.

    See Also
    --------
    decode_complex

    """
    # Grab the dtype name, and convert it to the right non-complex type
    # if it isn't already one.
    dtype_name = data.dtype.name
    if dtype_name[0:7] == 'complex':
        dtype_name = 'float' + str(int(float(dtype_name[7:])/2))

    # Create the new version of the data with the right field names for
    # the real and complex parts. This is easy to do with putting the
    # right detype in the view function.
    dt = np.dtype([(complex_names[0], dtype_name),
                   (complex_names[1], dtype_name)])
    return data.view(dt).copy()


def get_attribute(target, name):
    """ Gets an attribute from a Dataset or Group.

    Gets the value of an Attribute if it is present (get ``None`` if
    not).

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to get the attribute of.
    name : str
        Name of the attribute to get.

    Returns
    -------
    The value of the attribute if it is present, or ``None`` if it
    isn't.

    """
    try:
        return target.attrs[name]
    except:
        return None


def get_attribute_string(target, name):
    """ Gets a string attribute from a Dataset or Group.

    Gets the value of an Attribute that is a string if it is present
    (get ``None`` if it is not present or isn't a string type).

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to get the string attribute of.
    name : str
        Name of the attribute to get.

    Returns
    -------
    str or None
        The ``str`` value of the attribute if it is present, or ``None``
        if it isn't or isn't a type that can be converted to ``str``

    """
    value = get_attribute(target, name)
    if value is None:
        return value
    elif (sys.hexversion >= 0x03000000 and isinstance(value, str)) \
            or (sys.hexversion < 0x03000000 \
            and isinstance(value, unicode)):
        return value
    elif isinstance(value, bytes):
        return value.decode()
    elif isinstance(value, np.unicode_):
        return str(value)
    elif isinstance(value, np.bytes_):
        return value.decode()
    else:
        return None


def get_attribute_string_array(target, name):
    """ Gets a string array Attribute from a Dataset or Group.

    Gets the value of an Attribute that is a string array if it is
    present (get ``None`` if not).

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to get the attribute of.
    name : str
        Name of the string array Attribute to get.

    Returns
    -------
    list of str or None
        The string array value of the Attribute if it is present, or
        ``None`` if it isn't.

    """
    value = get_attribute(target, name)
    if value is None:
        return value
    return [convert_to_str(x) for x in value]


def set_attribute(target, name, value):
    """ Sets an attribute on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten if it differs from `value`.

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to set the attribute of.
    name : str
        Name of the attribute to set.
    value : numpy type other than ``numpy.str_``
        Value to set the attribute to.

    """

    # use alias to speed up the code
    target_attributes = target.attrs
    if name not in target_attributes:
        target_attributes.create(name, value)
    elif name == 'MATLAB_fields':
        if not np.array_equal(value, read_matlab_fields_attribute(
                target_attributes)):
            target_attributes.create(name, value)
    else:
        attr = target_attributes[name]
        if attr.dtype != value.dtype \
            or attr.shape != value.shape:
            target_attributes.create(name, value)
        elif np.any(attr != value):
            target_attributes.modify(name, value)


def set_attribute_string(target, name, value):
    """ Sets an attribute to a string on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten if it differs from `value`.

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to set the string attribute of.
    name : str
        Name of the attribute to set.
    value : string
        Value to set the attribute to. Can be any sort of string type
        that will convert to a ``numpy.bytes_``

    """
    set_attribute(target, name, np.bytes_(value))


def set_attribute_string_array(target, name, string_list):
    """ Sets an attribute to an array of string on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten with the list of string
    `string_list` (they will be vlen strings).

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to set the string array attribute of.
    name : str
        Name of the attribute to set.
    string_list : list of str
        List of strings to set the attribute to. Strings must be ``str``

    """
    s_list = [convert_to_str(s) for s in string_list]
    if sys.hexversion >= 0x03000000:
        target.attrs.create(name, s_list,
                            dtype=h5py.special_dtype(vlen=str))
    else:
        target.attrs.create(name, s_list,
                            dtype=h5py.special_dtype(vlen=unicode))


def del_attribute(target, name):
    """ Deletes an attribute on a Dataset or Group.

    If the attribute `name` exists, it is deleted.

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to delete attribute of.
    name : str
        Name of the attribute to delete.

    """
    attr_manager = target.attrs
    if name in attr_manager:
        del attr_manager[name]
