Overview
========

This Python package provides high level utilities to read/write a
variety of Python types to/from HDF5 (Heirarchal Data Format) formatted
files. This package also provides support for MATLAB MAT v7.3 formatted
files, which are just HDF5 files with a different extension and some
extra meta-data.

All of this is done without pickling data. Pickling is bad for security
because it allows arbitrary code to be executed in the interpreter. One
wants to be able to read possibly HDF5 and MAT files from untrusted
sources, so pickling is avoided in this package.

The package's documetation is found at
http://pythonhosted.org/hdf5storage/

The package's source code is found at
https://github.com/frejanordsiek/hdf5storage

The package is licensed under a 2-clause BSD license
(https://github.com/frejanordsiek/hdf5storage/blob/master/COPYING.txt).

Installation
============

Dependencies
------------

This package only supports Python >= 3.5. Python < 3.5 support was dropped
in version 0.2.

This package requires the python packages to run

* `numpy <https://pypi.org/project/numpy>`_
* `h5py <https://pypi.org/project/h5py>`_ >= 2.3
* `setuptools <https://pypi.org/project/setuptools>`_

Note that support for `h5py <https://pypi.org/project/h5py>`_ 2.1.x and 2.2.x
has been dropped in version 0.2.
This package also has the following optional dependencies

* `scipy <https://pypi.org/project/scipy>`_

Installing by pip
-----------------

This package is on `PyPI <https://pypi.org>`_ at
`hdf5storage <https://pypi.org/project/hdf5storage>`_. To install hdf5storage
using pip, run the command::

    pip install hdf5storage

Installing from Source
----------------------

To install hdf5storage from source, the
`setuptools <https://pypi.org/project/setuptools>`_ and
`wheel <https://pypi.org/project/wheel>`_ are required. Download this package
and then install the dependencies ::

    pip install -r requirements.txt

Then to install the package, run either ::

    pip install .

or, using the legacy :file:`setup.py` script ::

    python setup.py install

Running Tests
-------------

For testing, the package `pytest <https://pypi.org/project/pytest>`_
(>= 5.0) is additionally required. There are some tests that require
Matlab and `scipy <https://pypi.org/project/scipy>`_ to be installed
and be in the executable path respectively. In addition, there are some
tests that require `Julia <http://julialang.org/>`_ with the
`MAT <https://github.com/simonster/MAT.jl>`_ package. Not having them
means that those tests cannot be run (they will be skipped) but all
the other tests will run. To install all testing dependencies, other
than `scipy <https://pypi.org/project/scipy>`_, Julia, Matlab run ::

    pip install -r requirements_tests.txt.

To run the tests ::

    pytest


Building Documentation
----------------------

The documentation additionally requires the following packages

* `sphinx <https://pypi.org/project/sphinx>`_ >= 1.7
* `sphinx_rtd_theme <https://pypi.org/project/sphinx-rtd-theme>`_

The documentation dependencies can be installed by ::

    pip install -r requirements_doc.txt

To build the HTML documentation, run either ::

    sphinx-build doc/source doc/build/html

or, using the legacy :file:`setup.py` script ::

    python setup.py build_sphinx

Python 2
========

This package no longer supports Python 2.6 and 2.7. This package was
designed and written for Python 3, then backported to Python 2.x, and
then support dropped. But it can still read files made by version 0.1.x
of this library with Python 2.x, and this package still tries to write
files compatible with 0.1.x when possible.

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

+--------------------+---------+-------------------------+-------------+---------+-------------------+
| Python                                                 | MATLAB                | Notes             |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| Type               | Version | Converted to            | Class       | Version |                   |
+====================+=========+=========================+=============+=========+===================+
| bool               | 0.1     | np.bool\_ or np.uint8   | logical     | 0.1     | [1]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| None               | 0.1     | ``np.float64([])``      | ``[]``      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| Ellipsis           | 0.2     | ``np.float64([])``      | ``[]``      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| NotImplemented     | 0.2     | ``np.float64([])``      | ``[]``      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| int                | 0.1     | np.int64 or np.bytes\_  | int64       | 0.1     | [2]_ [3]_         |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| long               | 0.1     | np.int64 or np.bytes\_  | int64       | 0.1     | [3]_ [4]_         |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| float              | 0.1     | np.float64              | double      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| complex            | 0.1     | np.complex128           | double      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| str                | 0.1     | np.uint32/16            | char        | 0.1     | [5]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| bytes              | 0.1     | np.bytes\_ or np.uint16 | char        | 0.1     | [6]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| bytearray          | 0.1     | np.bytes\_ or np.uint16 | char        | 0.1     | [6]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| list               | 0.1     | np.object\_             | cell        | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| tuple              | 0.1     | np.object\_             | cell        | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| set                | 0.1     | np.object\_             | cell        | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| frozenset          | 0.1     | np.object\_             | cell        | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| cl.deque           | 0.1     | np.object\_             | cell        | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| cl.ChainMap        | 0.2     | np.object\_             | cell        | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| dict               | 0.1     |                         | struct      | 0.1     | [7]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| cl.OrderedDict     | 0.2     |                         | struct      | 0.2     | [7]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| cl.Counter         | 0.2     |                         | struct      | 0.2     | [7]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| slice              | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| range              | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| datetime.timedelta | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| datetime.timezone  | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| datetime.date      | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| datetime.time      | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| datetime.datetime  | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| fractions.Fraction | 0.2     |                         | struct      | 0.2     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.bool\_          | 0.1     |                         | logical     | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.void            | 0.1     |                         |             |         |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.uint8           | 0.1     |                         | uint8       | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.uint16          | 0.1     |                         | uint16      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.uint32          | 0.1     |                         | uint32      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.uint64          | 0.1     |                         | uint64      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.uint8           | 0.1     |                         | int8        | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.int16           | 0.1     |                         | int16       | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.int32           | 0.1     |                         | int32       | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.int64           | 0.1     |                         | int64       | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.float16         | 0.1     |                         |             |         | [8]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.float32         | 0.1     |                         | single      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.float64         | 0.1     |                         | double      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.complex64       | 0.1     |                         | single      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.complex128      | 0.1     |                         | double      | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.str\_           | 0.1     | np.uint32/16            | char/uint32 | 0.1     | [5]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.bytes\_         | 0.1     | np.bytes\_ or np.uint16 | char        | 0.1     | [6]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.object\_        | 0.1     |                         | cell        | 0.1     |                   |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.ndarray         | 0.1     | *see notes*             | *see notes* | 0.1     | [9]_  [10]_ [11]_ |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.matrix          | 0.1     | *see notes*             | *see notes* | 0.1     | [9]_ [12]_        |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.chararray       | 0.1     | *see notes*             | *see notes* | 0.1     | [9]_              |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.recarray        | 0.1     | structured np.ndarray   | *see notes* | 0.1     | [9]_ [10]_        |
+--------------------+---------+-------------------------+-------------+---------+-------------------+
| np.dtype           | 0.2     | np.bytes\_ or np.uint16 | char        | 0.2     | [6]_ [13]_        |
+--------------------+---------+-------------------------+-------------+---------+-------------------+

.. [1] Depends on the selected options. Always ``np.uint8`` when doing
       MATLAB compatiblity, or if the option is explicitly set.
.. [2] In Python 2.x with the 0.1.x version of this package, it may be
       read back as a ``long`` if it can't fit in the size of an
       ``int``.
.. [3] Stored as a ``np.int64`` if it is small enough to fit. Otherwise
       its decimal string representation is stored as an ``np.bytes_``
       for hdf5storage >= 0.2 (error in earlier versions).
.. [4] Type found only in Python 2.x. Python 2.x's ``long`` and ``int``
       are unified into a single ``int`` type in Python 3.x. Read as an
       ``int`` in Python 3.x.
.. [5] Depends on the selected options and whether it can be converted
       to UTF-16 without using doublets. If the option is explicity set
       (or implicitly when doing MATLAB compatibility) and it can be
       converted to UTF-16 without losing any characters that can't be
       represented in UTF-16 or using UTF-16 doublets (MATLAB doesn't
       support them), then it is written as ``np.uint16`` in UTF-16
       encoding. Otherwise, it is stored at ``np.uint32`` in UTF-32
       encoding.
.. [6] Depends on the selected options. If the option is explicitly set
       (or implicitly when doing MATLAB compatibility), it will be
       stored as ``np.uint16`` in UTF-16 encoding unless it has
       non-ASCII characters in which case a ``NotImplementedError`` is
       thrown). Otherwise, it is just written as ``np.bytes_``.
