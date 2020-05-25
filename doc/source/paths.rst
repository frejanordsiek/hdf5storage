.. currentmodule:: hdf5storage

.. _Paths:

=====
Paths
=====

Paths in HDF5
=============

HDF5 files are structured much like a Unix filesystem, so everything can
be referenced with a POSIX style path, which look like
``'/pyth/hf'``. Unlike a Windows path, forward slashes (``'/'``) are
used as directory separators instead of backward slashes (``'\\'``) and
the base of the file system is just ``'/'`` instead of something like
``'C:\\'``. In the language of HDF5, what we call directories and files
in filesystems are called groups and datasets.

Limitations of HDF5 Paths
=========================

The HDF5 format and library do not support having Dataset or Group names
containing nulls (``'\x00'``), containing forward slashes (``'/'``), or
starting out with one or more periods (``'.'``).

Solution - Escaping
===================

.. versionadded:: 0.2
   
   Ability to escape characters not allowed in Group or Dataset names.

.. warning::

   Before version 0.2, no escaping is supported and errors are thrown
   when a workaround cannot be found.

In order to work around these limitations in HDF5 Dataset and Group
names, the ability to escape these characters is provided. They are
escaped as hexidecimal specifications or as doubling, which is fairly
standard. The conversions are

==============  ==========  ===========
Name            Character   Escaped
==============  ==========  ===========
null            ``'\x00'``  ``'\\x00'``
forward slash   ``'/'``     ``'\\x2f'``
backward slash  ``'\\'``    ``'\\\\'``
==============  ==========  ===========

The backward slash has to be escaped or else it will be impossible to
accurately unescape.

When unescaping, all the hex and unicode escapes allowed in python
strings as well as how backward slashes are entered are used. They are

=================  ================  ==========
Escape             Kind              Conversion
=================  ================  ==========
``'\\\\'``         double backslash  ``'\\'``
``'\\xYY'``        hex               ``chr(N)``
``'\\uYYYY'``      unicode           ``chr(N)``
``'\\UYYYYYYYY'``  unicode           ``chr(N)``
=================  ================  ==========

Where the Y are hexidecimal digits and N is the value of the hexidecimal
number (the unicode character codepoint).

Supported Paths
===============

Paths can be given in a number of ways.

No Escaping
-----------

The path is given as a ``str``, ``bytes``, or :py:class:`pathlib.PurePath`.
It is the responsibility of the caller to make sure all escaping has been done.
Forward slashes are interpreted as path separators.

Escaping
--------

The path is given as an iterable (e.g. ``list``, ``tuple``, etc.) of
separated parts of the path (split at the separators) which must each be
``str``, ``bytes``, and :py:class:`pathlib.PurePath`. These parts will each
be escaped before being joined.

Escaping/Unescaping Functions
=============================

.. versionadded:: 0.2
   
   The functions described here.

:py:func:`pathesc.escape_path` is the function to escape an individual
part of a path with.

:py:func:`pathesc.unescape_path` is the function to unescape a path.

:py:func:`pathesc.process_path` is a function that will take a path of
any form, escape it if it is meant to be escaped, and get the Group that
the target of the path is in as well as the name of the target inside
that Group the path is pointing at.
