"""Tests for the `signal_analog.flow` package."""

import pytest

from signal_analog.flow import Program, Data, Filter, Op, When, Ref
from signal_analog.combinators import Mul, GT

@pytest.mark.parametrize("value", [None, "", {'foo':'bar'}])
def test_program_init_add_statement_invalid(value):
    """Ensure that neither Program's constructor nor add_statement allows
       non-statement values.
    """
    with pytest.raises(ValueError):
        Program(value)

    with pytest.raises(ValueError):
        Program().add_statements(value)


def test_program_init_valid_empty():
    assert Program().statements == []


def test_program_init_valid_statements():
    data = Data('cpu.utilization', filter=Filter('app', 'test-app'))
    program = Program(data)
    assert program.statements[0] == data


def test_add_statements():
    data = Data('foo').publish(label='A', enable='False')
    program = Program()
    program.add_statements(data)
    assert program.statements[0] == data


def test_find_label_unpublished():
    data = Data('cpu.utilization', filter=Filter('app', 'test-app'))
    program = Program(data)

    assert program.find_label('A') is None


def test_find_label_published():
    data = Data('cpu.utilization', filter=Filter('app', 'test-app'))\
        .publish(label='A')
    program = Program(data)

    assert program.find_label('A') == data


def test_find_label_empty():
    assert Program().find_label('A') is None

def test_op_combines_mul():
    data1 = Data('request.mean')\
        .publish(label='A')
    data2 = Data('request.count')\
        .publish(label='B')
    muldata = Op(Mul(data1,data2))
    program = Program(muldata)
    assert program.statements[0] == muldata


def test_when():
    data1 = Data('request.mean')\
        .publish(label='A')
    when = When(GT(data1, 50), '5m', 0.5)
    program = Program(when)
    assert program.statements[0] == when


def test_ref():
    strRef = "example_reference"
    ref = Ref(strRef)

    assert str(ref) == strRef
