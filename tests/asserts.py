import numpy as np
import numpy.testing as npt

def assert_equal(a, b):
    # Compares a and b for equality. If they are not numpy types (aren't
    # or don't inherit from np.generic or np.ndarray), then it is a
    # matter of just comparing them. Otherwise, their dtypes and shapes
    # have to be compared. Then, if they are not an object array,
    # numpy.testing.assert_equal will compare them elementwise. For
    # object arrays, each element must be iterated over to be compared.
    assert type(a) == type(b)
    if not isinstance(b, (np.generic, np.ndarray)):
        assert a == b
    else:
        assert a.dtype == b.dtype
        assert a.shape == b.shape
        if b.dtype.name != 'object':
            npt.assert_equal(a, b)
        else:
            for index, x in np.ndenumerate(a):
                assert_equal(a[index], b[index])


def assert_equal_python_collection(a, b, tp):
    # Compares two python collections that are supposed to be the
    # specified type tp. First, they have to be that type. If the type
    # is a set type, then a simple comparison is all that is
    # needed. Otherwise, an elementwise comparison needs to be done.
    assert type(a) == tp
    assert type(b) == tp
    assert len(a) == len(b)
    if type(b) in (set, frozenset):
        assert a == b
    else:
        for index in range(0, len(a)):
            assert_equal(a[index], b[index])