.. [7] Stored either as each key-value as their own Dataset or as two
       Datasets, one for keys and one for values. The former is used if
       all keys can be converted to ``str`` and they don't have null
       characters (``'\x00'``) or forward slashes (``'/'``) in them.
       Otherwise, the latter format is used.
.. [8] ``np.float16`` are not supported for h5py versions before
       ``2.2``. Version ``2.3`` or higher is required for this package
       since version ``0.2``.
.. [9] Container types are only supported if their underlying dtype is
       supported. Data conversions are done based on its dtype.
.. [10] Structured ``np.ndarray`` s (have fields in their dtypes) can be
        written as an HDF5 COMPOUND type or as an HDF5 Group with
        Datasets holding its fields (either the values directly, or as
        an HDF5 Reference array to the values for the different elements
        of the data). Can only be written as an HDF5 COMPOUND type if
        none of its field are of dtype ``'object'``. Field names cannot
        have null characters (``'\x00'``) and, when writing as an HDF5
        GROUP, forward slashes (``'/'``) in them.
.. [11] Structured ``np.ndarray`` s with no elements, when written like a
        structure, will not be read back with the right dtypes for their
        fields (will all become 'object').
.. [12] Will be read back as a ``np.ndarray`` if the ``np.matrix`` class
        is removed.
