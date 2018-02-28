try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json
import sys
from contextlib import contextmanager

import betamax
import pytest
import requests
from betamax_serializers import pretty_json
from mock import patch

from signal_analog.charts import TimeSeriesChart, PlotType
from signal_analog.dashboards import Dashboard, DashboardGroup
from signal_analog.errors import ResourceMatchNotFoundError, \
    ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError, \
    SignalAnalogError
from signal_analog.flow import Data


# Global config. This will store all recorded requests in the 'mocks' dir
with betamax.Betamax.configure() as config:
    betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.cassette_library_dir = 'tests/mocks'

# Don't get in the habit of doing this, but it simplifies testing
global_session = requests.Session()
global_recorder = betamax.Betamax(global_session)


# Method to capture stdout
@contextmanager
def stdout_redirected(new_stdout):
    save_stdout = sys.stdout
    sys.stdout = new_stdout
    try:
        yield None
    finally:
        sys.stdout = save_stdout


def mk_chart(name):
    program = Data('cpu.utilization').publish()
    return TimeSeriesChart(session=global_session)\
        .with_name(name)\
        .with_program(program)


def mk_dashboard(dashboard_name, chart_name):
    return Dashboard(session=global_session)\
        .with_name(dashboard_name)\
        .with_charts(mk_chart(chart_name))


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
def test_create_signal_analog_error(input):
    """Test the cases we expect to fail."""
    with global_recorder.use_cassette(input.lower().replace(' ', '_'),
                                      serialize_with='prettyjson'):
        with pytest.raises(SignalAnalogError):
            Dashboard(session=global_session)\
                    .with_name(input)\
                    .with_api_token('foo')\
                    .create()


