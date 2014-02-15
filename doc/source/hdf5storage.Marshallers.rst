hdf5storage.Marshallers
=======================

.. currentmodule:: hdf5storage.Marshallers

.. automodule:: hdf5storage.Marshallers

.. autosummary::

   write_object_array
   read_object_array
   TypeMarshaller
   NumpyScalarArrayMarshaller
   PythonScalarMarshaller
   PythonStringMarshaller
   PythonNoneMarshaller
   PythonDictMarshaller
   PythonListMarshaller
   PythonTupleSetDequeMarshaller


write_object_array
------------------

.. autofunction:: write_object_array


read_object_array
------------------

.. autofunction:: read_object_array


TypeMarshaller
--------------

.. autoclass:: TypeMarshaller
   :members: get_type_string, read, write, write_metadata 
   :show-inheritance:

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


NumpyScalarArrayMarshaller
--------------------------

.. autoclass:: NumpyScalarArrayMarshaller
   :members: read, write, write_metadata 
   :show-inheritance:

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.types
      :annotation: = [np.ndarray, np.matrix,
                      np.chararray, np.core.records.recarray,
                      np.bool_, np.void,
                      np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float16, np.float32, np.float64,
                      np.complex64, np.complex128,
                      np.bytes_, np.str_, np.object_]

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.python_type_strings
      :annotation: = ['numpy.ndarray', 'numpy.matrix',
                      'numpy.chararray', 'numpy.recarray',
                      'numpy.bool_', 'numpy.void',
                      'numpy.uint8', 'numpy.uint16',
                      'numpy.uint32', 'numpy.uint64', 'numpy.int8',
		      'numpy.int16', 'numpy.int32', 'numpy.int64',
                      'numpy.float16', 'numpy.float32', 'numpy.float64',
                      'numpy.complex64', 'numpy.complex128',
                      'numpy.bytes_', 'numpy.str_', 'numpy.object_']

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.matlab_classes
      :annotation: = ['logical', 'char', 'single', 'double', 'uint8',
	              'uint16', 'uint32', 'uint64', 'int8', 'int16',
                      'int32', 'int64', 'cell', 'canonical empty']


PythonScalarMarshaller
----------------------

.. autoclass:: PythonScalarMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonScalarMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoinstanceattribute:: PythonScalarMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonScalarMarshaller.types
      :annotation: = [bool, int, float, complex]

   .. autoinstanceattribute:: PythonScalarMarshaller.python_type_strings
      :annotation: = ['bool', 'int', 'float', 'complex']

   .. autoinstanceattribute:: PythonScalarMarshaller.matlab_classes
      :annotation: = []


PythonStringMarshaller
----------------------

.. autoclass:: PythonStringMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonStringMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoinstanceattribute:: PythonStringMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonStringMarshaller.types
      :annotation: = [str, bytes, bytearray]

   .. autoinstanceattribute:: PythonStringMarshaller.python_type_strings
      :annotation: = ['str', 'bytes', 'bytearray']

   .. autoinstanceattribute:: PythonStringMarshaller.matlab_classes
      :annotation: = []


PythonNoneMarshaller
--------------------

.. autoclass:: PythonNoneMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonNoneMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoinstanceattribute:: PythonNoneMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonNoneMarshaller.types
      :annotation: = [builtins.NoneType]

   .. autoinstanceattribute:: PythonNoneMarshaller.python_type_strings
      :annotation: = ['builtins.NoneType']

   .. autoinstanceattribute:: PythonNoneMarshaller.matlab_classes
      :annotation: = []


PythonDictMarshaller
--------------------

.. autoclass:: PythonDictMarshaller
   :members: read, write, write_metadata
   :show-inheritance:

   .. autoinstanceattribute:: PythonDictMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Fields'}

   .. autoinstanceattribute:: PythonDictMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class'}

   .. autoinstanceattribute:: PythonDictMarshaller.types
      :annotation: = [dict]

   .. autoinstanceattribute:: PythonDictMarshaller.python_type_strings
      :annotation: = ['dict']

   .. autoinstanceattribute:: PythonDictMarshaller.matlab_classes
      :annotation: = []


PythonListMarshaller
--------------------

.. autoclass:: PythonListMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonListMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoinstanceattribute:: PythonListMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonListMarshaller.types
      :annotation: = [list]

   .. autoinstanceattribute:: PythonListMarshaller.python_type_strings
      :annotation: = ['list']

   .. autoinstanceattribute:: PythonListMarshaller.matlab_classes
      :annotation: = []


PythonTupleSetDequeMarshaller
-----------------------------

.. autoclass:: PythonTupleSetDequeMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonTupleSetDequeMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoinstanceattribute:: PythonTupleSetDequeMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonTupleSetDequeMarshaller.types
      :annotation: = [tuple, set, frozenset, collections.deque]

   .. autoinstanceattribute:: PythonTupleSetDequeMarshaller.python_type_strings
      :annotation: = ['tuple', 'set', 'frozenset', 'collections.deque']

   .. autoinstanceattribute:: PythonTupleSetDequeMarshaller.matlab_classes
      :annotation: = []

