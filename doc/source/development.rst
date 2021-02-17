.. currentmodule:: hdf5storage

=======================
Development Information
=======================

The source code can be found on Github at
https://github.com/frejanordsiek/hdf5storage

Package Overview
================

The package is currently a pure Python package; using no Cython, C/C++,
or other languages.

Also, pickling is not used at all and should not be added. It is a
security risk since pickled data is read through the interpreter
allowing arbitrary code (which could be malicious) to be executed in the
interpreter. One wants to be able to read possibly HDF5 and MAT files
from untrusted sources, so pickling is avoided in this package.

The :py:mod:`hdf5storage` module contains the high level reading and
writing functions, as well as the :py:class:`Options` class for
encapsulating all the various options governing how data is read and
written. The high level reading and writing functions can either be
given an :py:class:`Options` object, or be given the keyword arguments
that its constructur takes (they will make one from those
arguments). There is also the :py:class:`MarshallerCollection` which
holds all the Marshallers (more below) and provides functions to find
the appropriate Marshaller given the ``type`` of a Python object, the
type string used for the 'Python.Type' Attribute, or the MATLAB class
string (contained in the 'MATLAB_class' Attribute). One can give the
collection additional user provided Marshallers.

The :py:mod:`hdf5storage.exceptions` module contains the special
exceptions/errors required for this package not covered by existing
Python exceptions/errors or those from the h5py package.

:py:mod:`hdf5storage.Marshallers` contains all the Marshallers for the
different Python data types that can be read from or written to an HDF5
file. They are all automitically added to any
:py:class:`MarshallerCollection` which inspects this module and grabs
all classes within it (if a class other than a Marshaller is added to
this module, :py:class:`MarshallerCollection` will need to be
modified). All Marshallers need to provide the same interface as
:py:class:`Marshallers.TypeMarshaller`, which is the base class for all
Marshallers in this module, and should probably be inherited from by any
custom Marshallers that one would write (while it can't marshall any
types, it does have some useful built in functionality). The main
Marshaller in the module is
:py:class:`Marshallers.NumpyScalarArrayMarshaller`, which can marshall
most Numpy types. All the other built in Marshallers other than
:py:class:`Marshallers.PythonDictMarshaller` inherit from it since they
convert their types to and from Numpy types and use the inherited
functions to do the actual work with the HDF5 file.

:py:mod:`hdf5storage.utilities` contains many functions that are used
throughout the pacakge, especially by the Marshallers. They include the
:py:func:`utilities.LowLevelFile` class for low level reading and
writing, which is passed to the methods of the Marshallers. Any
Marshaller that needs to read or write a nested object within a Group or
Python object must call its methods or other functions in the
:py:mod:`hdf5storage.utilities` module. There are also several functions
to get, set, and delete different kinds of HDF5 Attributes (handle
things such as them already existing, not existing, etc). Then there
functions to convert between different string representations, as well
as encode for writing and decode after reading complex types.


TODO
====

There are several features that need to be added, bugs that need to be
fixed, etc.

Standing Bugs
-------------

* Structured ``np.ndarray`` with no elements, when
  :py:attr:`Options.structured_numpy_ndarray_as_struct` is set, are not
  written in a way that the dtypes for the fields can be restored when
  it is read back from file.

Features to Add
---------------

* Marshallers for more Python types.
* Marshallers to be able to read the following MATLAB types

  * Categorical Arrays
  * Tables
  * Maps
  * Time Series
  * Classes (could be hard if they don't look like a struct in file)
  * Function Handles (wouldn't be able run in Python, but could at least
    manipulate)

* A ``whosmat`` function like the SciPy one :py:func:`scipy.io.whosmat`.
* A function to find and delete Datasets and Groups inside the Group
  :py:attr:`Options.group_for_references` that are not referenced by
  other Datasets in the file.