.. [13] Stored in their string representation.

This table gives the MATLAB classes that can be read from a MAT file,
the first version of this package that can read them, and the Python
type they are read as.

+-----------------+---------+-------------------------------------+
| MATLAB Class    | Version | Python Type                         |
+=================+=========+=====================================+
| logical         | 0.1     | np.bool\_                           |
+-----------------+---------+-------------------------------------+
| single          | 0.1     | np.float32 or np.complex64 [14]_    |
+-----------------+---------+-------------------------------------+
| double          | 0.1     | np.float64 or np.complex128 [14]_   |
+-----------------+---------+-------------------------------------+
| uint8           | 0.1     | np.uint8                            |
+-----------------+---------+-------------------------------------+
| uint16          | 0.1     | np.uint16                           |
+-----------------+---------+-------------------------------------+
| uint32          | 0.1     | np.uint32                           |
+-----------------+---------+-------------------------------------+
| uint64          | 0.1     | np.uint64                           |
+-----------------+---------+-------------------------------------+
| int8            | 0.1     | np.int8                             |
+-----------------+---------+-------------------------------------+
| int16           | 0.1     | np.int16                            |
+-----------------+---------+-------------------------------------+
| int32           | 0.1     | np.int32                            |
+-----------------+---------+-------------------------------------+
| int64           | 0.1     | np.int64                            |
+-----------------+---------+-------------------------------------+
| char            | 0.1     | np.str\_                            |
+-----------------+---------+-------------------------------------+
| struct          | 0.1     | structured np.ndarray or dict [15]_ |
+-----------------+---------+-------------------------------------+
| cell            | 0.1     | np.object\_                         |
+-----------------+---------+-------------------------------------+
| canonical empty | 0.1     | ``np.float64([])``                  |
+-----------------+---------+-------------------------------------+

.. [14] Depends on whether there is a complex part or not.
.. [15] Controlled by an option.


Versions
========

