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

import sys
import os
import posixpath
import copy
import inspect
import datetime
import numpy as np
import h5py

from hdf5storage.utilities import *

from hdf5storage.lowlevel import write_data


class Options(object):
    def __init__(self):
        self.store_type_information = True
        self.MATLAB_compatible = True
        self.scalar_options = {}
        self.array_options = {}
        self.delete_unused_variables = True
        self.convert_scalars_to_arrays = True
        self.reverse_dimension_order = True
        self.convert_strings_to_utf16 = True
        self.store_shape_for_empty = True
        self.complex_names = ('real', 'imag')
        self.marshaller_collection = MarshallerCollection()


class MarshallerCollection(object):
    """ Represents, maintains, and retreives a set of marshallers.

    Maintains a list of marshallers used to marshal data types to and
    from HDF5 files. It includes the builtin marshallers from the
    :py:mod:`hdf5storage.Marshallers` module as well as any user
    supplied or added marshallers. While the builtin list cannot be
    changed; user ones can be added or removed. Also has functions to
    get the marshaller appropriate for ``type`` or type_string for a
    python data type.

    User marshallers must provide the same interface as
    :py:class:`hdf5storage.Marshallers.TypeMarshaller`, which is
    probably most easily done by inheriting from it.

    Parameters
    ----------
    marshallers : marshaller or list of marshallers, optional
        The user marshaller/s to add to the collection.

    See Also
    --------
    hdf5storage.Marshallers
    hdf5storage.Marshallers.TypeMarshaller

    """
    def __init__(self, marshallers=[]):
        # Two lists of marshallers need to be maintained: one for the
        # builtin ones in the Marshallers module, and another for user
        # supplied ones.

        # Grab all the marshallers in the Marshallers module (they are
        # the classes) by inspection.
        self._builtin_marshallers = [m() for key, m in dict(
                                     inspect.getmembers(Marshallers,
                                     inspect.isclass)).items()]
        self._user_marshallers = []

        # A list of all the marshallers will be needed along with
        # dictionaries to lookup up the marshaller to use for given
        # types or type strings (they are the keys).
        self._marshallers = []
        self._out = dict()
        self._in = dict()

        # Add any user given marshallers.
        self.add_marshaller(copy.deepcopy(marshallers))

    def _update_marshallers(self):
        # Combine both sets of marshallers.
        self._marshallers = self._builtin_marshallers.copy()
        self._marshallers.extend(self._user_marshallers)

        # Construct the dictionary to look up the appropriate marshaller
        # by type.

        self._out = {tp: m for m in self._marshallers for tp in m.types}

        # The equivalent one to read data types given type strings needs
        # to be created from it. Basically, we have to make the key be
        # the cpython_type_string from it.

        self._in = {type_string: m for key, m in self._out.items()
                    for type_string in m.cpython_type_strings}

    def add_marshaller(self, marshallers):
        if not isinstance(marshallers, (list, tuple, set, frozenset)):
            marshallers = [marshallers]
        for m in marshallers:
            if m not in self._user_marshallers:
                self._user_marshallers.append(m)
        self._update_marshallers()

    def remove_marshaller(self, marshallers):
        if not isinstance(marshallers, (list, tuple, set, frozenset)):
            marshallers = [marshallers]
        for m in marshallers:
            if m in self._user_marshallers:
                self._user_marshallers.remove(m)
        self._update_marshallers()

    def clear_marshallers(self):
        """ Clears the list of user provided marshallers.

        Removes all user provided marshallers, but not the builtin ones
        from the :py:mod:`hdf5storage.Marshallers` module, from the list
        of marshallers used.

        """
        self._user_marshallers.clear()
        self._update_marshallers()

    def get_marshaller_for_type(self, tp):
        if tp in self._out:
            return copy.deepcopy(self._out[tp])
        else:
            return None


