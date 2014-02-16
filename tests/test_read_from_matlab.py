# Copyright (c) 2014, Freja Nordsiek
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

import os
import os.path
import subprocess

import scipy.io

import hdf5storage

from asserts import *

mat_files = ['types_v7p3.mat', 'types_v7.mat']
for i in range(0, len(mat_files)):
    mat_files[i] = os.path.join(os.path.dirname(__file__), mat_files[i])

script_name = os.path.join(os.path.dirname(__file__),
                           'make_mat_with_all_types.m')

data_v7 = dict()
data_v7p3 = dict()


def setup_module():
    teardown_module()
    matlab_command = "run('" + script_name + "')"
    subprocess.check_output(['matlab', '-nosplash', '-nodesktop',
                            '-nojvm', '-r', matlab_command])
    scipy.io.loadmat(file_name=mat_files[1], mdict=data_v7)
    hdf5storage.loadmat(file_name=mat_files[0], mdict=data_v7p3)


def teardown_module():
    for name in mat_files:
        if os.path.exists(name):
            os.remove(name)


def test_read():
    for k in (set(data_v7.keys()) - set(['__version__', '__header__', \
            '__globals__'])):
        yield check_variable, k


def check_variable(name):
    assert_equal_from_matlab(data_v7p3[name], data_v7[name])
