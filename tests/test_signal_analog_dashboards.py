import json
from signal_analog.dashboards import Dashboard
from signal_analog.charts import TimeSeriesChart


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

	chart2 = TimeSeriesChart()
	chart2.with_name('chart2')
	chart2.with_program("data('requests.min').publish()")
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