def write(filename='data.h5', name='/data', data=None,
          store_type_information=True, MATLAB_compatible=True,
          delete_unused_variables=False,
          convert_scalars_to_arrays=False,
          reverse_dimension_order=False,
          convert_strings_to_utf16=False,
          store_shape_for_empty=False,
          complex_names=('r','i')):
    # Pack the different options into an Options class.

    options = Options()

    options.store_type_information = store_type_information
    options.MATLAB_compatible = MATLAB_compatible
    options.scalar_options = {}
    options.array_options = {}
    options.delete_unused_variables = delete_unused_variables
    options.convert_scalars_to_arrays = convert_scalars_to_arrays
    options.reverse_dimension_order = reverse_dimension_order
    options.convert_strings_to_utf16 = convert_strings_to_utf16
    options.store_shape_for_empty = store_shape_for_empty
    options.complex_names = complex_names

    # Now, if we are doing MATLAB compatibility, certain options must be
    # overridden.

    if MATLAB_compatible:
        options.delete_unused_variables = True
        options.convert_scalars_to_arrays = True
        options.convert_strings_to_utf16 = True
        options.reverse_dimension_order = True
        options.store_shape_for_empty = True
        options.complex_names = ('real','imag')

    # Reset the list of MATLAB_fields attributes to set.

    _MATLAB_fields_pairs = []

    # Remove double slashes and a non-root trailing slash.

    name = posixpath.normpath(name)

    # Extract the group name and the target name (will be a dataset if
    # data can be mapped to it, but will end up being made into a group
    # otherwise. As HDF5 files use posix path, conventions, posixpath
    # will do everything.
    groupname = posixpath.dirname(name)
    targetname = posixpath.basename(name)

    # If groupname got turned into blank, then it is just root.
    if groupname == '':
        groupname = '/'

    # If targetname got turned blank, then it is the current directory.
    if targetname == '':
        targetname = '.'

    # Open the hdf5 file and start writing the data (and making the
    # group groupname at the same time if it doesn't exist). This is all
    # wrapped in a try block, so that the file can be closed if any
    # errors happen (the error is re-raised). The
    # h5py.get_config().complex_names is changed to complex_names. The
    # previous value is restored at the end. Obviously, this makes this
    # whole function thread unsafe as it changes it for h5py globally.

    backup_complex_names = h5py.get_config().complex_names

    try:
        h5py.get_config().complex_names = options.complex_names

        # If the file already exists, we just open it. If it doesn't
        # exist yet and we are doing any MATLAB formatting, we need to
        # allocate a 512 byte user block (need metadata for MATLAB to
        # tell it is a valid .mat file). The user_block size is also
        # grabbed right before closing, so that if there is a userblock
        # and we are doing MATLAB formatting, we know to set it.

        if os.path.isfile(filename) or not options.MATLAB_compatible:
            f = h5py.File(filename)
        else:
            f = h5py.File(filename, mode='w', userblock_size=512)

        if groupname not in f:
            grp = f.require_group(groupname)
        else:
            grp = f[groupname]

        write_data(f, grp, targetname, data,
                   None, options)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    finally:
        userblock_size = f.userblock_size
        f.close()
        h5py.get_config().complex_names = backup_complex_names

    # If we are doing MATLAB formatting and there is a sufficiently
    # large userblock, write the new userblock. The same sort of error
    # handling is used.

    if options.MATLAB_compatible and userblock_size >= 128:
        # Get the time.
        now = datetime.datetime.now()

        # Construct the leading string. The MATLAB one looks like
        #
        # s = 'MATLAB 7.3 MAT-file, Platform: GLNXA64, Created on: ' \
        #     + now.strftime('%a %b %d %H:%M:%S %Y') \
        #     + ' HDF5 schema 1.00 .'
        #
        # Platform is going to be changed to CPython version

        v = sys.version_info

        s = 'MATLAB 7.3 MAT-file, Platform: CPython ' \
            + '{0}.{1}.{2}'.format(v.major, v.minor, v.micro) \
            + ', Created on: ' \
            + now.strftime('%a %b %d %H:%M:%S %Y') \
            + ' HDF5 schema 1.00 .'

        # Make the bytearray while padding with spaces up to 128-12
        # (the minus 12 is there since the last 12 bytes are special.

        b = bytearray(s + (128-12-len(s))*' ', encoding='utf-8')

        # Add 8 nulls (0) and the magic number (or something) that
        # MATLAB uses.

        b.extend(bytearray.fromhex('00000000 00000000 0002494D'))

        # Now, write it to the beginning of the file.

        try:
            fd = open(filename, 'r+b')
            fd.write(b)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        finally:
            fd.close()


# Set an empty list of path-string_array pairs to set the
# MATLAB_fields attributes on all the things that correspond to MATLAB
# structures.

_MATLAB_fields_pairs = []
