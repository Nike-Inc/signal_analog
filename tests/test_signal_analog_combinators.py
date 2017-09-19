"""Tests for `signal_analog.combinators` package."""

from hypothesis import given
from hypothesis.strategies import one_of, just, none, lists
import pytest

import signal_analog.combinators as comb
from .generators import *


@given(one_of(none(), just("")))
def test_binary_combinator_empty_operator(value):
    """Binary combinator should not allow empty operators"""
    with pytest.raises(ValueError):
        comb.BinaryCombinator(value)


@given(op=ascii(), values=lists(elements=ascii()))
def test_binary_combinator_str(op, values):
    """Binary combinator should always intersperse its op in the elements."""
    assert str(comb.BinaryCombinator(op, *values)) == \
        " {0} ".format(op).join(map(str, values))


@given(flows(), flows())
def test_binary_combinator_and(f, ff):
    """And combinator should always intersperse 'and' in the elements."""
    assert str(comb.And(f, ff)) == "{0} and {1}".format(str(f), str(ff))

@given(flows(), flows())
def test_binary_combinator_or(f, ff):
    """Or combinator should always intersperse 'or' in the elements."""
    assert str(comb.Or(f, ff)) == "{0} or {1}".format(str(f), str(ff))


@given(flows())
def test_combinator_not(expr):
    """Not combinator should always prefix 'not' to its expression."""
    assert str(comb.Not(expr)) == "not {0}".format(str(expr))
