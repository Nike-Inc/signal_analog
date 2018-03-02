"""Tests for the `signal_analog.flow` package."""

import pytest

from signal_analog.flow import Program, Data, Filter

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
    data = Data('cpu.utilization', filter=Filter('app', 'shoeadmin'))
    program = Program(data)
    assert program.statements[0] == data


def test_add_statements():
    data = Data('foo').publish(label='A', enable='False')
    program = Program()
    program.add_statements(data)
    assert program.statements[0] == data


def test_find_label_unpublished():
    data = Data('cpu.utilization', filter=Filter('app', 'shoeadmin'))
    program = Program(data)

    assert program.find_label('A') is None


def test_find_label_published():
    data = Data('cpu.utilization', filter=Filter('app', 'shoeadmin'))\
        .publish(label='A')
    program = Program(data)

    assert program.find_label('A') == data


def test_find_label_empty():
    assert Program().find_label('A') is None