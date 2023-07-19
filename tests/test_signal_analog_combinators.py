"""Tests for `signal_analog.combinators` package."""

from hypothesis import given, settings
from hypothesis.strategies import one_of, just, none, lists
import pytest

import signal_analog.combinators as comb
from .generators import ascii, flows


@given(one_of(none(), just("")))
def test_binary_combinator_empty_operator(value):
    """Binary combinator should not accept empty operators"""
    with pytest.raises(ValueError):
        comb.NAryCombinator(value)


@given(op=ascii(), values=lists(elements=ascii()))
def test_binary_combinator_str(op, values):
    """Binary combinator should always intersperse its op in the elements."""
    assert str(comb.NAryCombinator(op, *values)) == \
        " {0} ".format(op).join(map(str, values))


@given(flows(), flows())
def test_binary_combinator_and(f, ff):
    """And combinator should always intersperse 'and' in the elements."""
    assert str(comb.And(f, ff)) == "{0} and {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_or(f, ff):
    """Or combinator should always intersperse 'or' in the elements."""
    assert str(comb.Or(f, ff)) == "{0} or {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_mul(f, ff):
    """Mul combinator should always intersperse '*' in the elements."""
    assert str(comb.Mul(f, ff)) == "{0} * {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_div(f, ff):
    """Div combinator should always intersperse '/' in the elements."""
    assert str(comb.Div(f, ff)) == "{0} / {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_add(f, ff):
    """Add combinator should always intersperse '+' in the elements."""
    assert str(comb.Add(f, ff)) == "{0} + {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_sub(f, ff):
    """Sub combinator should always intersperse '-' in the elements."""
    assert str(comb.Sub(f, ff)) == "{0} - {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_lt(f, ff):
    """LT combinator should always intersperse '<' in the elements."""
    assert str(comb.LT(f, ff)) == "{0} < {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_gt(f, ff):
    """GT combinator should always intersperse '>' in the elements."""
    assert str(comb.GT(f, ff)) == "{0} > {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_lte(f, ff):
    """LTE combinator should always intersperse '<=' in the elements."""
    assert str(comb.LTE(f, ff)) == "{0} <= {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_gte(f, ff):
    """GTE combinator should always intersperse '>=' in the elements."""
    assert str(comb.GTE(f, ff)) == "{0} >= {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_eq(f, ff):
    """EQ combinator should always intersperse '==' in the elements."""
    assert str(comb.EQ(f, ff)) == "{0} == {1}".format(str(f), str(ff))


@given(flows(), flows())
def test_binary_combinator_ne(f, ff):
    """NE combinator should always intersperse '!=' in the elements."""
    assert str(comb.NE(f, ff)) == "{0} != {1}".format(str(f), str(ff))


@given(flows())
def test_combinator_not(expr):
    """Not combinator should always prefix 'not' to its expression."""
    assert str(comb.Not(expr)) == "not {0}".format(str(expr))


@given(flows(), flows())
def test_mixed_combinators(f, ff):
    """Mixed combinators should preserve order of operations."""
    assert str(comb.And(comb.Not(f), comb.Or(f, ff))) == \
        "not {0} and ({0} or {1})".format(str(f), str(ff))
