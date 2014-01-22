# Copyright (c) 2013, Freja Nordsiek
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

import numpy as np
import h5py


def decode_to_numpy_unicode(data):
    """ Decodes data to Numpy unicode string (str_).

    Decodes `data` to a  Numpy unicode string (UTF-32), which is
    ``numpy.str_``. If it can't be decoded, it is returned as
    is. Unsigned integers, Python string types (``str``, ``bytes``), and
    ``numpy.string_`` are supported.

    Parameters
    ----------
    data : some type
        Data decode into a Numpy unicode string.

    Returns
    -------
    numpy.str_ or data
        If `data` can be decoded into a ``numpy.str_``, the decoded
        version is returned. Otherwise, `data` is returned unchanged.

    See Also
    --------
    decode_to_numpy_ascii
    numpy.str_

    """
    # How the conversion is done depends on the exact  underlying
    # type. For uint types, it is assumed to be stored as ASCII, UTF-16,
    # or UTF-32 depending on the size.
    if isinstance(data, (np.ndarray, np.uint8, np.uint16, np.uint32)):
        if data.dtype.name == 'uint8':
            data = data.data.tobytes().decode(encoding='ASCII')
        elif data.dtype.name == 'uint16':
            data = data.data.tobytes().decode(encoding='UTF-16')
        elif data.dtype.name == 'uint32':
            data = data.data.tobytes().decode(encoding='UTF-32')

    if isinstance(data, str):
        return np.unicode(data)
    elif isinstance(data, (bytes, np.string_)):
        return np.unicode(data.decode())
    else:
        return data


def decode_to_numpy_ascii(data):
    """ Decodes data to Numpy ASCII string (string_).

    Decodes `data` to a  Numpy ASCII string, which is
    ``numpy.string_``. If it can't be decoded, it is returned as
    is. Unsigned integers, Python string types (``str``, ``bytes``), and
    ``numpy.str_`` (UTF-32) are supported.

    Parameters
    ----------
    data : some type
        Data decode into a Numpy ASCII string.

    Returns
    -------
    numpy.string_ or data
        If `data` can be decoded into a ``numpy.string_``, the decoded
        version is returned. Otherwise, `data` is returned unchanged.

    See Also
    --------
    decode_to_numpy_unicode
    numpy.str_

    """
    # How the conversion is done depends on the exact  underlying
    # type. For uint types, it is assumed to be stored as ASCII, UTF-16,
    # or UTF-32 depending on the size when converting to an str. Then,
    # conversions from str, bytes, and numpy.unicode can be done.

    if isinstance(data, (np.ndarray, np.uint8, np.uint16, np.uint32)):
        if data.dtype.name == 'uint8':
            data = data.data.tobytes().decode(encoding='ASCII')
        elif data.dtype.name == 'uint16':
            data = data.data.tobytes().decode(encoding='UTF-16')
        elif data.dtype.name == 'uint32':
            data = data.data.tobytes().decode(encoding='UTF-32')

    if isinstance(data, bytes):
        return np.string_(data)
    elif isinstance(data, (str, np.unicode)):
        return np.string_(data.encode(encoding='ascii',
                          errors='replace'))
    else:
        return data


def decode_complex(data):
    """ Decodes possibly complex data read from an HDF5 file.

    Decodes possibly complex datasets read from an HDF5 file. HDF5
    doesn't have a native complex type, so they are stored as
    H5T_COMPOUND types with fields such as 'r' and 'i' for the real and
    imaginary parts. As there is no standardization for field names, the
    field names have to be analyzed for proper decoding. A variety of
    reasonably expected combinations of field names are checked and used
    if available to decode. If decoding is not possible, it is returned
    as is.

    Parameters
    ----------
    data : arraylike
        The data read from an HDF5 file, that might be complex, to
        decode into the proper Numpy complex type.

    Returns
    -------
    decoded data or data
        If `data` can be decoded into a complex type, the decoded
        complex version is returned. Otherwise, `data` is returned
        unchanged.

    See Also
    --------
    encode_complex

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

    real_name = None
    imag_name = None

    real_fields = ['r', 're', 'real']
    imag_fields = ['i', 'im', 'imag', 'imaginary']

    for s in fields:
        if s.lower() in real_fields:
            real_name = s
        elif s.lower() in imag_fields:
            imag_name = s

    # If the real and imaginary fields were found, construct the complex
    # form from the fields. Otherwise, return what we were given because
    # it isn't in the right form.
    if real_name is not None and imag_name is not None:
        return data[real_name] + 1j*data[imag_name]
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
        dtype_name = 'float' + str(int(dtype_name[7:]))

    # Create the new version of the data with the right field names for
    # the real and complex parts and the right shape.
    new_data = np.ndarray(shape=data.shape,
                          dtype=[(complex_names[0], dtype_name),
                          (complex_names[1], dtype_name)])

    # Set the real and complex parts and return it.
    new_data[complex_names[0]] = np.real(data)
    new_data[complex_names[1]] = np.imag(data)
    return new_data


def get_attribute(target, name):
    """ Gets an attribute from a Dataset or Group.

    Gets the value of an Attribute if it is present (get ``None`` if
    not).

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to get the
        attribute of.
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
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to get the
        string attribute of.
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
    elif isinstance(value, str):
        return value
    elif isinstance(value, bytes):
        return value.decode()
    elif isinstance(value, np.unicode):
        return str(value)
    elif isinstance(value, np.string_):
        return value.decode()
    else:
        return None


def set_attribute(target, name, value):
    """ Sets an attribute on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten if it differs from `value`.

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to set.
    value : numpy type other than :py:class:`str_`
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
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to set.
    value : string
        Value to set the attribute to. Can be any sort of string type
        that will convert to a :py:class:`numpy.string_`

    """
    set_attribute(target, name, np.string_(value))


def set_attribute_string_array(target, name, string_list):
    """ Sets an attribute to an array of string on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten with the list of string
    `string_list` (they will be vlen strings).

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to set.
    string_list : list, tuple
        List of strings to set the attribute to. Can be any string type
        that will convert to a :py:class:`numpy.string_`

    """
    target.attrs.create(name, np.string_(string_list),
                        dtype=h5py.special_dtype(vlen=bytes))


def del_attribute(target, name):
    """ Deletes an attribute on a Dataset or Group.

    If the attribute `name` exists, it is deleted.

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to delete.

    """
    if name in target.attrs:
        del target.attrs[name]
