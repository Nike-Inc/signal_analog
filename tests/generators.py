"""Generator definitions for signal_analog.flow objects."""

from hypothesis.strategies import \
     text, characters, composite, recursive, sampled_from, floats
from hypothesis import settings

import signal_analog.flow as flow


def ascii():
    return text(
        characters(min_codepoint=1, max_codepoint=128,
                   blacklist_categories=['Cc', 'Cs']),
        min_size=1, max_size=5)


def flows():
    return recursive(
        filters() | datas() | consts() | graphites() | newrelics(),
        lambda children: whens() | detects(),
        max_leaves=5)


@composite
def filters(draw):
    parameter_name = draw(ascii())
    query = draw(ascii())
    return flow.Filter(parameter_name, query)


@composite
def datas(draw):
    """TODO expand to include all optional parameters."""
    metric = draw(ascii())
    filter = draw(filters())
    return flow.Data(metric, filter=filter)


@composite
def consts(draw):
    """TODO timeseries needs to be fixed"""
    value = draw(ascii())
    key = draw(ascii())
    timeseries = draw(ascii())
    return flow.Const(value, key, timeseries)


@composite
def unions(draw):
    """TODO"""
    pass


@composite
def whens(draw):
    f = draw(flows())
    lasting = ascii()
    return flow.When(f, lasting=lasting)


@composite
def graphites(draw):
    """TODO support all optional args"""
    metric = draw(ascii())
    return flow.Graphite(metric)


@composite
def newrelics(draw):
    """TODO support all optional args"""
    metric = draw(ascii())
    filter = draw(filters())
    return flow.Newrelic(metric, filter=filter)


@composite
def detects(draw):
    on = draw(flows())
    off = draw(ascii())
    mode = draw(sampled_from(["paired", "split"]))
    return flow.Detect(on, off=off, mode=mode)


@composite
def lastings(draw):
    """TODO solidify the lasting definition"""
    lasting = draw(ascii())
    at_least = draw(floats())
    return flow.Lasting(lasting=lasting, at_least=at_least)
