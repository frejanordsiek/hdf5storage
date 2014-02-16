Overview
========

This Python package provides high level utilities to read/write a
variety of Python types to/from HDF5 (Heirarchal Data Format) formatted
files. This package also provides support for MATLAB MAT v7.3 formatted
files, which are just HDF5 files with a different extension and some
extra meta-data.

The package's documetation is found at
http://pythonhosted.org/hdf5storage/

The package's source code is found at
https://github.com/frejanordsiek/hdf5storage

The package is licensed under a 2-clause BSD license
(https://github.com/frejanordsiek/hdf5storage/blob/master/COPYING.txt).

Installation
============

This package only supports Python >= 2.6.

This package requires the numpy and h5py (>= 2.1) packages. An optional
dependency is the scipy package.

To install hdf5storage, download the package and run the command on
Python 3 ::

    python3 setup.py install

or the command on Python 2 ::

    python setup.py install

Python 2
========

This package was designed and written for Python 3, with Python 2.7 and
2.6 support added later. This does mean that a few things are a little
clunky in Python 2. Examples include supporting ``unicode`` keys for
dictionaries, not being able to import a structured ``numpy.ndarray`` if
any of its fields contain characters outside of ASCII, the ``int`` and
``long`` types both being mapped to the Python 3 ``int`` type, etc. The
storage format's metadata looks more familiar from a Python 3 standpoint
as well.

All documentation and examples are written in terms of Python 3 syntax
and types. Important Python 2 information beyond direct translations of
syntax and types will be pointed out.

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
(http://www.h5py.org/) as opposed to the PyTables package
(http://www.pytables.org/).

MATLAB MAT v7.3 file support
============================

MATLAB (http://www.mathworks.com/) MAT files version 7.3 and later are
HDF5 files with a different file extension (``.mat``) and a very
specific set of meta-data and storage conventions. This package provides
read and write support for a limited set of Python and MATLAB types.

SciPy (http://scipy.org/) has functions to read and write the older MAT
file formats. This package has functions modeled after the
``scipy.io.savemat`` and ``scipy.io.loadmat`` functions, that have the
same names and similar arguments. The dispatch to the SciPy versions if
the MAT file format is not an HDF5 based one.

Supported Types
===============

The supported Python and MATLAB types are given in the tables below.
The tables assume that one has imported collections and numpy as::

    import collections as cl
    import numpy as np

The table gives which Python types can be read and written, the first
version of this package to support it, the numpy type it gets
converted to for storage (if type information is not written, that
will be what it is read back as) the MATLAB class it becomes if
targetting a MAT file, and the first version of this package to
support writing it so MATlAB can read it.

=============  =======  ==========================  ===========  =============
Python                                              MATLAB
--------------------------------------------------  --------------------------
Type           Version  Converted to                Class        Version
=============  =======  ==========================  ===========  =============
bool           0.1      np.bool\_ or np.uint8       logical      0.1 [1]_
None           0.1      ``np.float64([])``          ``[]``       0.1
int            0.1      np.int64                    int64        0.1
float          0.1      np.float64                  double       0.1
complex        0.1      np.complex128               double       0.1
str            0.1      np.uint32/16                char         0.1 [2]_
bytes          0.1      np.bytes\_ or np.uint16     char         0.1 [3]_
bytearray      0.1      np.bytes\_ or np.uint16     char         0.1 [3]_
list           0.1      np.object\_                 cell         0.1
tuple          0.1      np.object\_                 cell         0.1
set            0.1      np.object\_                 cell         0.1
frozenset      0.1      np.object\_                 cell         0.1
cl.deque       0.1      np.object\_                 cell         0.1
dict           0.1                                  struct       0.1 [4]_
np.bool\_      0.1                                  logical      0.1
np.void        0.1
np.uint8       0.1                                  uint8        0.1
np.uint16      0.1                                  uint16       0.1
np.uint32      0.1                                  uint32       0.1
np.uint64      0.1                                  uint64       0.1
np.uint8       0.1                                  int8         0.1
np.int16       0.1                                  int16        0.1
np.int32       0.1                                  int32        0.1
np.int64       0.1                                  int64        0.1
np.float16     0.1
np.float32     0.1                                  single       0.1
np.float64     0.1                                  double       0.1
np.complex64   0.1                                  single       0.1
np.complex128  0.1                                  double       0.1
np.str\_       0.1      np.uint32/16                char/uint32  0.1 [2]_
np.bytes\_     0.1      np.bytes\_ or np.uint16     char         0.1 [3]_
np.object\_    0.1                                  cell         0.1
np.ndarray     0.1      [5]_ [6]_                   [5]_ [6]_    0.1 [5]_ [7]_
np.matrix      0.1      [5]_                        [5]_         0.1 [5]_
np.chararray   0.1      [5]_                        [5]_         0.1 [5]_
np.recarray    0.1      structured np.ndarray       [5]_ [6]_    0.1 [5]_
=============  =======  ==========================  ===========  =============

.. [1] Depends on the selected options. Always ``np.uint8`` when doing
       MATLAB compatiblity, or if the option is explicitly set.
.. [2] Depends on the selected options and whether it can be converted
       to UTF-16 without using doublets. If the option is explicity set
       (or implicitly through doing MATLAB compatibility) and it can be
       converted to UTF-16 without losing any characters that can't be
       represented in UTF-16 or using UTF-16 doublets (MATLAB doesn't
       support them), then it is written as ``np.uint16`` in UTF-16
       encoding. Otherwise, it is stored at ``np.uint32`` in UTF-32
       encoding.
.. [3] Depends on the selected options. If the option is explicitly set
       (or implicitly through doing MATLAB compatibility), it will be
       stored as ``np.uint16`` in UTF-16 encoding. Otherwise, it is just
       written as ``np.bytes_``.
.. [4] All keys must be ``str`` in Python 3 or ``unicode`` in Python 2.
.. [5] Container types are only supported if their underlying dtype is
       supported. Data conversions are done based on its dtype.
.. [6] Structured ``np.ndarray`` s (have fields in their dtypes) can be
       written as an HDF5 COMPOUND type or as an HDF5 Group with Datasets
       holding its fields (either the values directly, or as an HDF5
       Reference array to the values for the different elements of the
       data).
.. [7] Structured ``np.ndarray`` s with no elements, when written like a
       structure, will not be read back with the right dtypes for their
       fields (will all become 'object').

This table gives the MATLAB classes that can be read from a MAT file,
the first version of this package that can read them, and the Python
type they are read as.

===============  =======  =================================
MATLAB Class     Version  Python Type
===============  =======  =================================
logical          0.1      np.bool\_
single           0.1      np.float32 or np.complex64 [8]_
double           0.1      np.float64 or np.complex128 [8]_
uint8            0.1      np.uint8
uint16           0.1      np.uint16
uint32           0.1      np.uint32
uint64           0.1      np.uint64
int8             0.1      np.int8
int16            0.1      np.int16
int32            0.1      np.int32
int64            0.1      np.int64
char             0.1      np.str\_
struct           0.1      structured np.ndarray
cell             0.1      np.object\_
canonical empty  0.1      ``np.float64([])``
===============  =======  =================================

.. [8] Depends on whether there is a complex part or not.
