"""Tests for the `signal_analog.flow` package."""

import pytest

from signal_analog.flow import Program, Data, Filter, Op, When, Assign, Ref, \
                               Top, KWArg, StrArg, Count, Mean, \
                               Mean_plus_stddev, Median, Min, Max, Size, \
                               Stddev, Sum, Variance, \
                               AggregationTransformationMixin, Plot
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

def test_count_percentage_by_methods():
    # TODO consider making this test use dynamic fn calls to test all stream
    #      methods with the same signature.
    data = Data('cpu.utilization', filter=Filter('app', 'test-app'))\
        .top(count=3,  percentage=22.3, by=["env", "datacenter"])\
        .bottom(count=4, percentage=22.4, by=["env", "datacenter"])\
        .publish(label='A')

    assert data.call_stack[0].args  == [KWArg("count", 3), KWArg("percentage", 22.3), KWArg("by", ["env", "datacenter"])]
    assert data.call_stack[1].args  == [KWArg("count", 4), KWArg("percentage", 22.4), KWArg("by", ["env", "datacenter"])]

def test_fill():
    data = Data("cpu.utilization", filter=Filter('app', 'test-app'))\
        .fill(value=42, duration="1m")\
        .publish(label = 'a')
    
    assert data.call_stack[0].name =='fill'
    assert data.call_stack[0].args == [KWArg("value", 42), KWArg("duration", '1m')]

def test_integrate():
    data = Data("cpu.utilization", filter=Filter('app', 'test-app'))\
        .integrate()\
        .publish(label = 'a')

    assert data.call_stack[0].name == 'integrate'
    assert data.call_stack[0].args == []

def test_kpss():
    data = Data("cpu.utilization", filter=Filter('app', 'test-app'))\
        .kpss(over='1h')\
        .publish(label = 'a')

    assert data.call_stack[0].name == 'kpss'
    # mode should default to level
    assert data.call_stack[0].args == [KWArg("over", '1h'), KWArg("mode", 'level')]

    data = Data("cpu.utilization", filter=Filter('app', 'test-app'))\
        .kpss(over='2m', mode='trend')\
        .publish(label = 'a')

    # should allow trend
    assert data.call_stack[0].args == [KWArg("over", '2m'), KWArg("mode", 'trend')]

    try:
        Data("cpu.utilization", filter=Filter('app', 'test-app'))\
            .kpss(over='2m', mode='tr3nd')
        assert False
    except ValueError as ve:
        assert str(ve) == 'kpss mode must be level|trend'

def test_rateofchange():
    data = Data("cpu.utilization", filter=Filter('app', 'test-app'))\
        .rateofchange()\
        .publish(label = 'a')

    assert data.call_stack[0].name == 'rateofchange'
    assert data.call_stack[0].args == []


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

def test_valid_publish_statements_plot_happy():
    Program(
        Plot('A', 'foo', fx=[Max()], label="lol")
    ).validate()
    Program(
        Plot('A', 'foo', fx=None, label="lol")
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


def test_over_by_methods_single_invocation():
    """Ensure that by/over methods don't allow you to supply both in a single call."""
    with pytest.raises(ValueError):
        Data('foo').count(by='dimension', over='1m')

    data_by = Data('bar').count(by='foo')
    data_over = Data('baz').count(over='1m')

    assert data_by.call_stack[0].args[0].arg == 'foo'
    assert data_over.call_stack[0].args[1].arg == '1m'


def test_dimensions_method_happy():
    data = Data('bar').dimensions(aliases={'foo': 'baz'}).publish(label='foo')
    assert data.call_stack[0].args[0] == KWArg("aliases", {'foo': 'baz'})

    data = Data('bar').dimensions(renames={'foo': 'baz'}).publish(label='foo')
    assert data.call_stack[0].args[1] == KWArg("renames", {'foo': 'baz'})


def test_dimensions_invalid():
    with pytest.raises(ValueError):
        data = Data('bar').dimensions(aliases={}, renames={})


def test_ewma_happy():
    data = Data('foo').ewma(1)
    assert data.call_stack[0].args[0].arg == 1

    data = Data('foo').ewma(over='1m')
    assert data.call_stack[0].args[0] == KWArg("over", '1m')


def test_ewma_invalid():
    with pytest.raises(ValueError):
        Data('foo').ewma(1, '1m')


def test_percentile_happy():
    data = Data('foo').percentile(99)
    assert data.call_stack[0].args[0].arg == 99


def test_above_happy_zero():
    data = Data('foo').above(0)
    assert data.call_stack[0].args[0].arg == 0


@pytest.mark.parametrize("clazz", [Count, Mean, Mean_plus_stddev, Median, Min,
                                   Max, Size, Stddev, Sum, Variance])
def test_transform_aggregation_happy(clazz):

    assert clazz(by='foo').args[0].arg == 'foo'
    assert clazz(over='bar').args[1].arg == 'bar'


@pytest.mark.parametrize("clazz", [Count, Mean, Mean_plus_stddev, Median, Min,
                                   Max, Size, Stddev, Sum, Variance])
def test_transform_aggregation_invalid(clazz):
    with pytest.raises(ValueError):
        clazz(by='foo', over='bar')


def test_transform_aggregation_not_stream_method():

    class Foo(object):
        pass

    class Bar(Foo, AggregationTransformationMixin):
        pass

    with pytest.raises(ValueError):
        Bar().check_pre_conditions()
