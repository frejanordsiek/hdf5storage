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

""" Module of functions for low level reading and writing, setting and
delete HDF5 attributes, encoding and decoding strings and complex
arrays, etc.

"""

import sys
import copy
import string
import random
import posixpath

import numpy as np
import h5py

import hdf5storage.lowlevel


def write_data(f, grp, name, data, type_string, options):
    """ Writes a piece of data into an open HDF5 file.

    Low level function to store a Python type (`data`) into the
    specified Group.

    Parameters
    ----------
    f : h5py.File
        The open HDF5 file.
    grp : h5py.Group or h5py.File
        The Group to place the data in.
    name : str
        The name to write the data to.
    data : any
        The data to write.
    type_string : str or None
        The type string of the data, or ``None`` to deduce
        automatically.
    options : hdf5storage.core.Options
        The options to use when writing.

    Raises
    ------
    NotImplementedError
        If writing `data` is not supported.
    TypeNotMatlabCompatibleError
        If writing a type not compatible with MATLAB and
        `options.action_for_matlab_incompatible` is set to ``'error'``.

    See Also
    --------
    hdf5storage.write : Higher level version.
    read_data
    hdf5storage.Options

    """
    # Get the marshaller for type(data).

    tp = type(data)
    m = options.marshaller_collection.get_marshaller_for_type(tp)

    # If a marshaller was found, use it to write the data. Otherwise,
    # return an error. If we get something other than None back, then we
    # must recurse through the entries. Also, we must set the H5PATH
    # attribute to be the path to the containing group.

    if m is not None:
        m.write(f, grp, name, data, type_string, options)
    else:
        raise NotImplementedError('Can''t write data type: '+str(tp))


def read_data(f, grp, name, options):
    """ Writes a piece of data into an open HDF5 file.

    Low level function to read a Python type of the specified name from
    specified Group.

    Parameters
    ----------
    f : h5py.File
        The open HDF5 file.
    grp : h5py.Group or h5py.File
        The Group to read the data from.
    name : str
        The name of the data to read.
    options : hdf5storage.core.Options
        The options to use when reading.

    Returns
    -------
    data
        The data named `name` in Group `grp`.

    Raises
    ------
    CantReadError
        If the data cannot be read successfully.

    See Also
    --------
    hdf5storage.read : Higher level version.
    write_data
    hdf5storage.Options

    """
    # If name isn't found, return error.
    if name not in grp:
        raise hdf5storage.lowlevel.CantReadError('Could not find ' \
            + posixpath.join(grp.name, name))

    # Get the different attributes that can be used to identify they
    # type, which are the type string and the MATLAB class.
    type_string = get_attribute_string(grp[name], 'Python.Type')
    matlab_class = get_attribute_string(grp[name], 'MATLAB_class')

    # If the type_string is present, get the marshaller for it. If it is
    # not, use the one for the matlab class if it is given. Otherwise,
    # use the fallback (NumpyScalarArrayMarshaller for both Datasets and
    # Groups). If calls to the marshaller collection to get the right
    # marshaller don't return one (return None), we also go to the
    # default).

    m = None
    mc = options.marshaller_collection
    if type_string is not None:
        m = mc.get_marshaller_for_type_string(type_string)
    elif matlab_class is not None:
        m = mc.get_marshaller_for_matlab_class(matlab_class)
    elif hasattr(grp[name], 'dtype'):
        # Numpy dataset
        m = mc.get_marshaller_for_type(grp[name].dtype)
    elif isinstance(grp[name], (h5py.Group, h5py.File)):
        # Groups and files are like Matlab struct
        m = mc.get_marshaller_for_matlab_class('struct')

    if m is None:
        # use Numpy as a fallback
        m = mc.get_marshaller_for_type(np.uint8)

    # If a marshaller was found, use it to write the data. Otherwise,
    # return an error.

    if m is not None:
        return m.read(f, grp, name, options)
    else:
        raise hdf5storage.lowlevel.CantReadError('Could not read '
                                                 + grp[name].name)


