"""Tests for the `signal_analog.flow` package."""

import pytest

from signal_analog.flow import Program, Data, Filter, Op, When, Assign, Ref, Top, KWArg
from signal_analog.combinators import Mul, GT, Div
from signal_analog.errors import \
    ProgramDoesNotPublishTimeseriesError

from hypothesis import given, settings
from .generators import ascii, flows


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

def test_top_function():
    data = Data('cpu.utilization', filter=Filter('app', 'test-app'))\
        .top(count=3,  percentage=22.3, by=["env", "datacenter"])\
        .publish(label='A')
    program = Program(data)
    assert data.call_stack[0].args  == [KWArg("count", 3), KWArg("percentage", 22.3), KWArg("by", ["env", "datacenter"])]

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


@given(assignee=ascii(), expr=flows())
def test_assign(assignee, expr):
    """Assign.__str__ should always return a string matching assignee = expr."""
    assert str(Assign(assignee, expr)) == \
        "{0} = {1}".format(str(assignee), str(expr))


def test_ref():
    strRef = "example_reference"
    ref = Ref(strRef)

    assert str(ref) == strRef


def test_valid_publish_statements_default():
    data = Data('requests.mean')

    with pytest.raises(ProgramDoesNotPublishTimeseriesError):
        Program(data).validate()


def test_valid_publish_statements_happy():
    data = Data('requests.mean').publish(label='foo')
    Program(data).validate()


def test_valid_publish_statements_multi():
    Program(
        Data('requests.mean'),
        Data('foo').publish(label='foo')
    ).validate()


def test_valid_publish_statements_assign_happy():
    Program(
        Assign('A', Data('foo').publish(label='lol'))
    ).validate()


def test_valid_publish_statements_assign_invalid():
    with pytest.raises(ProgramDoesNotPublishTimeseriesError):
        Program(
            Assign('A', Data('foo'))
        ).validate()


def test_valid_publish_statements_comb_invalid():
    with pytest.raises(ProgramDoesNotPublishTimeseriesError):
        Program(
            Op(Div(Data('foo'), Data('bar')))
        ).validate()


def test_valid_publish_statement_comb_valid():
    Program(
        Op(Div(Data('foo'), Data('bar'))).publish(label='foobar')
    ).validate()
