.. currentmodule:: hdf5storage

.. _Compression:

===========
Compression
===========

The HDF5 libraries and the :py:mod:`h5py` module support transparent
compression of data in HDF5 files.

The use of compression can sometimes drastically reduce file size, often
makes it faster to read the data from the file, and sometimes makes it
faster to write the data. Though, not all data compresses very well and
can occassionally end up larger after compression than it was
uncompressed. Compression does cost CPU time both when compressing the
data and when decompressing it. The reason this can sometimes lead to
faster read and write times is because disks are very slow and the space
savings can save enough disk access time to make up for the CPU time.

All versions of this package can read compressed data, but not all
versions can write compressed data.

.. versionadded:: 0.1.9
   
   HDF5 write compression features added along with several options to
   control it in :py:class:`Options`.


.. versionadded:: 0.1.7

   :py:class:`Options` will take the compression options but ignores
   them.


.. warning::

   Passing the compression options for versions earlier than ``0.1.7``
   will result in an error.


Enabling Compression
====================

Compression, which is enabled by default, is controlled by setting
:py:attr:`Options.compress` to ``True`` or passing ``compress=X`` to
:py:func:`write` and :py:func:`savemat` where ``X`` is ``True`` or
``False``.


.. note::
   
   Not all python objects written to the HDF5 file will be compressed,
   or even support compression. For one, :py:mod:`numpy` scalars or any
   type that is stored as one do not support compression due to
   limitations of the HDF5 library, though compressing them would be a
   waste (hence the lack of support).


Setting The Minimum Data Size for Compression
=============================================

Compressing small pieces of data often wastes space (compressed size is
larger than uncompressed size) and CPU time. Due to this, python objects
have to be larger than a particular size before this package will
compress them. The threshold, in bytes, is controlled by setting
:py:attr:`Options.compress_size_threshold` or passing
``compress_size_threshold=X`` to :py:func:`write` and
:py:func:`savemat` where ``X`` is a non-negative integer. The default
value is 16 KB.


Controlling The Compression Algorithm And Level
===============================================

Many compression algorithms can be used with HDF5 files, though only
three are common. The Deflate algorithm (sometimes known as the GZIP
algorithm), LZF algorithm, and SZIP algorithms are the algorithms that
the HDF5 library is explicitly setup to support. The library has a
mechanism for adding additional algorithms. Popular ones include the
BZIP2 and BLOSC algorithms.

The compression algorithm used is controlled by setting
:py:attr:`Options.compression_algorithm` or passing
``compression_algorithm=X`` to :py:func:`write` and :py:func:`savemat`.
``X`` is the ``str`` name of the algorithm. The default is ``'gzip'``
corresponding to the Deflate/GZIP algorithm.

.. note::
   
   As of version ``0.2``, only the Deflate (``X = 'gzip'``), LZF
   (``X = 'lzf'``), and SZIP (``X = 'szip'``) algorithms are supported.


.. note::

   If doing MATLAB compatibility (:py:attr:`Options.matlab_compatible`
   is ``True``), only the Deflate algorithm is supported.


The algorithms, in more detail

GZIP / Deflate (``'gzip'``)
   The common Deflate algorithm seen in the Unix and Linux ``gzip``
   utility and the most common compression algorithm used in ZIP files.
   It is the most compatible algorithm. It achieves good compression and
   is reasonably fast. It has no patent or license restrictions.

LZF (``'lzf'``)
   A very fast algorithm but with inferior compression to GZIP/Deflate.
   It is less commonly used than GZIP/Deflate, but similarly has no
   patent or license restrictions.

SZIP (``'szip'``)
   This compression algorithm isn't always available and has patent
   and license restrictions. See
   `SZIP License <https://www.hdfgroup.org/doc_resource/SZIP/Commercial_szip.html>`_.


If GZIP/Deflate compression is being used, the compression level can be
adjusted by setting :py:attr:`Options.gzip_compression_level` or passing
``gzip_compression_level=X`` to :py:func:`write` and :py:func:`savemat`
where ``X`` is an integer between ``0`` and ``9`` inclusive. ``0`` is
the lowest compression, but is the fastest. ``9`` gives the best
compression, but is the slowest. The default is ``7``.

For all compression algorithms, there is an additional filter which can
help achieve better compression at relatively low cost in CPU time. It
is the shuffle filter. It is controlled by setting
:py:attr:`Options.shuffle_filter` or passing ``shuffle_filter=X`` to
:py:func:`write` and :py:func:`savemat` where ``X`` is ``True`` or
``False``. The default is ``True``.


Using Checksums
===============

Fletcher32 checksums can be calculated and stored for most types of
stored data in an HDF5 file. These are then checked when the data is
read to catch file corruption, which will cause an error when reading
the data informing the user that there is data corruption. The filter
can be enabled or disabled separately for data that is compressed and
data that is not compressed (e.g. compression is disabled, the python
object can't be compressed, or the python object's data size is smaller
than the compression threshold).

For compressed data, it is controlled by setting
:py:attr:`Options.compressed_fletcher32_filter` or passing
``compressed_fletcher32_filter=X`` to :py:func:`write` and
:py:func:`savemat` where ``X`` is ``True`` or ``False``. The default is
``True``.

For uncompressed data, it is controlled by setting
:py:attr:`Options.uncompressed_fletcher32_filter` or passing
``uncompressed_fletcher32_filter=X`` to :py:func:`write` and
:py:func:`savemat` where ``X`` is ``True`` or ``False``. The default is
``False``.


.. note::
   
   Fletcher32 checksums are not computed for anything that is stored
   as a :py:mod:`numpy` scalar.


Chunking
========

When no filters are used (compression and Fletcher32), this package
stores data in HDF5 files in a contiguous manner. The use of any filter
requires that the data use chunked storage. Chunk sizes are determined
automatically using the autochunk feature of :py:mod:`h5py`. The HDF5
libraries make reading contiguous and chunked data transparent, though
access speeds can differ and the chunk size affects the compression
ratio.


Further Reading
===============

.. seealso::

   `HDF5 Datasets Filter pipeline <http://docs.h5py.org/en/latest/high/dataset.html#filter-pipeline>`_
      Description of the Dataset filter pipeline in the :py:mod:`h5py`
   
   `Using Compression in HDF5 <http://www.hdfgroup.org/HDF5/faq/compression.html>`_
      FAQ on compression from the HDF Group.
   
   `HDF5 Tutorial: Learning The Basics: Dataset Storage Layout <https://www.hdfgroup.org/HDF5/Tutor/layout.html>`_
      Information on Dataset storage format from the HDF Group
   
   `SZIP License <https://www.hdfgroup.org/doc_resource/SZIP/Commercial_szip.html>`_
      The license for using the SZIP compression algorithm.

   `SZIP COMPRESSION IN HDF PRODUCTS <https://www.hdfgroup.org/doc_resource/SZIP>`_
      Information on using SZIP compression from the HDF Group.

   `3rd Party Compression Algorithms for HDF5 <https://www.hdfgroup.org/services/contributions.html>`_
      List of common additional compression algorithms.
   
