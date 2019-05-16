import click
from click.testing import CliRunner

from signal_analog.charts import TimeSeriesChart
from signal_analog.cli import CliBuilder
from signal_analog.dashboards import Dashboard
from signal_analog.flow import Data


def test_cli_create_success(sfx_recorder, session):
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with sfx_recorder.use_cassette('cli_create_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create'])
        assert result.exit_code == 0


def test_cli_create_failure(sfx_recorder, session):
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with sfx_recorder.use_cassette('cli_create_failure',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create'])
        assert result.exception


def test_cli_create_force_success(sfx_recorder, session):
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with sfx_recorder.use_cassette('cli_create_force_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create', '-f'])
        assert result.exit_code == 0


def test_cli_create_interactive_success(sfx_recorder, session):
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with sfx_recorder.use_cassette('cli_create_interactive_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create', '-i'], input='y')
        assert result.exit_code == 0


def test_cli_create_interactive_failure(sfx_recorder, session):
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with sfx_recorder.use_cassette('cli_create_interactive_failure',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'create', '-i'], input='n')
        click.echo(result.exception)
        assert result.exception


def test_cli_update_success(sfx_recorder, session):
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with sfx_recorder.use_cassette('cli_update_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'update',
                                          '--description', 'updated_dashboard_description'])
        assert result.exit_code == 0


def test_cli_update_failure(sfx_recorder, session):
    program = Data('cpu.utilization').publish()
    chart = TimeSeriesChart().with_name('lol').with_program(program)

    with sfx_recorder.use_cassette('cli_update_failure',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_charts(chart)

        cli = CliBuilder().with_resources(dashboard).build()

        runner = CliRunner()
        result = runner.invoke(cli, args=['--api-key', 'foo', 'update',
                                          '--description', 'updated_dashboard_description'])
        assert result.exception