0.2. Feature release adding/changing the following, including some API breaking changes.
     * Issues #50 and #84. Python < 3.5 support dropped.
     * Issue #53. h5py 2.1.x and 2.2.x  support dropped.
     * Issue #85. Changed to using the PEP 518 method of specifying
       build dependencies from using the older ``ez_setup.py`` to ensure
       ``setuptools`` was available for building.
     * Added a file object class :py:class:`hdf5storage.File` for
       opening a file and doing multiple read and/or write calls on the
       same file.
     * ``reads``, ``read``, and ``loadmat`` now raise a ``KeyError`` if
       an object can't be found as opposed to a
       ``hdf5storage.exceptions.CantReadError``.
     * Issue #88. Made it so that objects inside the Group specified by
       ``Options.group_for_references`` cannot be read from or written
       to directly by the external API.
     * Issue #64 and PR #87. Added ``structs_as_dicts`` that will cause MATLAB structs
       to be read as ``dict`` instead of structured ``np.dnarray``.
     * Issue #60. Platform label in the MAT file header changed to
       ``hdf5storage VERSION`` from ``CPython VERSION``.
     * Issue #61. User provided marshallers must inherit from
       ``Marshallers.TypeMarshaller``. Before, they just had to provide
       the same interface.
     * Issue #78. Added the ability to pass object paths as
       ``pathlib.PurePath`` (and descendants) objects.
     * Issue #62. The priority ordering between builtin, plugin, and
       user provided marshallers can be selected. The default is now
       builtin, plugin, user; as opposed to user, builtin in the 0.1.x
       branch.
     * Issue #65. Added the ability to load marshallers from other python
       packages via plugin using the
       ``'hdf5storage.marshallers.plugins'`` entry point in their
       ``setup.py`` files. Third party marshallers are not loaded into
       the default initial ``MarshallerCollection``. Users who want
       to use them must call ``make_new_default_MarshallerCollection``
       with the ``load_plugins`` option set to ``True``.
     * Issue #66. A version Marshaller API has been added to make it
       easier for developers to write plugin marshallers without having
       to do extensive checking of the ``hdf5storage`` package version.
       The Marshaller API version will advance separately from the
       package version. The initial version is ``'1.0'``.
     * Fixed bugs in ``savemat`` and ``loadmat`` with appening the file
       extension to filenames that are ``bytes``.
     * Issue #27. Added support for paths with null characters, slashes,
       and leading periods. It is used for the field names of structured
       numpy ndarrays as well as the keys of ``dict`` like objects when
       writing their values to individual Datasets.
     * Issue #89. ``Marshallers.PythonNoneMarshaller`` was renamed to
       ``Marshallers.PythonNoneEllipsisNotImplementedMarshaller`` and
       support added for the ``Ellipsis`` and ``NotImplemented`` types.
     * The ``write`` method of all marshallers now must return the written
       HDF5 Group or Dataset (or ``None`` if unsuccessful).
     * Issue #49. Changed marshaller types and their handling code to
       support marshallers that handle types in modules that may not be
       available or should not be imported until needed. If the the
       required modules are not available, an approximate version of
       the data is read using the ``read_approximate`` method of the
       marshaller instead of the ``read`` method. The required modules,
       if available, can either be imported immediately upon the
       creation of the ``MarshallerCollection`` or they can be imported
       only when the marshaller is needed for actual use (lazy loading).
     * Changed the type of the ``types``, ``python_type_strings``, and
       ``matlab_classes`` attributes of ``TypeMarshaller`` to ``tuple``
       from ``list``.
     * Issue #52. Added the usage of a default ``MarshallerCollection``
       which is used whenever creating a new ``Options`` without
       a ``MarshallerCollection`` specified. The default can be
       obtained using ``get_default_MarshallerCollection`` and a new
       default can be generated using
       ``make_new_default_MarshallerCollection``. This is useful if
       one wants to override the default lazy loading behavior.
     * Issues #42 and #106. read and write functions moved from the ``lowlevel``
       and ``Marshallers`` modules to the ``utilities`` module and
       the ``lowlevel`` module renamed to ``exceptions`` since that is
       all that remains in it. The functions to read/write Datasets and Groups
       were replaced with a wrapper class ``LowLevelFile`` with methods
       that are similar.
     * Issue #106. Marshallers are passed a ``utilities.LowLevelFile`` object
       as the first argument (``f``) instead of the file handle (``h5py.File``)
       with the ``Options`` as the keyword argument ``options``.
     * Ability to write Python 3.x ``int`` and Python 2.x ``long`` that
       are too large to fit into ``np.int64``. Doing so no longer
       raises an exception.
     * Ability to write ``np.bytes_`` with non-ASCII characters in them.
       Doing so no longer raises an exception.
     * Issue #24 and #25. Added support for writing ``dict`` like
       objects with keys that are not all ``str`` without null and ``'/'``
       characters. Two new options, ``'dict_like_keys_name'`` and
       ``'dict_like_values_name'`` control how they are stored if the
       keys are not string like, can't be converted to Python 3.x
       ``str`` or Python 2.x ``unicode``, or have null or ``'/'``
       characters.
     * Issues #38 and #91. Added support for ``cl.OrderedDict`` and
       ``cl.Counter``. The were added added to
       ``Marshallers.PythonDictMarshaller`` and the new
       ``Marshallers.PythonCounterMarshaller`` respectively.
     * Issue #80. Added a support for ``slice`` and ``range`` with the new
       marshaller ``Marshallers.PythonSliceRangeMarshaller``.
     * Issue #92. Added support for ``collections.ChainMap`` with the new
       marshaller ``Marshallers.PythonChainMap``.
     * Issue #93. Added support for ``fractions.Fraction`` with the new
       marshaller ``Marshallers.PythonFractionMarshaller``.
     * Issue #99. Added support for ``np.dtype`` with the new marshaller
       ``Marshallers.NumpyDtypeMarshaller``.
     * Issue #95. Added support for objects in the ``datetime`` module
       (only ``datetime.tzinfo`` class implemented is
       ``datetime.timezone``) in the new marshaller
       ``Marshallers.PythonDatetimeObjsMarshaller``.
     * Issue #107. Added handling of the eventual removal of the
       ``numpy.matrix`` class since it is pending deprecation. If the class
       is not available, objects that were written as one are read back as
       ``numpy.ndarray``.
     * Added the utility function ``utilities.convert_dtype_to_str`` to convet
       ``numpy.dtype`` to ``str`` in a way they can be converted back by
       passing through ``ast.literal_eval`` and then ``numpy.dtype``.
     * Issue #40. Made it so that tests use tempfiles instead of
       using hardcoded filenames in the local directory.
     * Issue #41. Added tests using the Julia MAT package to check
       interop with Matlab v7.3 MAT files.
     * Issue #39. Documentation now uses the napoleon extension in
       Sphinx >= 1.3 as a replacement for numpydoc package.
     * Changed documentation theme to ``sphinx_rtd_theme``.
     * Issue #55. Major performance increases by reducing the overhead
       involved with reading and writing each Dataset and Group.
     * Issue #96. Changed unit testing to use
       `pytest <https://pypi.org/project/pytest>`_ instead of
       `nose <https://pypi.org/project/nose>`_.

