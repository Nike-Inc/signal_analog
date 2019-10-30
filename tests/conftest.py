"""Configuration for the pytest suite."""

import betamax
from betamax_serializers import pretty_json
import pytest
import requests
import os

from signal_analog.flow import Data, Program, Detect, Data
from signal_analog.combinators import GT
from signal_analog.charts import TimeSeriesChart, PlotType
from signal_analog.dashboards import Dashboard
from signal_analog.detectors import Detector, Rule, Severity, EmailNotification

signalfx_api_token = os.environ.get("SFX_API_TOKEN", "test-token")


with betamax.Betamax.configure() as config:
    betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.cassette_library_dir = "tests/mocks"
    config.define_cassette_placeholder("<SFX_TOKEN>", signalfx_api_token)


global_session = requests.Session()


@pytest.fixture(scope="session")
def api_token():
    return signalfx_api_token


@pytest.fixture(scope="session")
def session():
    return global_session


@pytest.fixture(scope="session")
def sfx_recorder(session):
    recorder = betamax.Betamax(session)
    return recorder


@pytest.fixture()
def chart(session):
    def fun(name):
        program = Data("cpu.utilization").publish()
        return TimeSeriesChart(session=session).with_name(name).with_program(program)

    return fun


@pytest.fixture()
def dashboard(session, chart):
    def fun(dash_name, chart_name):
        return (
            Dashboard(session=session)
            .with_name(dash_name)
            .with_charts(chart(chart_name))
        )

    return fun


@pytest.fixture()
def detector(session, chart):
    def fun(name, threshold):
        program = Program(
            Detect(GT(Data("cpu.utilization"), threshold)).publish(label=name)
        )

        rule = (
            Rule()
            .for_label(name)
            .with_severity(Severity.Info)
            .with_notifications(
                EmailNotification("francisco.friar@polite.thoughtleader.org")
            )
        )

        return (
            Detector(session=session)
            .with_name(name)
            .with_program(program)
            .with_rules(rule)
        )

    return fun
