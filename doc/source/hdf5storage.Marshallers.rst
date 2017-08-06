hdf5storage.Marshallers
=======================

.. currentmodule:: hdf5storage.Marshallers

.. automodule:: hdf5storage.Marshallers

.. autosummary::

   TypeMarshaller
   NumpyScalarArrayMarshaller
   PythonScalarMarshaller
   PythonStringMarshaller
   PythonNoneMarshaller
   PythonDictMarshaller
   PythonListMarshaller
   PythonTupleSetDequeMarshaller


TypeMarshaller
--------------

.. autoclass:: TypeMarshaller
   :members: update_type_lookups, get_type_string, read, read_approximate, write, write_metadata
   :show-inheritance:

   .. autoinstanceattribute:: TypeMarshaller.required_parent_modules
      :annotation: = []

   .. autoinstanceattribute:: TypeMarshaller.required_modules
      :annotation: = []

   .. autoinstanceattribute:: TypeMarshaller.python_attributes
      :annotation: = {'Python.Type'}

   .. autoinstanceattribute:: TypeMarshaller.matlab_attributes
      :annotation: = {'H5PATH'}

   .. autoinstanceattribute:: TypeMarshaller.types
      :annotation: = []

   .. autoinstanceattribute:: TypeMarshaller.python_type_strings
      :annotation: = []

   .. autoinstanceattribute:: TypeMarshaller.matlab_classes
      :annotation: = []

   .. autoinstanceattribute:: TypeMarshaller.type_to_typestring
      :annotation: = dict()

   .. autoinstanceattribute:: TypeMarshaller.typestring_to_type
      :annotation: = dict()


NumpyScalarArrayMarshaller
--------------------------

.. autoclass:: NumpyScalarArrayMarshaller
   :members: read, write, write_metadata
   :show-inheritance:

   Handles the following ::

       python_attributes = {'Python.Type', 'Python.Shape', 'Python.Empty',
                            'Python.numpy.UnderlyingType',
                            'Python.numpy.Container', 'Python.Fields'}

       matlab_attributes = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
                            'MATLAB_int_decode', 'MATLAB_fields'}

       types = [np.ndarray, np.matrix,
                np.chararray, np.core.records.recarray,
                np.bool_, np.void,
                np.uint8, np.uint16, np.uint32, np.uint64,
                np.int8, np.int16, np.int32, np.int64,
                np.float16, np.float32, np.float64,
                np.complex64, np.complex128,
                np.bytes_, np.str_, np.object_]

       python_type_strings = ['numpy.ndarray', 'numpy.matrix',
                              'numpy.chararray', 'numpy.recarray',
                              'numpy.bool_', 'numpy.void',
                              'numpy.uint8', 'numpy.uint16',
                              'numpy.uint32', 'numpy.uint64', 'numpy.int8',
                              'numpy.int16', 'numpy.int32', 'numpy.int64',
                              'numpy.float16', 'numpy.float32', 'numpy.float64',
                              'numpy.complex64', 'numpy.complex128',
                              'numpy.bytes_', 'numpy.str_', 'numpy.object_']

       matlab_classes = ['logical', 'char', 'single', 'double', 'uint8',
                         'uint16', 'uint32', 'uint64', 'int8', 'int16',
                         'int32', 'int64', 'cell', 'canonical empty']


PythonScalarMarshaller
----------------------

.. autoclass:: PythonScalarMarshaller
   :members: read, write
   :show-inheritance:

   Handles the following ::

       python_attributes = {'Python.Type', 'Python.Shape', 'Python.Empty',
                            'Python.numpy.UnderlyingType',
                            'Python.numpy.Container', 'Python.Fields'}

       matlab_attributes = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
                            'MATLAB_int_decode'}

       types = [bool, int, float, complex]

       python_type_strings = ['bool', 'int', 'float', 'complex']

       matlab_classes = []


PythonStringMarshaller
----------------------

.. autoclass:: PythonStringMarshaller
   :members: read, write
   :show-inheritance:

   Handles the following ::

       python_attributes = {'Python.Type', 'Python.Shape', 'Python.Empty',
                            'Python.numpy.UnderlyingType',
                            'Python.numpy.Container', 'Python.Fields'}

       matlab_attributes = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
                            'MATLAB_int_decode'}

       types = [str, bytes, bytearray]

       python_type_strings = ['str', 'bytes', 'bytearray']

       matlab_classes = []


PythonNoneMarshaller
--------------------

.. autoclass:: PythonNoneMarshaller
   :members: read, write
   :show-inheritance:

   Handles the following ::

       python_attributes = {'Python.Type', 'Python.Shape', 'Python.Empty',
                            'Python.numpy.UnderlyingType',
                            'Python.numpy.Container', 'Python.Fields'}

       matlab_attributes = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
                            'MATLAB_int_decode'}

       types = [builtins.NoneType]

       python_type_strings = ['builtins.NoneType']

       matlab_classes = []


PythonDictMarshaller
--------------------

.. autoclass:: PythonDictMarshaller
   :members: read, write, write_metadata
   :show-inheritance:

   Handles the following ::

       python_attributes = {'Python.Type', 'Python.Fields'}

       matlab_attributes = {'H5PATH', 'MATLAB_class', 'MATLAB_fields'}

       types = [dict, collections.OrderedDict]

       python_type_strings = ['dict', 'collections.OrderedDict']

       matlab_classes = []


PythonListMarshaller
--------------------

.. autoclass:: PythonListMarshaller
   :members: read, write
   :show-inheritance:

   Handles the following ::

       python_attributes = {'Python.Type', 'Python.Shape', 'Python.Empty',
                            'Python.numpy.UnderlyingType',
                            'Python.numpy.Container', 'Python.Fields'}

       matlab_attributes = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
                            'MATLAB_int_decode'}

       types = [list]

       python_type_strings = ['list']

       matlab_classes = []


PythonTupleSetDequeMarshaller
-----------------------------

.. autoclass:: PythonTupleSetDequeMarshaller
   :members: read, write
   :show-inheritance:

   Handles the following ::

       python_attributes = {'Python.Type', 'Python.Shape', 'Python.Empty',
                            'Python.numpy.UnderlyingType',
                            'Python.numpy.Container', 'Python.Fields'}

       matlab_attributes = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
                            'MATLAB_int_decode'}

       types = [tuple, set, frozenset, collections.deque]

       python_type_strings = ['tuple', 'set', 'frozenset', 'collections.deque']

       matlab_classes = []

