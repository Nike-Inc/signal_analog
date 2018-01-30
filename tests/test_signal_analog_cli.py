import betamax
import click
import requests
from betamax_serializers import pretty_json
from click.testing import CliRunner

from signal_analog.charts import TimeSeriesChart
from signal_analog.cli import CliBuilder
from signal_analog.dashboards import Dashboard
from signal_analog.flow import Data

# Global config. This will store all recorded requests in the 'mocks' dir
with betamax.Betamax.configure() as config:
    betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.cassette_library_dir = 'tests/mocks'

# Don't get in the habit of doing this, but it simplifies testing
global_session = requests.Session()
global_recorder = betamax.Betamax(global_session)


def test_cli_create_success():
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with global_recorder.use_cassette('cli_create_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create'])
        assert result.exit_code == 0


def test_cli_create_failure():
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with global_recorder.use_cassette('cli_create_failure',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create'])
        assert result.exception


def test_cli_create_force_success():
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with global_recorder.use_cassette('cli_create_force_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create', '-f'])
        assert result.exit_code == 0


def test_cli_create_interactive_success():
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with global_recorder.use_cassette('cli_create_interactive_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create', '-i'], input='y')
        assert result.exit_code == 0


def test_cli_create_interactive_failure():
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with global_recorder.use_cassette('cli_create_interactive_failure',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create', '-i'], input='n')
        click.echo(result.exception)
        assert result.exception


def test_cli_update_success():
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with global_recorder.use_cassette('cli_update_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', '***REMOVED***', 'update',
                                          '--description', 'updated_dashboard_description'])
        assert result.exit_code == 0


def test_cli_update_failure():
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with global_recorder.use_cassette('cli_update_failure',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'update',
                                          '--description', 'updated_dashboard_description'])
        assert result.exception
