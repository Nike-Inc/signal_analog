"""Configuration for the pytest suite."""

import betamax
from betamax_serializers import pretty_json
import pytest
import requests

from signal_analog.flow import Data
from signal_analog.charts import TimeSeriesChart, PlotType
from signal_analog.dashboards import Dashboard


with betamax.Betamax.configure() as config:
    betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.cassette_library_dir = 'tests/mocks'


global_session = requests.Session()


@pytest.fixture(scope='session')
def session():
    return global_session


@pytest.fixture(scope='session')
def sfx_recorder(session):
    recorder = betamax.Betamax(session)
    return recorder


@pytest.fixture()
def chart(session):
    def fun(name):
        program = Data('cpu.utilization').publish()
        return TimeSeriesChart(session=session)\
            .with_name(name)\
            .with_program(program)
    return fun


@pytest.fixture()
def dashboard(session, chart):
    def fun(dash_name, chart_name):
        return Dashboard(session=session)\
            .with_name(dash_name)\
            .with_charts(chart(chart_name))
    return fun
