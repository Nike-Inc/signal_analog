try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import betamax
import json
import sys
from contextlib import contextmanager

import pytest
import requests
from mock import patch

from signal_analog.charts import TimeSeriesChart, PlotType
from signal_analog.dashboards import Dashboard, DashboardGroup
from signal_analog.errors import ResourceMatchNotFoundError, \
    ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError, \
    SignalAnalogError
from signal_analog.filters import DashboardFilters, FilterVariable, FilterSource, FilterTime

import signal_analog.error.signalfx as sfxerr


# Method to capture stdout
@contextmanager
def stdout_redirected(new_stdout):
    save_stdout = sys.stdout
    sys.stdout = new_stdout
    try:
        yield None
    finally:
        sys.stdout = save_stdout


def test_dashboard_init():
    dashboard = Dashboard()
    assert dashboard.endpoint == '/dashboard'
    assert dashboard.options == {'charts': []}


def test_dashboard_with_name():
    expected_name = 'SharedInfraTest'
    dashboard = Dashboard().with_name('SharedInfraTest')
    assert dashboard.options['name'] == expected_name


def test_dashboard_with_charts(chart):
    chart1 = chart('chart1')
    chart2 = chart('chart2')

    expected_values = [chart1, chart2]

    dashboard = Dashboard()
    dashboard.with_charts(chart1, chart2)

    list_charts = dashboard.options['charts']
    assert len(list_charts) == 2
    assert set(map(lambda x: x.__get__('name'), list_charts)) \
        == set(map(lambda x: x.__get__('name'), expected_values))


def test_dashboard_create():
    chart1 = TimeSeriesChart()
    chart1.with_name('chart1')
    chart1.with_program("data('requests.min').publish()")
    chart1.with_default_plot_type(PlotType.area_chart)

    chart2 = TimeSeriesChart()
    chart2.with_name('chart2')
    chart2.with_program("data('requests.min').publish()")
    chart2.with_default_plot_type(PlotType.line_chart)

    dashboard_name = 'removeme111'
    dashboard = Dashboard()
    dashboard.with_charts(chart1, chart2)
    dashboard.with_name(dashboard_name)
    f = StringIO()
    with stdout_redirected(f):
        dashboard.create(dry_run=True)

    response = f.getvalue()
    result_string = response[response.find('{'):]\
        .replace('\'', '\"')\
        .replace('("', '(\\"')\
        .replace('")', '\\")')

    result = json.loads(result_string)

    assert 'charts' in result
    assert 'name' in result
    assert len(result['charts']) == 2
    assert result['name'] == dashboard_name
    assert result['charts'][0]['options']['defaultPlotType'] \
        == PlotType.area_chart.value
    assert result['charts'][1]['options']['defaultPlotType'] \
        == PlotType.line_chart.value


def test_dashboard_get_valid():
    dash = Dashboard().with_name('foo')
    assert dash.__get__('name') == 'foo'


def test_dashboard_get_default():
    dash = Dashboard()
    assert dash.__get__('dne', 1) == 1


def test_dashboard_get_invalid():
    dash = Dashboard()
    assert dash.__get__('dne') is None


def test_dashboard_mult_match_invalid():
    dash = Dashboard()
    res = dash.__has_multiple_matches__('foo', [{'name': 'foo'}])
    assert res is False


def test_dashboard_mult_match_valid():
    dash = Dashboard()
    res = dash.__has_multiple_matches__(
        'foo', [{'name': 'foo'}, {'name': 'foo'}])
    assert res is True


def test_find_match_empty():
    dash = Dashboard()
    with pytest.raises(ResourceMatchNotFoundError):
        dash.__find_existing_match__({'count': 0})


def test_find_match_exact():
    response = {
        'count': 1,
        'results': [
            {
                'name': 'foo'
            }
        ]
    }

    dash = Dashboard().with_name('foo')
    with pytest.raises(ResourceAlreadyExistsError):
        dash.__find_existing_match__(response)


def test_find_match_duplicate_matches():
    response = {
        'count': 1,
        'results': [
            {
                'name': 'foo'
            },
            {
                'name': 'foo'
            }
        ]
    }
    dash = Dashboard().with_name('foo')
    with pytest.raises(ResourceHasMultipleExactMatchesError):
        dash.__find_existing_match__(response)


def test_find_match_none():
    response = {
        'count': 1,
        'results': [
            {
                'name': 'bar'
            }
        ]
    }

    dash = Dashboard().with_name('foo')
    with pytest.raises(ResourceMatchNotFoundError):
        dash.__find_existing_match__(response)


