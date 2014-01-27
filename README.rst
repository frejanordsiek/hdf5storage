Overview
========

This Python package provides high level utilities to read/write a
variety of Python types to/from HDF5 (Heirarchal Data Format) formatted
files. This package also provides support for MATLAB MAT v7.3 formatted
files, which are just HDF5 files with a different extension and some
extra meta-data.

The package's source code is found at
https://github.com/frejanordsiek/hdf5storage

Installation
============

This package will not work on Python < 3.0.

This package requires the numpy and h5py (>= 2.0) packages.

To install hdf5storage, download the package and run the command::

    python3 setup.py install

Hierarchal Data Format 5 (HDF5)
===============================

HDF5 files (see http://www.hdfgroup.org/HDF5/) are a commonly used file
format for exchange of numerical data. It has built in support for a
large variety of number formats (un/signed integers, floating point
numbers, strings, etc.) as scalars and arrays, enums and compound types.
It also handles differences in data representation on different hardware
platforms (endianness, different floating point formats, etc.). As can
be imagined from the name, data is represented in an HDF5 file in a
hierarchal form modelling a Unix filesystem (Datasets are equivalent to
files, Groups are equivalent to directories, and links are supported).

This package interfaces HDF5 files using the h5py package
(http://www.h5py.org/) as opposed to the tables package
(http://www.pytables.org/).

MATLAB MAT v7.3 file support
============================

MATLAB (http://www.mathworks.com/) MAT files version 7.3 and later are
HDF5 files with a different file extension (``.mat``) and a very
specific set of meta-data and storage conventions. This package provides
read and write support for a limited set of Python and MATLAB types.

Supported Types
===============

The supported Python and MATLAB types are given in the tables below.  The tables assume that one has imported numpy as::

    import numpy as np

The table gives which Python types can be read and written, the first
version of this package to support it, the numpy type it gets
converted to for storage (if type information is not written, that
will be what it is read back as) the MATLAB class it becomes if
targetting a MAT file, and the first version of this package to
support writing it so MATlAB can read it.

=============  =======  ==================  =======  ========
Python                                      MATLAB
------------------------------------------  -----------------
Type           Version  Converted to        Class    Version
=============  =======  ==================  =======  ========
bool           0.1      np.bool\_           logical  0.1
None           0.1      ``np.float64([])``  ``[]``   0.1
int            0.1      np.int64            int64    0.1
float          0.1      np.float64          double   0.1
complex        0.1      np.complex128       double   0.1
str            0.1      np.bytes\_          char     0.1 [1]_
bytes          0.1      np.bytes\_          char     0.1
bytearray      0.1      np.bytes\_          char     0.1
np.bool\_      0.1                          logical  0.1
np.uint8       0.1                          uint8    0.1
np.float16     0.1
np.float32     0.1                          single   0.1
np.float64     0.1                          double   0.1
np.complex32   0.1
np.complex64   0.1                          single   0.1
np.complex128  0.1                          double   0.1
np.str\_       0.1      np.uint32           uint32   0.1 [2]_
np.bytes\_     0.1                          char     0.1
dict           0.1                          struct   0.1 [3]_
=============  =======  ==================  =======  ========

.. [1] Converted to ASCII, so characters outside of that set are lost.
.. [2] Simply copied over as the uint32 versions of each UTF-32 character.
.. [3] All keys must be ``str``.

This table gives the MATLAB classes that can be read from a MAT file,
the first version of this package that can read them, and the Python
type they are read as.

============  =======  ================================
MATLAB Class  Version  Python Type
============  =======  ================================
logical       0.1      np.bool\_
single        0.1      np.float32 or np.complex64 [4]_
double        0.1      np.float64 or np.complex128 [4]_
uint8         0.1      np.uint8
uint16        0.1      np.uint16
uint32        0.1      np.uint32
uint64        0.1      np.uint64
int8          0.1      np.int8
int16         0.1      np.int16
int32         0.1      np.int32
int64         0.1      np.int64
struct        0.1      dict [5]_
============  =======  ================================

.. [4] Depends on whether there is a complex part or not.
.. [5] Structure arrays are not supported.