0.1.17. Bugfix and deprecation workaround release that fixed the following.
        * Issue #109. Fixed the fix Issue #102 for 32-bit platforms (previous
          fix was segfaulting).
        * Moved to using ``pkg_resources.parse_version`` from ``setuptools``
          with ``distutils.version`` classes as a fallback instead of just the
          later to prepare for the removal of ``distutils`` (PEP 632) and
          prevent warnings on Python versions where it is marked as deprecated.
        * Issue #110. Changed all uses of the ``tostring`` method on numpy types
          to using ``tobytes`` if available, with ``tostring`` as the fallback
          for old versions of numpy where it is not.

0.1.16. Bugfix release that fixed the following bugs.
        * Issue #81 and #82. ``h5py.File`` will require the mode to be
          passed explicitly in the future. All calls without passing it were
          fixed to pass it.
        * Issue #102. Added support for h5py 3.0 and 3.1.
        * Issue #73. Fixed bug where a missing variable in ``loadmat`` would
          cause the function to think that the file is a pre v7.3 format MAT
          file fall back to ``scipy.io.loadmat`` which won't work since the file
          is a v7.3 format MAT file.
        * Fixed formatting issues in the docstrings and the documentation that
          prevented the documentation from building.

0.1.15. Bugfix release that fixed the following bugs.
        * Issue #68. Fixed bug where ``str`` and ``numpy.unicode_``
          strings (but not ndarrays of them) were saved in
          ``uint32`` format regardless of the value of
          ``Options.convert_numpy_bytes_to_utf16``.
        * Issue #70. Updated ``setup.py`` and ``requirements.txt`` to specify
          the maximum versions of numpy and h5py that can be used for specific
          python versions (avoid version with dropped support).
        * Issue #71. Fixed bug where the ``'python_fields'`` attribute wouldn't
          always be written when doing python metadata for data written in
          a struct-like fashion. The bug caused the field order to not be
          preserved when writing and reading.
        * Fixed an assertion in the tests to handle field re-ordering when
          no metadata is used for structured dtypes that only worked on
          older versions of numpy.
        * Issue #72. Fixed bug where python collections filled with ndarrays
          that all have the same shape were converted to multi-dimensional
          object ndarrays instead of a 1D object ndarray of the elements.

