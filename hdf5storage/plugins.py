# Copyright (c) 2017-2020, Freja Nordsiek
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

""" Module for finding plugins and indicating supported API versions

"""

# From setuptools, despite name.
import pkg_resources


def supported_marshaller_api_versions():
    """ Get the Marshaller API versions that are supported.

    Gets the different Marshaller API versions that this version of
    ``hdf5storage`` supports.

    .. versionadded:: 0.2

    Returns
    -------
    versions : tuple
        The different versions of marshallers that are supported. Each
        element is a version that is supported. The versions are
        specified in standard major, minor, etc. format as ``str``
        (e.g. ``'1.0'``). They are in descending order (highest version
        first, lowest version last).

    """
    return ('1.0', )


def find_thirdparty_marshaller_plugins():
    """ Find, but don't load, all third party marshaller plugins.

    Third party marshaller plugins declare the entry point
    ``'hdf5storage.marshallers.plugins'`` with the name being the
    Marshaller API version and the target being a callable that returns
    a ``tuple`` or ``list`` of all the marshallers provided by that
    plugin when given the hdf5storage version (``str``) as its only
    argument.

    .. versionadded:: 0.2

    Returns
    -------
    plugins : dict
        The marshaller obtaining entry points from third party
        plugins. The keys are the Marshaller API versions (``str``) and
        the values are ``dict`` of the entry points, with the module
        names as the keys (``str``) and the values being the entry
        points (``pkg_resources.EntryPoint``).

    See Also
    --------
    supported_marshaller_api_versions

    """
    all_plugins = tuple(pkg_resources.iter_entry_points(
        'hdf5storage.marshallers.plugins'))
    return {ver: {p.module_name: p
                  for p in all_plugins if p.name == ver}
            for ver in supported_marshaller_api_versions()}