def test_dashboard_create_success():
    with global_recorder.use_cassette('dashboard_create_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=global_session)\
            .with_name('testy mctesterson')\
            .with_api_token('foo')\
            .with_charts(mk_chart('lol'))\
            .create()


def test_dashboard_create_force_success():
    dashboard = Dashboard(session=global_session)\
        .with_name('testy mctesterson')\
        .with_api_token('foo')\
        .with_charts(mk_chart('lol'))

    with global_recorder.use_cassette('dashboard_create_success_force',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
        # Force the dashboard to create itself again
        dashboard.create(force=True)


@patch('click.confirm')
def test_dashboard_create_interactive_success(confirm):
    confirm.__getitem__.return_value = 'y'
    dashboard = Dashboard(session=global_session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(mk_chart('lol'))
    with global_recorder.use_cassette('dashboard_create_success_interactive',
                                      serialize_with='prettyjson'):
        # Create our first dashboard
        dashboard.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard.create()
        # Force the dashboard to create itself again
        dashboard.create(interactive=True)


@patch('click.confirm')
def test_dashboard_create_interactive_failure(confirm):
    confirm.__getitem__.return_value = 'n'
    dashboard = Dashboard(session=global_session) \
        .with_name('testy mctesterson') \
        .with_api_token('foo') \
        .with_charts(mk_chart('lol'))
    with global_recorder.use_cassette('dashboard_create_failure_interactive',
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
        # Just to make sure there are multiple dashboards exists, create a new
        # dashboard with the same name
        dashboard.create(force=True)
        dashboard.create(force=True)

        with pytest.raises(SignalAnalogError):
            # Verify that we can't update when multiple dashboards exist
            dashboard.update(name='updated_dashboard_name',
                             description='updated_dashboard_description')


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
            lambda x: x.options != chart2.options,
            dashboard.options['charts']))

        resp_delete = dashboard.update()
        # We should only have one chart
        assert len(resp_delete['charts']) == 1


def test_dashboard_read_success():
    with global_recorder.use_cassette('dashboard_read_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=global_session)\
            .with_api_token('foo')\
            .read('DWgS_7IAgAA')


def test_dashboard_delete_success():
    with global_recorder.use_cassette('dashboard_delete_success',
                                      serialize_with='prettyjson'):
        Dashboard(session=global_session)\
            .with_api_token('foo')\
            .delete('DWgS_7IAgAA')


def test_dashboard_group_create_success():
    with global_recorder.use_cassette('dashboard_group_create_success',
                                      serialize_with='prettyjson'):
        DashboardGroup(session=global_session)\
            .with_name('spaceX')\
            .with_api_token('foo')\
            .create()


def test_dashboard_group_create_force_success():
    dashboard_group = DashboardGroup(session=global_session)\
        .with_name('spaceX')\
        .with_api_token('foo')\

    with global_recorder.use_cassette('dashboard_group_create_success_force',
                                      serialize_with='prettyjson'):
        # Create our first dashboard group
        dashboard_group.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard_group.create()
        # Force the dashboard group to create itself again
        dashboard_group.create(force=True)


@patch('click.confirm')
def test_dashboard_group_create_interactive_success(confirm):
    confirm.__getitem__.return_value = 'y'
    dashboard_group = DashboardGroup(session=global_session) \
        .with_name('spaceX') \
        .with_api_token('foo')
    with global_recorder.use_cassette(
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
def test_dashboard_group_create_interactive_failure(confirm):
    confirm.__getitem__.return_value = 'n'
    dashboard_group = DashboardGroup(session=global_session) \
        .with_name('spaceX') \
        .with_api_token('foo')
    with global_recorder.use_cassette(
        'dashboard_group_create_failure_interactive',
            serialize_with='prettyjson'):

        # Create our first dashboard_group
        dashboard_group.create()
        with pytest.raises(SignalAnalogError):
            # Verify that we can't create it again
            dashboard_group.create()
            dashboard_group.create(interactive=True)


def test_dashboard_group_update_success():

    name = 'spaceX lol'
    updated_name = 'updated_dashboard_group_name'

    with global_recorder.use_cassette('dashboard_group_update_success',
                                      serialize_with='prettyjson'):

        dashboard_group = DashboardGroup(session=global_session)\
            .with_name(name)\
            .with_api_token('foo')

        create_result = dashboard_group.create()

        update_result = dashboard_group\
            .with_id(create_result['id'])\
            .update(name='updated_dashboard_group_name',
                    description='updated_dashboard_group_description')

        assert create_result['name'] == name
        assert update_result['name'] == updated_name


def test_dashboard_group_update_failure():

    dashboard_group = DashboardGroup(session=global_session) \
        .with_name('spaceX') \
        .with_api_token('foo')
    with global_recorder.use_cassette('dashboard_group_update_failure',
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


def test_dashboard_group_with_dashboard_create_success():

    name = 'spaceX unique'
    group = DashboardGroup(session=global_session)\
        .with_name(name)\
        .with_dashboards(mk_dashboard('Falcon99', 'chart1'))\
        .with_api_token('foo')\

    with global_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_success',
            serialize_with='prettyjson'):

        result = group.create()

        assert result['name'] == name
        assert len(result['dashboards']) == 1


def test_dashboard_group_with_dashboard_create_force_success():

    name = 'spaceX'
    dashboard_group = DashboardGroup(session=global_session)\
        .with_name(name) \
        .with_dashboards(mk_dashboard('Falcon99', 'chart1'))\
        .with_api_token('foo')

    with global_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_success_force',
            serialize_with='prettyjson'):

        result = dashboard_group.create(force=True)

        assert result['name'] == name
        assert len(result['dashboards']) == 1


@patch('click.confirm')
def test_dashboard_group_with_dashboard_create_interactive_success(confirm):
    confirm.__getitem__.return_value = 'y'

    name = 'spaceX'

    dashboard_group = DashboardGroup(session=global_session) \
        .with_name(name) \
        .with_dashboards(mk_dashboard('Falcon99', 'chart1')) \
        .with_api_token('foo')

    with global_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_success_interactive',
            serialize_with='prettyjson'):

        result = dashboard_group.create(interactive=True)
        assert result['name'] == name
        assert len(result['dashboards']) == 1


@patch('click.confirm')
def test_dashboard_group_with_dashboard_create_interactive_failure(confirm):
    confirm.__getitem__.return_value = 'n'

    name = 'spaceX'

    dashboard_group = DashboardGroup(session=global_session) \
        .with_name(name) \
        .with_dashboards(mk_dashboard('Falcon99', 'chart1')) \
        .with_api_token('foo')

    with global_recorder.use_cassette(
        'dashboard_group_with_dashboard_create_failure_interactive',
            serialize_with='prettyjson'):

            result = dashboard_group.create(interactive=True)
            assert result['name'] == name
            assert len(result['dashboards']) == 1


def test_dashboard_group_with_dashboard_update_success():
    with global_recorder.use_cassette(
        'dashboard_group_with_dashboard_update_success',
            serialize_with='prettyjson'):

        dashboard_group = DashboardGroup(session=global_session) \
            .with_name('spaceX') \
            .with_dashboards(
                mk_dashboard('Falcon99', 'chart1'),
                mk_dashboard('FalconHeavy', 'chart2')) \
            .with_api_token('foo')

        dashboard_group.update()


def test_dashboard_group_with_delete_existing_dashboard_update_success():
    name = 'spaceX'

    with global_recorder.use_cassette(
        'dashboard_group_with_delete_existing_dashboard_update_success',
            serialize_with='prettyjson'):

        dashboard_group = DashboardGroup(session=global_session) \
            .with_name(name) \
            .with_dashboards(mk_dashboard('Draagoon', 'chart3')) \
            .with_api_token('foo')

        response = dashboard_group.update()

        assert response['name'] == name
        assert len(response['dashboards']) == 1


def test_dashboard_group_read_success():
    with global_recorder.use_cassette('dashboard_group_read_success',
                                      serialize_with='prettyjson'):
        expected = '[prod] Legacyidmapping Application Dashboard Group'
        response = DashboardGroup(session=global_session)\
            .with_api_token('foo')\
            .with_name(expected)\
            .read()

        assert response['name'] == expected


def test_dashboard_group_delete_success():
    with global_recorder.use_cassette('dashboard_group_delete_success',
                                      serialize_with='prettyjson'):
        DashboardGroup(session=global_session)\
            .with_api_token('foo')\
            .delete('DWgXZfyAcAA')


def test_dashboard_group_clone_success():
    with global_recorder.use_cassette('dashboard_group_clone_success',
                                      serialize_with='prettyjson'):
        DashboardGroup(session=global_session)\
            .with_api_token('foo')\
            .clone('DWgX6iYAcAA', 'DWgX6dNAYAA')
