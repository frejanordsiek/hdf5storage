# Copyright (c) 2016-2021, Freja Nordsiek
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

import posixpath
import random

from hdf5storage.pathesc import escape_path, unescape_path, process_path

from make_randoms import random_str_ascii, random_str_some_unicode

random.seed()


# Get the characters that have to be escaped and make sure they are str
# instead of bytes.
chars_to_escape = ['\\', '/', '\x00']
substitutions = ['\\\\', '\\x2f', '\\x00']
period = '.'
period_substitute = '\\x2e'
if isinstance(chars_to_escape[0], bytes):
    chars_to_escape = [c.decode('utf-8') for c in chars_to_escape]
    substitutions = [c.decode('utf-8') for c in substitutions]
    period = period.decode('utf-8')
    period_substitute = period_substitute.decode('utf-8')


def make_str_for_esc(include_escapes=None,
                     include_leading_periods=False,
                     no_unicode=False,
                     pack_digits=True):
    sl = list(random_str_ascii(10))
    if not no_unicode:
        sl += list(random_str_some_unicode(10))
    if pack_digits:
        chars = b'0 1 2 3 4 5 6 7 8 9 a b c d e f A B C D E F'
        sl += chars.decode('ascii').split(b' '.decode('ascii')) * 10
    sl += [period] * 10
    if include_escapes is not None:
        for c in include_escapes:
            sl += [c] * 3
    random.shuffle(sl)
    s = b''.decode('ascii').join(sl).lstrip(period)
    if include_leading_periods:
        s = period * random.randint(1, 10) + s
    return s


def test_escaping():
    for i in range(20):
        s = make_str_for_esc(include_escapes=chars_to_escape,
                             include_leading_periods=True)
        s_e = s
        for j, c in enumerate(chars_to_escape):
            s_e = s_e.replace(c, substitutions[j])
        length = len(s_e)
        s_e = s_e.lstrip(period)
        s_e = period_substitute * (length - len(s_e)) + s_e
        assert s_e == escape_path(s)


def test_unescaping_x():
    fmts = [b'{0:02x}'.decode('ascii'), b'{0:02X}'.decode('ascii')]
    prefix = b'\\x'.decode('ascii')
    for i in range(20):
        s = make_str_for_esc(no_unicode=True,
                             pack_digits=True)
        index = random.randrange(1, len(s) - 1)
        c = s[index]
        n = ord(c)
        c_e = prefix + random.choice(fmts).format(n)
        s_e = s[:index] + c_e + s[(index + 1):]
        assert s == unescape_path(s_e)


def test_unescaping_u():
    fmts = [b'{0:04x}'.decode('ascii'), b'{0:04X}'.decode('ascii')]
    prefix = b'\\u'.decode('ascii')
    for i in range(20):
        s = make_str_for_esc(pack_digits=True)
        index = random.randrange(1, len(s) - 1)
        c = s[index]
        n = ord(c)
        c_e = prefix + random.choice(fmts).format(n)
        s_e = s[:index] + c_e + s[(index + 1):]
        assert s == unescape_path(s_e)


def test_unescaping_U():
    fmts = [b'{0:08x}'.decode('ascii'), b'{0:08X}'.decode('ascii')]
    prefix = b'\\U'.decode('ascii')
    for i in range(20):
        s = make_str_for_esc(pack_digits=True)
        index = random.randrange(1, len(s) - 1)
        c = s[index]
        n = ord(c)
        c_e = prefix + random.choice(fmts).format(n)
        s_e = s[:index] + c_e + s[(index + 1):]
        assert s == unescape_path(s_e)


def test_escape_reversibility_no_escapes():
    for i in range(20):
        s = make_str_for_esc()
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e
        assert s == s_e_u


def test_escape_reversibility_no_escapes_bytes():
    for i in range(20):
        s = make_str_for_esc()
        s = s.encode('utf-8')
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e.encode('utf-8')
        assert s == s_e_u.encode('utf-8')