def write_object_array(f, data, options):
    """ Writes an array of objects recursively.

    Writes the elements of the given object array recursively in the
    HDF5 Group ``options.group_for_references`` and returns an
    ``h5py.Reference`` array to all the elements.

    Parameters
    ----------
    f : h5py.File
        The HDF5 file handle that is open.
    data : numpy.ndarray of objects
        Numpy object array to write the elements of.
    options : hdf5storage.core.Options
        hdf5storage options object.

    Returns
    -------
    numpy.ndarray of h5py.Reference
        A reference array pointing to all the elements written to the
        HDF5 file. For those that couldn't be written, the respective
        element points to the canonical empty.

    Raises
    ------
    TypeNotMatlabCompatibleError
        If writing a type not compatible with MATLAB and
        `options.action_for_matlab_incompatible` is set to ``'error'``.

    See Also
    --------
    read_object_array
    hdf5storage.Options.group_for_references
    h5py.Reference

    """
    # We need to grab the special reference dtype and make an empty
    # array to store all the references in.
    ref_dtype = h5py.special_dtype(ref=h5py.Reference)
    data_refs = np.zeros(shape=data.shape, dtype='object')

    # We need to make sure that the group to hold references is present,
    # and create it if it isn't.

    if options.group_for_references not in f:
        f.create_group(options.group_for_references)

    grp2 = f[options.group_for_references]

    if not isinstance(grp2, h5py.Group):
        del f[options.group_for_references]
        f.create_group(options.group_for_references)
        grp2 = f[options.group_for_references]

    # The Dataset 'a' needs to be present as the canonical empty. It is
    # just and np.uint32/64([0, 0]) with its a MATLAB_class of
    # 'canonical empty' and the 'MATLAB_empty' attribute set. If it
    # isn't present or is incorrectly formatted, it is created
    # truncating anything previously there.
    if 'a' not in grp2 or grp2['a'].shape != (2,) \
            or not grp2['a'].dtype.name.startswith('uint') \
            or np.any(grp2['a'][...] != np.uint64([0, 0])) \
            or get_attribute_string(grp2['a'], 'MATLAB_class') != \
            'canonical empty' \
            or get_attribute(grp2['a'], 'MATLAB_empty') != 1:
        if 'a' in grp2:
            del grp2['a']
        grp2.create_dataset('a', data=np.uint64([0, 0]))
        set_attribute_string(grp2['a'], 'MATLAB_class',
                             'canonical empty')
        set_attribute(grp2['a'], 'MATLAB_empty',
                      np.uint8(1))

    # Go through all the elements of data and write them, gabbing their
    # references and putting them in data_refs. They will be put in
    # group_for_references, which is also what the H5PATH needs to be
    # set to if we are doing MATLAB compatibility (otherwise, the
    # attribute needs to be deleted). If an element can't be written
    # (doing matlab compatibility, but it isn't compatible with matlab
    # and action_for_matlab_incompatible option is True), the reference
    # to the canonical empty will be used for the reference array to
    # point to.
    for index, x in np.ndenumerate(data):
        data_refs[index] = None
        name_for_ref = next_unused_name_in_group(grp2, 16)
        write_data(f, grp2, name_for_ref, x, None, options)
        if name_for_ref in grp2:
            data_refs[index] = grp2[name_for_ref].ref
            if options.matlab_compatible:
                set_attribute_string(grp2[name_for_ref],
                                     'H5PATH', grp2.name)
            else:
                del_attribute(grp2[name_for_ref], 'H5PATH')
        else:
            data_refs[index] = grp2['a'].ref

    # Now, the dtype needs to be changed to the reference type and the
    # whole thing copied over to data_to_store.
    return data_refs.astype(ref_dtype).copy()


def read_object_array(f, data, options):
    """ Reads an array of objects recursively.

    Read the elements of the given HDF5 Reference array recursively
    in the and constructs a ``numpy.object_`` array from its elements,
    which is returned.

    Parameters
    ----------
    f : h5py.File
        The HDF5 file handle that is open.
    data : numpy.ndarray of h5py.Reference
        The array of HDF5 References to read and make an object array
        from.
    options : hdf5storage.core.Options
        hdf5storage options object.

    Raises
    ------
    NotImplementedError
        If reading the object from file is currently not supported.

    Returns
    -------
    numpy.ndarray of numpy.object_
        The Python object array containing the items pointed to by
        `data`.

    See Also
    --------
    write_object_array
    hdf5storage.Options.group_for_references
    h5py.Reference

    """
    # Go through all the elements of data and read them using their
    # references, and the putting the output in new object array.
    data_derefed = np.zeros(shape=data.shape, dtype='object')
    for index, x in np.ndenumerate(data):
        try:
            data_derefed[index] = read_data(f, f[x].parent, \
                posixpath.basename(f[x].name), options)
        except:
            raise
    return data_derefed


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
    ltrs = string.ascii_letters + string.digits
    existing_names = set(grp.keys())
    while True:
        name = ''.join([random.choice(ltrs) for i in range(0, length)])
        if name not in existing_names:
            return name

