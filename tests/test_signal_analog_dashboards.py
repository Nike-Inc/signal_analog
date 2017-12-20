import json
import pytest

from signal_analog.charts import TimeSeriesChart, PlotType
from signal_analog.dashboards import Dashboard
from signal_analog.errors import DashboardMatchNotFoundError, \
        DashboardHasMultipleExactMatchesError, DashboardAlreadyExistsError


def test_dashboard_init():
    dashboard = Dashboard()
    assert dashboard.endpoint == '/dashboard/simple'
    assert dashboard.options == {'charts': []}


def test_dashboard_with_name():
    expected_name = 'SharedInfraTest'
    dashboard = Dashboard().with_name('SharedInfraTest')
    assert dashboard.options['name'] == expected_name


def test_dashboard_with_charts():
    chart1 = TimeSeriesChart()
    chart1.with_name('chart1')
    chart1.with_program("data('requests.min').publish()")

    chart2 = TimeSeriesChart()
    chart2.with_name('chart2')
    chart2.with_program("data('requests.min').publish()")

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
    result_dict = json.loads(result)

    assert 'charts' in result_dict
    assert 'name' in result_dict
    assert len(result_dict['charts']) == 2
    assert result_dict['name'] == dashboard_name
    assert result_dict['charts'][0]['options']['defaultPlotType']\
        == PlotType.area_chart.value
    assert result_dict['charts'][1]['options']['defaultPlotType']\
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
    with pytest.raises(DashboardMatchNotFoundError):
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
    with pytest.raises(DashboardAlreadyExistsError):
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
    with pytest.raises(DashboardHasMultipleExactMatchesError):
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
    with pytest.raises(DashboardMatchNotFoundError):
        dash.__find_existing_match__(response)


def test_get_existing_dashboards():
    """Make sure we don't make network requests if we don't have a name."""
    with pytest.raises(ValueError):
        Dashboard().__get_existing_dashboards__()
