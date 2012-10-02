import pytest

from .. import dehumanize


def test_None():
    # let caller pass in None and get out None, to make handling
    # default cases simpler
    got = dehumanize.parse(None)
    assert got is None


def test_int():
    # yaml can contain just "ram: 123456", and that comes through as
    # an int
    got = dehumanize.parse(42)
    assert got == 42


def test_float():
    # yaml can contain just "ram: 123.456", that's silly because there
    # are no fractional bytes, but let's not crap out.
    got = dehumanize.parse(42.51)
    # rounded
    assert got == 43


def test_simple():
    got = dehumanize.parse('42')
    assert got == 42


def test_kibibyte():
    got = dehumanize.parse('42KiB')
    assert got == 42*1024


def test_kibibyte_space():
    got = dehumanize.parse('42 KiB')
    assert got == 42*1024


def test_kibibyte_space_many():
    got = dehumanize.parse(' 42   KiB  ')
    assert got == 42*1024


def test_megs():
    got = dehumanize.parse('42M')
    assert got == 42*1024*1024


def test_kB():
    got = dehumanize.parse('42kB')
    assert got == 42000


def test_float_M():
    got = dehumanize.parse('1.2M')
    assert got == int(round(1.2*1024*1024))
    assert got == 1258291


def test_bad_no_number():
    with pytest.raises(dehumanize.NotANumberAndUnit) as exc:
        dehumanize.parse('foo')
    assert str(exc.value) == "Input does not look like a number with unit: 'foo'"
    assert exc.value.args == ('foo',)


def test_bad_unit():
    with pytest.raises(dehumanize.NotANumberAndUnit) as exc:
        dehumanize.parse('42 kilolol')
    assert str(exc.value) == "Input does not look like a number with unit: '42 kilolol'"
    assert exc.value.args == ('42 kilolol',)