def test_escape_reversibility_escapes():
    for i in range(20):
        s = make_str_for_esc(include_escapes=chars_to_escape)
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e_u


def test_escape_reversibility_escapes_bytes():
    for i in range(20):
        s = make_str_for_esc(include_escapes=chars_to_escape)
        s = s.encode('utf-8')
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e_u.encode('utf-8')


def test_escape_reversibility_leading_periods():
    for i in range(20):
        s = make_str_for_esc(include_leading_periods=True)
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e_u


def test_escape_reversibility_leading_periods_bytes():
    for i in range(20):
        s = make_str_for_esc(include_leading_periods=True)
        s = s.encode('utf-8')
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e_u.encode('utf-8')


def test_escape_reversibility_escapes_leading_periods():
    for i in range(20):
        s = make_str_for_esc(include_escapes=chars_to_escape,
                             include_leading_periods=True)
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e_u


def test_escape_reversibility_escapes_leading_periods_bytes():
    for i in range(20):
        s = make_str_for_esc(include_escapes=chars_to_escape,
                             include_leading_periods=True)
        s = s.encode('utf-8')
        s_e = escape_path(s)
        s_e_u = unescape_path(s_e)
        assert s == s_e_u.encode('utf-8')


def test_process_path_no_escapes():
    for i in range(10):
        pth = [make_str_for_esc() for j in range(10)]
        beginning = tuple(pth[:-1])
        gs = posixpath.join(*beginning)
        ts = pth[-1]
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname


def test_process_path_no_escapes_bytes():
    for i in range(10):
        pth = [make_str_for_esc().encode('utf-8') for j in range(10)]
        beginning = tuple(pth[:-1])
        gs = posixpath.join(*beginning).decode('utf-8')
        ts = pth[-1].decode('utf-8')
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname


def test_process_path_escapes():
    for i in range(10):
        pth = [make_str_for_esc(include_escapes=chars_to_escape)
               for j in range(10)]
        beginning = tuple([escape_path(s) for s in pth[:-1]])
        gs = posixpath.join(*beginning)
        ts = escape_path(pth[-1])
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname


def test_process_path_escapes_bytes():
    for i in range(10):
        pth = [make_str_for_esc(
               include_escapes=chars_to_escape).encode('utf-8')
               for j in range(10)]
        beginning = tuple([escape_path(s) for s in pth[:-1]])
        gs = posixpath.join(*beginning)
        ts = escape_path(pth[-1])
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname


def test_process_path_leading_periods():
    for i in range(10):
        pth = [make_str_for_esc(include_leading_periods=True)
               for j in range(10)]
        beginning = tuple([escape_path(s) for s in pth[:-1]])
        gs = posixpath.join(*beginning)
        ts = escape_path(pth[-1])
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname


def test_process_path_leading_periods_bytes():
    for i in range(10):
        pth = [make_str_for_esc(
               include_leading_periods=True).encode('utf-8')
               for j in range(10)]
        beginning = tuple([escape_path(s) for s in pth[:-1]])
        gs = posixpath.join(*beginning)
        ts = escape_path(pth[-1])
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname


def test_process_path_escapes_leading_periods():
    for i in range(10):
        pth = [make_str_for_esc(include_escapes=chars_to_escape,
                                include_leading_periods=True)
               for j in range(10)]
        beginning = tuple([escape_path(s) for s in pth[:-1]])
        gs = posixpath.join(*beginning)
        ts = escape_path(pth[-1])
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname


def test_process_path_escapes_leading_periods_bytes():
    for i in range(10):
        pth = [make_str_for_esc(
               include_escapes=chars_to_escape,
               include_leading_periods=True).encode('utf-8')
               for j in range(10)]
        beginning = tuple([escape_path(s) for s in pth[:-1]])
        gs = posixpath.join(*beginning)
        ts = escape_path(pth[-1])
        gname, tname = process_path(pth)
        assert gs == gname
        assert ts == tname