def convert_numpy_str_to_uint16(data):
    """ Converts a numpy.str_ to UTF-16 encoding in numpy.uint16 form.

    Convert a ``numpy.str`` or an array of them (they are UTF-32
    strings) to UTF-16 in the equivalent array of ``numpy.uint16``. The
    conversion will throw an exception if any characters cannot be
    converted to UTF-16. Strings are expanded along rows (across columns)
    so a 2x3x4 array of 10 element strings will get turned into a 2x30x4
    array of uint16's if every UTF-32 character converts easily to a
    UTF-16 singlet, as opposed to a UTF-16 doublet.

    Parameters
    ----------
    data : numpy.str_ or numpy.ndarray of numpy.str_
        The string or array of them to convert.

    Returns
    -------
    numpy.ndarray of numpy.uint16
        The result of the conversion.

    Raises
    ------
    UnicodeEncodeError
        If a UTF-32 character has no UTF-16 representation.

    See Also
    --------
    convert_numpy_str_to_uint32
    decode_to_numpy_str

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
                      buffer=cdata.tostring())


def convert_numpy_str_to_uint32(data):
    """ Converts a numpy.str_ to its numpy.uint32 representation.

    Convert a ``numpy.str`` or an array of them (they are UTF-32
    strings) into the equivalent array of ``numpy.uint32`` that is byte
    for byte identical. Strings are expanded along rows (across columns)
    so a 2x3x4 array of 10 element strings will get turned into a 2x30x4
    array of uint32's.

    Parameters
    ----------
    data : numpy.str_ or numpy.ndarray of numpy.str_
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
            return data.tostring().decode('UTF-8')
        elif data.dtype.name == 'uint16':
            return data.tostring().decode('UTF-16')
        elif data.dtype.name == 'uint32':
            return data.tostring().decode('UTF-32')
        elif data.dtype.char == 'S':
            return data.decode('UTF-8')
        else:
            if isinstance(data, np.ndarray):
                return data.tostring().decode('UTF-32')
            else:
                return data.encode('UTF-32').decode('UTF-32')

    if isinstance(data, bytes):
        return data.decode('UTF-8')
    else:
        return data


def convert_to_numpy_str(data, length=None):
    """ Decodes data to Numpy unicode string (str_).

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
    numpy.str_ or numpy.ndarray of numpy.str_ or data
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
        # They are single UTF-8 or UTF-16 scalars, which can be wrapped
        # into an array and recursed.
        return convert_to_numpy_str(np.atleast_1d(data))[0]
    elif isinstance(data, np.uint32):
        # It is just the uint32 version of the character, so it just
        # needs to be have the dtype essentially changed by having its
        # bytes read into ndarray.
        return np.ndarray(shape=tuple(), dtype='U1',
                          buffer=data.tostring())[()]
    elif isinstance(data, np.ndarray) and data.dtype.char == 'S':
        return np.char.encode(data, 'UTF-32')
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

        # numpy.char.decode will be used to decode. It needs the
        # encoding (UTF-8/16/32) which is gotten from the dtype. But it
        # also needs the data to be in big endian format, so it must be
        # byteswapped if it isn't. Without the swapping, an error occurs
        # since trailing nulls are dropped in numpy bytes_ arrays. The
        # dtype for each string element is just 'SX' where X is the
        # number of bytes.
        if data.dtype.name == 'uint8':
            encoding = 'UTF-8'
            swapbytes = False
            dt = 'S' + str(length)
        else:
            if data.dtype.name == 'uint16':
                encoding = 'UTF-16BE'
                dt = 'S' + str(2 * length)
            else:
                encoding = 'UTF-32BE'
                dt = 'S' + str(4 * length)
            if (data.dtype.byteorder == '<'
                or (sys.byteorder == 'little'
                    and data.dtype.byteorder == '=')):
                swapbytes = True
            else:
                swapbytes = False
        # Copy is needed to prevent errors.
        if swapbytes:
            return np.char.decode(data.copy().byteswap().view(dt),
                                  encoding)
        else:
            return np.char.decode(data.copy().view(dt), encoding)
    else:
        # Couldn't figure out what it is, so nothing can be done but
        # return it as is.
        return data


def convert_to_numpy_bytes(data, length=None):
    """ Decodes data to Numpy UTF-8 econded string (bytes_).

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
    numpy.bytes_ or numpy.ndarray of numpy.bytes_ or data
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
                          buffer=data.flatten().tostring())[()]
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
                new_data[i] = np.ndarray(shape=tuple(),
                                         dtype=new_data.dtype,
                                         buffer=chunk.tostring())[()]
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
    if name not in target.attrs:
        return None
    else:
        return target.attrs[name]


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
    if name not in target.attrs:
        target.attrs.create(name, value)
    elif target.attrs[name].dtype != value.dtype \
            or target.attrs[name].shape != value.shape:
        target.attrs.create(name, value)
    elif np.any(target.attrs[name] != value):
        target.attrs.modify(name, value)


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
    if name in target.attrs:
        del target.attrs[name]