@pytest.mark.parametrize('input',
                         ['Shoeadmin Application Dashboard',
                          'Riposte Template Dashboard'])
def test_create_signal_analog_error(input, session, sfx_recorder):
    """Test the cases we expect to fail."""
    with sfx_recorder.use_cassette(input.lower().replace(' ', '_'),
                                      serialize_with='prettyjson'):
        with pytest.raises(SignalAnalogError):
            Dashboard(session=session)\
                    .with_name(input)\
                    .with_api_token('foo')\
                    .create()


def test_dashboard_create_success(sfx_recorder, session, chart):
    with sfx_recorder.use_cassette('dashboard_create_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .create()


def test_dashboard_create_force_success(sfx_recorder, session, chart):
    dashboard = Dashboard(session=session)\
        .with_name('testy mctesterson')\
        .with_api_token('foo')\
        .with_charts(chart('lol'))

    with sfx_recorder.use_cassette('dashboard_create_success_force',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
        # Force the dashboard to create itself again
        dashboard.create(force=True)


@patch('click.confirm')
def test_dashboard_create_interactive_success(confirm, sfx_recorder, session, chart):
    confirm.__getitem__.return_value = 'y'
    dashboard = Dashboard(session=session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(chart('lol'))
    with sfx_recorder.use_cassette('dashboard_create_success_interactive',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
        # Force the dashboard to create itself again
        dashboard.create(interactive=True)


@patch('click.confirm')
def test_dashboard_create_interactive_failure(confirm, sfx_recorder, session, chart):
    confirm.__getitem__.return_value = 'n'
    dashboard = Dashboard(session=session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(chart('lol'))
    with sfx_recorder.use_cassette('dashboard_create_failure_interactive',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
            dashboard.create(interactive=True)


def test_dashboard_update_success(sfx_recorder, session, chart):
    with sfx_recorder.use_cassette('dashboard_update_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol'))

        dashboard.create()
        dashboard.update(name='updated_dashboard_name',
                         description='updated_dashboard_description')


def test_dashboard_update_failure(sfx_recorder, session, chart):
    chart = chart('lol')

    dashboard = Dashboard(session=session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(chart)
    with sfx_recorder.use_cassette('dashboard_update_failure',
                                      serialize_with='prettyjson'):
        # Just to make sure there are multiple dashboards exists, create a new
        # dashboard with the same name
        dashboard.create(force=True)
        dashboard.create(force=True)

        with pytest.raises(SignalAnalogError):
            # Verify that we can't update when multiple dashboards exist
            dashboard.update(name='updated_dashboard_name',
                             description='updated_dashboard_description')


def test_dashboard_update_child_chart(sfx_recorder, session, chart):
    chart = chart('rawr')

    dashboard = Dashboard(session=session)\
        .with_name('foobarium')\
        .with_api_token('foo')\
        .with_charts(chart)

    with sfx_recorder.use_cassette('dashboard_update_child_chart',
                                      serialize_with='prettyjson'):
        # We expect that updating the chart immediately shouldn't have
        # any effect on the state of the chart.
        dashboard.update()
        resp = dashboard.update()

        # We should only have one chart
        assert len(resp['charts']) == 1


def test_dashboard_create_child_chart(sfx_recorder, session, chart):
    chart1 = chart('rawr')
    chart2 = chart('roar')

    dashboard = Dashboard(session=session)\
        .with_name('bariumfoo')\
        .with_api_token('foo')\
        .with_charts(chart1)

    with sfx_recorder.use_cassette('dashboard_create_child_chart',
                                      serialize_with='prettyjson'):
        resp = dashboard.create()
        assert len(resp['charts']) == 1

        # Simulate updating a configuration file.
        dashboard.options['charts'].append(chart2)

        resp_update = dashboard.update()
        assert len(resp_update['charts']) == 2


def test_dashboard_delete_child_chart(sfx_recorder, session, chart):
    chart1 = chart('rawr')
    chart2 = chart('roar')

    dashboard = Dashboard(session=session)\
        .with_name('isley brothers')\
        .with_api_token('foo')\
        .with_charts(chart1, chart2)

    with sfx_recorder.use_cassette('dashboard_delete_child_chart',
                                      serialize_with='prettyjson'):
        resp = dashboard.create()
        assert len(resp['charts']) == 2

        # Simulate removing a chart from a user's config.
        dashboard.options['charts'] = list(filter(
            lambda x: x.options != chart2.options,
            dashboard.options['charts']))

        resp_delete = dashboard.update()
        # We should only have one chart
        assert len(resp_delete['charts']) == 1


def test_dashboard_create_with_filters_with_one_variable_success(sfx_recorder, session, chart):
    app_var = FilterVariable().with_alias('app') \
        .with_property('app') \
        .with_is_required(True) \
        .with_value('bar')

    dashboard_filter = DashboardFilters() \
        .with_variables(app_var)

    with sfx_recorder.use_cassette('dashboard_create_with_filters_with_one_variable_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_with_multiple_variables_success(sfx_recorder, session, chart):
    app_var = FilterVariable().with_alias('app') \
        .with_property('app') \
        .with_is_required(True) \
        .with_value('bar')

    env_var = FilterVariable().with_alias('env') \
        .with_property('env') \
        .with_is_required(True) \
        .with_value('prod')

    dashboard_filter = DashboardFilters() \
        .with_variables(app_var, env_var)

    with sfx_recorder.use_cassette('dashboard_create_with_filters_with_multiple_variables_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_with_multiple_values_success(sfx_recorder, session, chart):
    app_var = FilterVariable().with_alias('app') \
        .with_property('app') \
        .with_is_required(True) \
        .with_value('bar1', 'bar2')

    dashboard_filter = DashboardFilters() \
        .with_variables(app_var)

    with sfx_recorder.use_cassette('dashboard_create_with_filters_with_multiple_values_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_with_empty_alias_failure(session, chart):
    with pytest.raises(ValueError):
        app_var = FilterVariable().with_alias('') \
            .with_property('app') \
            .with_is_required(True) \
            .with_value('bar')

        dashboard_filter = DashboardFilters() \
            .with_variables(app_var)

        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_with_empty_property_failure(session, chart):
    with pytest.raises(ValueError):
        app_var = FilterVariable().with_alias('app') \
            .with_property('') \
            .with_is_required(True) \
            .with_value('bar')

        dashboard_filter = DashboardFilters() \
            .with_variables(app_var)

        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_with_missing_alias_failure(session, chart):
    with pytest.raises(ValueError):
        app_var = FilterVariable().with_property('app') \
            .with_is_required(True) \
            .with_value('bar')

        dashboard_filter = DashboardFilters() \
            .with_variables(app_var)

        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_with_missing_property_failure(session, chart):
    with pytest.raises(ValueError):
        app_var = FilterVariable().with_alias('app') \
            .with_is_required(True) \
            .with_value('bar')

        dashboard_filter = DashboardFilters() \
            .with_variables(app_var)

        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_with_unexpected_data_type_failure(session, chart):
    with pytest.raises(ValueError):
        app_var = FilterVariable().with_alias('app') \
            .with_is_required("THIS SHOULD BE BOOLEAN NOT A STRING") \
            .with_value('bar')

        dashboard_filter = DashboardFilters() \
            .with_variables(app_var)

        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_source_success(sfx_recorder, session, chart):
    aws_src = FilterSource()\
        .with_property("aws_region")\
        .with_value("us-west-2")

    dashboard_filter = DashboardFilters()\
        .with_sources(aws_src)

    with sfx_recorder.use_cassette('dashboard_create_with_filters_source_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_source_NOT_success(sfx_recorder, session, chart):
    aws_src = FilterSource()\
        .with_property("aws_region")\
        .with_value("us-west-2") \
        .with_is_not(True)

    dashboard_filter = DashboardFilters()\
        .with_sources(aws_src)

    with sfx_recorder.use_cassette('dashboard_create_with_filters_source_NOT_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_source_with_empty_property_failure(session, chart):
    with pytest.raises(ValueError):
        aws_src = FilterSource() \
            .with_property("") \
            .with_value("us-west-2")

        dashboard_filter = DashboardFilters() \
            .with_sources(aws_src)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_source_with_empty_value_failure(session, chart):
    with pytest.raises(ValueError):
        aws_src = FilterSource() \
            .with_property("aws_region") \
            .with_value("")

        dashboard_filter = DashboardFilters() \
            .with_sources(aws_src)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_source_with_empty_is_not_failure(session, chart):
    with pytest.raises(ValueError):
        aws_src = FilterSource() \
            .with_property("aws_region") \
            .with_value("") \
            .with_is_not('')

        dashboard_filter = DashboardFilters() \
            .with_sources(aws_src)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_source_with_missing_property_failure(session, chart):
    with pytest.raises(ValueError):
        aws_src = FilterSource() \
            .with_value("us-west-2")

        dashboard_filter = DashboardFilters() \
            .with_sources(aws_src)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_source_with_missing_value_failure(session, chart):
    with pytest.raises(ValueError):
        aws_src = FilterSource() \
            .with_property("aws_region")

        dashboard_filter = DashboardFilters() \
            .with_sources(aws_src)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_source_with_missing_property_and_value_failure(session, chart):
    with pytest.raises(ValueError):
        aws_src = FilterSource()

        dashboard_filter = DashboardFilters() \
            .with_sources(aws_src)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_as_string_success(sfx_recorder, session, chart):
    time = FilterTime()\
        .with_start("-1h")\
        .with_end("Now")

    dashboard_filter = DashboardFilters()\
        .with_time(time)

    with sfx_recorder.use_cassette('dashboard_create_with_filters_time_as_string_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_time_as_integer_success(sfx_recorder, session, chart):
    time = FilterTime()\
        .with_start(1523721600000)\
        .with_end(1523808000000)

    dashboard_filter = DashboardFilters()\
        .with_time(time)

    with sfx_recorder.use_cassette('dashboard_create_with_filters_time_as_integer_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .create()


def test_dashboard_create_with_filters_time_empty_start_time_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime() \
            .with_start('') \
            .with_end('Now')

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_empty_end_time_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime() \
            .with_start('-1h') \
            .with_end('')

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_missing_start_time_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime() \
            .with_end('Now')

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_missing_end_time_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime() \
            .with_start('-1h')

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_missing_start_and_end_time_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_and_end_time_as_different_data_types_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start(1523808000000)\
            .with_end("Now")

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_and_end_time_as_unsupported_data_type_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start(True)\
            .with_end(False)

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_first_character_is_not_negative_sign_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start("1h")\
            .with_end("Now")

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_unexpected_last_character_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start("-1z")\
            .with_end("Now")

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_no_positive_integer_after_negative_sign_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start("--1h")\
            .with_end("Now")

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_no_integer_after_negative_sign_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start("-zh")\
            .with_end("Now")

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_end_time_is_not_Now_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start("-1h")\
            .with_end("Not Now")

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_and_end_time_are_negative_integers_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start(-1523808000000)\
            .with_end(-1523894400000)

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_time_is_negative_integer_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start(-1523808000000)\
            .with_end(1523894400000)

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_end_time_is_negative_integer_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start(1523808000000)\
            .with_end(-1523894400000)

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_filters_time_start_time_is_not_less_than_end_time_failure(session, chart):
    with pytest.raises(ValueError):
        time = FilterTime()\
            .with_start(1523894400000)\
            .with_end(1523808000000)

        dashboard_filter = DashboardFilters() \
            .with_time(time)

        Dashboard(session=session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(chart('lol')) \
            .with_filters(dashboard_filter) \
            .create()


def test_dashboard_create_with_dashboard_group_id_success(sfx_recorder, session, chart):
    with sfx_recorder.use_cassette('dashboard_create_with_dashboard_group_id_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .create(group_id='DnogQGhAcAA')


def test_dashboard_create_with_invalid_dashboard_group_id_failure(session, chart):
    with pytest.raises(sfxerr.SignalFxError):
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .create(group_id='asdf;lkj')


def test_dashboard_update_with_filters_success(sfx_recorder, session, chart):
    app_var = FilterVariable().with_alias('app') \
        .with_property('app') \
        .with_is_required(True) \
        .with_value('bar')

    env_var = FilterVariable().with_alias('env') \
        .with_property('env') \
        .with_is_required(True) \
        .with_value('prod')

    dashboard_filter = DashboardFilters() \
        .with_variables(app_var, env_var)

    with sfx_recorder.use_cassette('dashboard_update_with_filters_success',
                                      serialize_with='prettyjson'):

        # This Dashboard does not exist. So, a new dashboard should be created
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .update()


def test_dashboard_update_existing_dashboard_with_filters_success(sfx_recorder, session, chart):

    app_var = FilterVariable().with_alias('app') \
        .with_property('app') \
        .with_is_required(True) \
        .with_value('bar1', 'bar2')

    dashboard_filter = DashboardFilters() \
        .with_variables(app_var)

    with sfx_recorder.use_cassette('dashboard_update_with_filters_success',
                                      serialize_with='prettyjson'):

        # This Dashboard already exists. So, it will be updated
        Dashboard(session=session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(chart('lol'))\
            .with_filters(dashboard_filter)\
            .update()


def test_dashboard_read_success(sfx_recorder, session):
    with sfx_recorder.use_cassette('dashboard_read_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_api_token('foo')\
            .read('DWgS_7IAgAA')


def test_dashboard_delete_success(sfx_recorder, session):
    with sfx_recorder.use_cassette('dashboard_delete_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=session)\
            .with_api_token('foo')\
            .delete('DWgS_7IAgAA')


def test_dashboard_group_create_success(sfx_recorder, session):
    with sfx_recorder.use_cassette('dashboard_group_create_success',
                                      serialize_with='prettyjson'):
        DashboardGroup(session=session)\
            .with_name('spaceX')\
            .with_api_token('foo')\
            .create()


def test_dashboard_group_create_force_success(sfx_recorder, session):
    dashboard_group = DashboardGroup(session=session)\
        .with_name('spaceX')\
        .with_api_token('foo')\

    with sfx_recorder.use_cassette('dashboard_group_create_success_force',
                                      serialize_with='prettyjson'):
        # Create our first dashboard group
        dashboard_group.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard_group.create()
        # Force the dashboard group to create itself again
        dashboard_group.create(force=True)


@patch('click.confirm')
def test_dashboard_group_create_interactive_success(confirm, sfx_recorder, session):
    confirm.__getitem__.return_value = 'y'
    dashboard_group = DashboardGroup(session=session) \
        .with_name('spaceX') \
        .with_api_token('foo')
    with sfx_recorder.use_cassette(
        'dashboard_group_create_success_interactive',
            serialize_with='prettyjson'):

        # Create our first dashboard group
        dashboard_group.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard_group.create()
        # Run the dashboard group creation in interactive mode
        dashboard_group.create(interactive=True)


@patch('click.confirm')
def test_dashboard_group_create_interactive_failure(confirm, sfx_recorder, session):
    confirm.__getitem__.return_value = 'n'
    dashboard_group = DashboardGroup(session=session) \
        .with_name('spaceX') \
        .with_api_token('foo')
    with sfx_recorder.use_cassette(
        'dashboard_group_create_failure_interactive',
            serialize_with='prettyjson'):

        # Create our first dashboard_group
        dashboard_group.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard_group.create()
            dashboard_group.create(interactive=True)


def test_dashboard_group_update_success(sfx_recorder, session):
    # Enforcing the request body helps to prevent a defect from being masked due to over-mocking
    # the requests/responses.
    with betamax.Betamax.configure() as config:
        initial_cassette_options = config.default_cassette_options['match_requests_on']
        config.default_cassette_options['match_requests_on'] = ['body', 'method', 'uri']

        with sfx_recorder.use_cassette('dashboard_group_update_success',
            serialize_with='prettyjson'):
            name = 'spaceX lol'
            updated_name = 'updated_dashboard_group_name'
            updated_team_id = 'updated_team_id'

            dashboard_group = DashboardGroup(session=session)\
                .with_name(name)\
                .with_api_token('foo')

            create_result = dashboard_group.create()

            update_result = dashboard_group\
                .with_id(create_result['id'])\
                .with_teams(updated_team_id)\
                .update(name='updated_dashboard_group_name',
                        description='updated_dashboard_group_description')

            assert create_result['name'] == name
            assert update_result['name'] == updated_name
            assert updated_team_id in update_result['teams']

        with betamax.Betamax.configure() as config:
            config.default_cassette_options['match_requests_on'] = initial_cassette_options


def test_dashboard_group_update_failure(sfx_recorder, session):

    dashboard_group = DashboardGroup(session=session) \
        .with_name('spaceX') \
        .with_api_token('foo')
    with sfx_recorder.use_cassette('dashboard_group_update_failure',
                                      serialize_with='prettyjson'):
        # Just to make sure there are multiple dashboard groups exists,
        # create a new dashboard group with the same name
        dashboard_group.create(force=True)
        dashboard_group.create(force=True)

        with pytest.raises(SignalAnalogError):
            # Verify that we can't update when multiple dashboard groups exist
            dashboard_group.update(
                name='updated_dashboard_group_name',
                description='updated_dashboard_group_description')


def test_dashboard_group_with_dashboard_create_success(sfx_recorder, session, dashboard):

    name = 'spaceX unique'
    group = DashboardGroup(session=session)\
        .with_name(name)\
        .with_dashboards(dashboard('Falcon99', 'chart1'))\
        .with_api_token('foo')\

    with sfx_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_success',
            serialize_with='prettyjson'):

        result = group.create()

        assert result['name'] == name
        assert len(result['dashboards']) == 1


def test_dashboard_group_with_dashboard_create_force_success(sfx_recorder, session, dashboard):

    name = 'spaceX'
    dashboard_group = DashboardGroup(session=session)\
        .with_name(name) \
        .with_dashboards(dashboard('Falcon99', 'chart1'))\
        .with_api_token('foo')

    with sfx_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_success_force',
            serialize_with='prettyjson'):

        result = dashboard_group.create(force=True)

        assert result['name'] == name
        assert len(result['dashboards']) == 1


@patch('click.confirm')
def test_dashboard_group_with_dashboard_create_interactive_success(confirm, sfx_recorder, session, dashboard):
    confirm.__getitem__.return_value = 'y'

    name = 'spaceX'

    dashboard_group = DashboardGroup(session=session) \
        .with_name(name) \
        .with_dashboards(dashboard('Falcon99', 'chart1')) \
        .with_api_token('foo')

    with sfx_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_success_interactive',
            serialize_with='prettyjson'):

        result = dashboard_group.create(interactive=True)
        assert result['name'] == name
        assert len(result['dashboards']) == 1


@patch('click.confirm')
def test_dashboard_group_with_dashboard_create_interactive_failure(confirm, sfx_recorder, session, dashboard):
    confirm.__getitem__.return_value = 'n'

    name = 'spaceX'

    dashboard_group = DashboardGroup(session=session) \
        .with_name(name) \
        .with_dashboards(dashboard('Falcon99', 'chart1')) \
        .with_api_token('foo')

    with sfx_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_failure_interactive',
            serialize_with='prettyjson'):

            result = dashboard_group.create(interactive=True)
            assert result['name'] == name
            assert len(result['dashboards']) == 1


def test_dashboard_group_with_dashboard_update_success(sfx_recorder, session, dashboard):
    with sfx_recorder.use_cassette(
        'dashboard_group_with_dashboard_update_success',
            serialize_with='prettyjson'):

        dashboard_group = DashboardGroup(session=session) \
            .with_name('spaceX') \
            .with_dashboards(
                dashboard('Falcon99', 'chart1'),
                dashboard('FalconHeavy', 'chart2')) \
            .with_api_token('foo')

        dashboard_group.update()


def test_dashboard_group_with_delete_existing_dashboard_update_success(sfx_recorder, session, dashboard):
    name = 'spaceX'

    with sfx_recorder.use_cassette(
        'dashboard_group_with_delete_existing_dashboard_update_success',
            serialize_with='prettyjson'):

        dashboard_group = DashboardGroup(session=session) \
            .with_name(name) \
            .with_dashboards(dashboard('Draagoon', 'chart3')) \
            .with_api_token('foo')

        response = dashboard_group.update()

        assert response['name'] == name
        assert len(response['dashboards']) == 1


def test_dashboard_group_read_success(sfx_recorder, session):
    with sfx_recorder.use_cassette('dashboard_group_read_success',
                                      serialize_with='prettyjson'):
        expected = '[prod] Legacyidmapping Application Dashboard Group'
        response = DashboardGroup(session=session)\
            .with_api_token('foo')\
            .with_name(expected)\
            .read()

        assert response['name'] == expected


def test_dashboard_group_delete_success(sfx_recorder, session):
    with sfx_recorder.use_cassette('dashboard_group_delete_success',
                                      serialize_with='prettyjson'):
        DashboardGroup(session=session)\
            .with_api_token('foo')\
            .delete('DWgXZfyAcAA')


def test_dashboard_group_clone_success(sfx_recorder, session):
    with sfx_recorder.use_cassette('dashboard_group_clone_success',
                                      serialize_with='prettyjson'):
        DashboardGroup(session=session)\
            .with_api_token('foo')\
            .clone('DWgX6iYAcAA', 'DWgX6dNAYAA')


def test_dashboard_group_with_team_noop():
    group = DashboardGroup()

    # Sfx API will ignore an empty teams object, so this is harmless.
    assert group.with_teams().options['teams'] == []


def test_dashboard_group_with_team_happy():
    expected = '1234'
    group = DashboardGroup().with_teams(expected)

    assert group.options['teams'] == [expected]
