import pytest

import hydration as h


class Tomer(h.Struct):
    b = h.UInt8(5)
    c = h.Double(3)


class Lior(h.Struct):
    a = h.Array(5, fill=True)


def test_message():
    first = Tomer()
    last = Tomer()
    x = first / Lior() / last
    assert x[0] == x[Tomer] == x[(Tomer, 0)]
    assert x[-1] == x[(Tomer, 1)]
    assert x.size == len(bytes(x))
    assert x[-1] is last
    assert Tomer in x
    assert Lior in x

    class LiTor(h.Struct):
        pass

    assert LiTor not in x

    assert first in x
    assert last in x
    assert Tomer() not in x
    assert LiTor() not in x

    with pytest.raises(TypeError):
        assert 3 not in x


def test_bytes_suffix():
    x = Tomer() / Lior() / b'test'
    assert bytes(x) == b''.join((bytes(Tomer()), bytes(Lior()), b'test'))


def test_suffix_with_length():
    class Header(h.Struct):
        length = h.InclusiveLengthField(h.UInt16)

    Header() / b'lomeshane'


def test_associativity():
    assert (Tomer() / Lior() / b'test') == (Tomer() / (Lior() / b'test')) == ((Tomer() / Lior()) / b'test')


def test_length_fields():
    class A(h.Struct):
        a = h.UInt16
        length_field = h.ExclusiveLengthField(h.UInt16)

    class B(h.Struct):
        a = h.UInt16
        length_field = h.InclusiveLengthField(h.UInt16)

    class C(h.Struct):
        x = h.Array(5)
        y = h.UInt8

    class D(h.Struct):
        v = h.Vector(length='y')

    msg = A() / B()

    assert msg[A].length_field == msg[B].length_field == len(B())

    msg /= C()

    assert msg[A].length_field == msg[B].length_field == len(B()) + len(C())

    the_d = D(v=[1, 2, 3])
    msg /= the_d

    assert msg[A].length_field == msg[B].length_field == len(B()) + len(C()) + len(the_d)


def test_opcode_field():

    class C1(h.Struct):
        x = h.UInt32

    b_opcodes = {
        C1: 3
    }

    class B1(h.Struct):
        data = h.UInt8

    class B2(h.Struct):
        opcode = h.OpcodeField(h.UInt8, b_opcodes)

    a_opcodes = {
        B1: 1,
        B2: 2
    }

    class A(h.Struct):
        opcode = h.OpcodeField(h.UInt8, a_opcodes)

    assert (A() / B1())[A].opcode == 1
    assert (A() / B2())[A].opcode == 2

    assert (A() / B2() / C1())[B2].opcode == 3

    class B3(h.Struct):
        pass

    with pytest.raises(ValueError):
        A() / B3()


def test_single():
    class T(h.Struct):
        x = h.InclusiveLengthField(h.UInt8)
        y = h.Array(10, fill=True)

    t = h.Message(T())
    assert t[T].x == 11