0.1.14. Bugfix release that also added a couple features.
        * Issue #45. Fixed syntax errors in unicode strings for Python
          3.0 to 3.2.
        * Issues #44 and #47. Fixed bugs in testing of conversion and
          storage of string types.
        * Issue #46. Fixed raising of ``RuntimeWarnings`` in tests due
          to signalling NaNs.
        * Added requirements files for building documentation and
          running tests.
        * Made it so that Matlab compatability tests are skipped if
          Matlab is not found, instead of raising errors.

0.1.13. Bugfix release fixing the following bug.
        * Issue #36. Fixed bugs in writing ``int`` and ``long`` to HDF5
          and their tests on 32 bit systems.

0.1.12. Bugfix release fixing the following bugs. In addition, copyright years were also updated and notices put in the Matlab files used for testing.
        * Issue #32. Fixed transposing before reshaping ``np.ndarray``
          when reading from HDF5 files where python metadata was stored
          but not Matlab metadata.
        * Issue #33. Fixed the loss of the number of characters when
          reading empty numpy string arrays.
        * Issue #34. Fixed a conversion error when ``np.chararray`` are
          written with Matlab metadata.

0.1.11. Bugfix release fixing the following.
        * Issue #30. Fixed ``loadmat`` not opening files in read mode.

0.1.10. Minor feature/performance fix release doing the following.
        * Issue #29. Added ``writes`` and ``reads`` functions to write
          and read more than one piece of data at a time and made
          ``savemat`` and ``loadmat`` use them to increase performance.
          Previously, the HDF5 file was being opened and closed for
          each piece of data, which impacted performance, especially
	  for large files.

0.1.9. Bugfix and minor feature release doing the following.
       * Issue #23. Fixed bug where a structured ``np.ndarray`` with
         a field name of ``'O'`` could never be written as an
         HDF5 COMPOUND Dataset (falsely thought a field's dtype was
         object).
       * Issue #6. Added optional data compression and the storage of
         data checksums. Controlled by several new options.

0.1.8. Bugfix release fixing the following two bugs.
       * Issue #21. Fixed bug where the ``'MATLAB_class'`` Attribute is
         not set when writing ``dict`` types when writing MATLAB
         metadata.
       * Issue #22. Fixed bug where null characters (``'\x00'``) and
         forward slashes (``'/'``) were allowed in ``dict`` keys and the
         field names of structured ``np.ndarray`` (except that forward
         slashes are allowed when the
         ``structured_numpy_ndarray_as_struct`` is not set as is the
         case when the ``matlab_compatible`` option is set). These
         cause problems for the ``h5py`` package and the HDF5 library.
         ``NotImplementedError`` is now thrown in these cases.

