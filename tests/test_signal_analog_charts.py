import pytest

from signal_analog.charts import Chart, TimeSeriesChart, UnitPrefix, ColorBy, \
                                 PlotType
from signal_analog.flow import Data


@pytest.mark.parametrize("value", [None, ""])
def test_chart_with_empties(value):
    with pytest.raises(ValueError):
        Chart().with_name(value)
        Chart().with_description(value)
        Chart().with_program()


def test_chart_init():
    chart = Chart()
    assert chart.endpoint == '/chart'
    assert chart.options == {}


def test_chart_with_name():
    expected = 'El Aparecido'
    chart = Chart().with_name(expected)
    assert chart.options['name'] == expected


def test_chart_with_description():
    expected = 'Petite frere'
    chart = Chart().with_description(expected)
    assert chart.options['description'] == expected


def test_chart_with_program():
    expected = Data('Ms. Communication')
    chart = Chart().with_program(expected)
    assert chart.options['programText'] == str(expected)


def test_ts_chart_init():
    assert TimeSeriesChart().chart_options['type'] == 'TimeSeriesChart'


@pytest.mark.parametrize("bad_input", [None, "", Chart()])
def test_ts_chart_without_enums(bad_input):
    with pytest.raises(ValueError):
        TimeSeriesChart().with_unit_prefix(bad_input)
        TimeSeriesChart().with_color_by(bad_input)
        TimeSeriesChart().with_default_plot_type(bad_input)


@pytest.mark.parametrize("prefix", UnitPrefix)
def test_ts_chart_with_prefix(prefix):
    chart = TimeSeriesChart().with_unit_prefix(prefix)
    assert chart.chart_options['unitPrefix'] == prefix.value


@pytest.mark.parametrize("color_by", ColorBy)
def test_ts_chart_with_color_by(color_by):
    chart = TimeSeriesChart().with_color_by(color_by)
    assert chart.chart_options['colorBy'] == color_by.value


@pytest.mark.parametrize("plot_type", PlotType)
def test_ts_chart_with_default_plot_type(plot_type):
    chart = TimeSeriesChart().with_default_plot_type(plot_type)
    assert chart.chart_options['defaultPlotType'] == plot_type.value


def test_ts_chart_show_event_lines():
    chart = TimeSeriesChart().show_event_lines(True)
    assert chart.chart_options['showEventLines'] == 'true'


def test_ts_chart_stack_chart():
    chart = TimeSeriesChart().stack_chart(False)
    assert chart.chart_options['stack'] == 'false'


def test_ts_chart_with_axis_precision():
    chart = TimeSeriesChart().with_axis_precision(1)
    assert chart.chart_options['axisPrecision'] == 1


not_implemented_methods = [
                             "with_program_options",
                             "with_time_config",
                             "with_axes",
                             "with_legend_options",
                             "with_line_chart_options",
                             "with_area_chart_options",
                             "with_publish_label_options",
                             "with_chart_legend_options"
                          ]


@pytest.mark.parametrize("fn", not_implemented_methods)
def test_not_implemented(fn):
    with pytest.raises(NotImplementedError):
        chart = TimeSeriesChart()
        getattr(chart, fn)()
