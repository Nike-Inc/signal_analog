import json
import pytest
from betamax_serializers import pretty_json
import betamax
import requests
from mock import patch
from signal_analog.flow import Data
from signal_analog.charts import TimeSeriesChart, PlotType
from signal_analog.dashboards import Dashboard
from signal_analog.errors import ResourceMatchNotFoundError, \
        ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError, \
        SignalAnalogError

# Global config. This will store all recorded requests in the 'mocks' dir
with betamax.Betamax.configure() as config:
    betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.cassette_library_dir = 'tests/mocks'

# Don't get in the habit of doing this, but it simplifies testing
global_session = requests.Session()
global_recorder = betamax.Betamax(global_session)


def mk_chart(name):
    program = Data('cpu.utilization').publish()
    return TimeSeriesChart(session=global_session)\
        .with_name(name)\
        .with_program(program)


def test_dashboard_init():
    dashboard = Dashboard()
    assert dashboard.endpoint == '/dashboard'
    assert dashboard.options == {'charts': []}


def test_dashboard_with_name():
    expected_name = 'SharedInfraTest'
    dashboard = Dashboard().with_name('SharedInfraTest')
    assert dashboard.options['name'] == expected_name


def test_dashboard_with_charts():
    chart1 = mk_chart('chart1')
    chart2 = mk_chart('chart2')

    expected_values = [chart1, chart2]

    dashboard = Dashboard()
    dashboard.with_charts(chart1, chart2)

    list_charts = dashboard.options['charts']
    assert len(list_charts) == 2
    assert set(list_charts) == set(expected_values)


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
    result = dashboard.create(dry_run=True)

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
def test_create_signal_analog_error(input):
    """Test the cases we expect to fail."""
    with global_recorder.use_cassette(input.lower().replace(' ', '_'),
                                      serialize_with='prettyjson'):
        with pytest.raises(SignalAnalogError):
            Dashboard(session=global_session)\
                    .with_name(input)\
                    .with_api_token('foo')\
                    .create()


def test_create_success():
    with global_recorder.use_cassette('create_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(mk_chart('lol'))\
            .create()


def test_create_force_success():
    dashboard = Dashboard(session=global_session)\
        .with_name('testy mctesterson')\
        .with_api_token('foo')\
        .with_charts(mk_chart('lol'))

    with global_recorder.use_cassette('create_success_force',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
        # Force the dashboard to create itself again
        dashboard.create(force=True)


@patch('click.confirm')
def test_create_interactive_success(confirm):
    confirm.__getitem__.return_value = 'y'
    program = Data('cpu.utilization').publish()
    dashboard = Dashboard(session=global_session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(mk_chart('lol'))
    with global_recorder.use_cassette('create_success_interactive',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
        # Force the dashboard to create itself again
        dashboard.create(interactive=True)


@patch('click.confirm')
def test_create_interactive_failure(confirm):
    confirm.__getitem__.return_value = 'n'
    dashboard = Dashboard(session=global_session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(mk_chart('lol'))
    with global_recorder.use_cassette('create_failure_interactive',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
            dashboard.create(interactive=True)


def test_dashboard_update_success():
    with global_recorder.use_cassette('dashboard_update_success',
                                      serialize_with='prettyjson'):
        dashboard = Dashboard(session=global_session) \
            .with_name('testy mctesterson') \
            .with_api_token('foo') \
            .with_charts(mk_chart('lol'))

        dashboard.create()
        dashboard.update(name='updated_dashboard_name',
            description='updated_dashboard_description')


def test_dashboard_update_failure():
    chart = mk_chart('lol')

    dashboard = Dashboard(session=global_session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(chart)
    with global_recorder.use_cassette('dashboard_update_failure',
                                      serialize_with='prettyjson'):
        # Just to make sure there are multiple dashboards exists, create a new dashboard with the same name
        dashboard.create(force=True)
        dashboard.create(force=True)

        with pytest.raises(SignalAnalogError):
            # Verify that we can't update when multiple dashboards exist
            dashboard.update(name='updated_dashboard_name', description='updated_dashboard_description')


def test_dashboard_update_child_chart():
    chart = mk_chart('rawr')

    dashboard = Dashboard(session=global_session)\
        .with_name('foobarium')\
        .with_api_token('foo')\
        .with_charts(chart)

    with global_recorder.use_cassette('dashboard_update_child_chart',
                                      serialize_with='prettyjson'):
        # We expect that updating the chart immediately shouldn't have
        # any effect on the state of the chart.
        dashboard.update()
        resp = dashboard.update()

        # We should only have one chart
        assert len(resp['charts']) == 1


def test_dashboard_create_child_chart():
    chart = mk_chart('rawr')
    chart2 = mk_chart('roar')

    dashboard = Dashboard(session=global_session)\
        .with_name('bariumfoo')\
        .with_api_token('foo')\
        .with_charts(chart)

    with global_recorder.use_cassette('dashboard_create_child_chart',
                                      serialize_with='prettyjson'):
        resp = dashboard.create()
        assert len(resp['charts']) == 1

        # Simulate updating a configuration file.
        dashboard.options['charts'].append(chart2)

        resp_update = dashboard.update()
        assert len(resp_update['charts']) == 2


def test_dashboard_delete_child_chart():
    chart = mk_chart('rawr')
    chart2 = mk_chart('roar')

    dashboard = Dashboard(session=global_session)\
        .with_name('isley brothers')\
        .with_api_token('foo')\
        .with_charts(chart, chart2)

    with global_recorder.use_cassette('dashboard_delete_child_chart',
                                      serialize_with='prettyjson'):
        resp = dashboard.create()
        assert len(resp['charts']) == 2

        # Simulate removing a chart from a user's config.
        dashboard.options['charts'] = list(filter(
            lambda x: x.options != chart2.options, dashboard.options['charts']))

        resp_delete = dashboard.update()
        assert resp_delete is None