0.1.7. Bugfix release with an added compatibility option and some added test code. Did the following.
       * Fixed an issue reading variables larger than 2 GB in MATLAB
         MAT v7.3 files when no explicit variable names to read are
         given to ``hdf5storage.loadmat``. Fix also reduces memory
         consumption and processing time a little bit by removing an
         unneeded memory copy.
       * ``Options`` now will accept any additional keyword arguments it
         doesn't support, ignoring them, to be API compatible with future
         package versions with added options.
       * Added tests for reading data that has been compressed or had
         other HDF5 filters applied.

0.1.6. Bugfix release fixing a bug with determining the maximum size of a Python 2.x ``int`` on a 32-bit system.

0.1.5. Bugfix release fixing the following bug.
       * Fixed bug where an ``int`` could be stored that is too big to
         fit into an ``int`` when read back in Python 2.x. When it is
         too big, it is converted to a ``long``.
       * Fixed a bug where an ``int`` or ``long`` that is too big to
	 big to fit into an ``np.int64`` raised the wrong exception.
       * Fixed bug where fields names for structured ``np.ndarray`` with
         non-ASCII characters (assumed to be UTF-8 encoded in
         Python 2.x) can't be read or written properly.
       * Fixed bug where ``np.bytes_`` with non-ASCII characters can
         were converted incorrectly to UTF-16 when that option is set
         (set implicitly when doing MATLAB compatibility). Now, it throws
         a ``NotImplementedError``.

0.1.4. Bugfix release fixing the following bugs. Thanks goes to `mrdomino <https://github.com/mrdomino>`_ for writing the bug fixes.
       * Fixed bug where ``dtype`` is used as a keyword parameter of
         ``np.ndarray.astype`` when it is a positional argument.
       * Fixed error caused by ``h5py.__version__`` being absent on
         Ubuntu 12.04.

0.1.3. Bugfix release fixing the following bug.
       * Fixed broken ability to correctly read and write empty
         structured ``np.ndarray`` (has fields).

0.1.2. Bugfix release fixing the following bugs.
       * Removed mistaken support for ``np.float16`` for h5py versions
         before ``2.2`` since that was when support for it was
         introduced.
       * Structured ``np.ndarray`` where one or more fields is of the
         ``'object'`` dtype can now be written without an error when
         the ``structured_numpy_ndarray_as_struct`` option is not set.
         They are written as an HDF5 Group, as if the option was set.
       * Support for the ``'MATLAB_fields'`` Attribute for data types
         that are structures in MATLAB has been added for when the
         version of the h5py package being used is ``2.3`` or greater.
         Support is still missing for earlier versions (this package
         requires a minimum version of ``2.1``).
       * The check for non-unicode string keys (``str`` in Python 3 and
         ``unicode`` in Python 2) in the type ``dict`` is done right
         before any changes are made to the HDF5 file instead of in the
         middle so that no changes are applied if an invalid key is
         present.
       * HDF5 userblock set with the proper metadata for MATLAB support
         right at the beginning of when data is being written to an HDF5
         file instead of at the end, meaning the writing can crash and
         the file will still be a valid MATLAB file.

0.1.1. Bugfix release fixing the following bugs.
       * ``str`` is now written like ``numpy.str_`` instead of
         ``numpy.bytes_``.
       * Complex numbers where the real or imaginary part are ``nan``
         but the other part are not are now read correctly as opposed
         to setting both parts to ``nan``.
       * Fixed bugs in string conversions on Python 2 resulting from
         ``str.decode()`` and ``unicode.encode()`` not taking the same
         keyword arguments as in Python 3.
       * MATLAB structure arrays can now be read without producing an
         error on Python 2.
       * ``numpy.str_`` now written as ``numpy.uint16`` on Python 2 if
         the ``convert_numpy_str_to_utf16`` option is set and the
         conversion can be done without using UTF-16 doublets, instead
         of always writing them as ``numpy.uint32``.

0.1. Initial version.
