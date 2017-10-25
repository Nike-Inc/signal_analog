import pytest

from signal_analog.charts import Chart, TimeSeriesChart, UnitPrefix, ColorBy, \
                                 PlotType, AxisOption, FieldOption
from signal_analog.flow import Data


@pytest.mark.parametrize("value", [None, ""])
def test_chart_with_empties(value):
    with pytest.raises(ValueError):
        Chart().with_name(value)
        Chart().with_description(value)
        Chart().with_program()
        AxisOption(value, value, value, value, value)
        FieldOption(value, False)


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


def test_ts_chart_with_program_opts():
    opts = {'minimumResolution': 1, 'maxDelay': 2, 'disableSampling': False}
    chart = TimeSeriesChart().with_program_options(1, 2)
    assert chart.chart_options['programOptions'] == opts


def test_ts_chart_with_time_config_relative():
    opts = {'type': 'relative', 'range': 1000}
    chart = TimeSeriesChart().with_time_config_relative(1000)
    assert chart.chart_options['time'] == opts


def test_ts_chart_with_time_config_absolute():
    opts = {'type': 'absolute', 'start': 1, 'end': 2}
    chart = TimeSeriesChart().with_time_config_absolute(1, 2)
    assert chart.chart_options['time'] == opts


def test_ts_chart_overwrite_time_config():
    """Ensure that relative/absolute options overwrite each other"""
    opts_a = {'type': 'absolute', 'start': 1, 'end': 2}
    opts_r = {'type': 'relative', 'range': 1000}

    chart = TimeSeriesChart().with_time_config_absolute(1, 2)

    assert chart.chart_options['time'] == opts_a

    chart.with_time_config_relative(1000)

    assert chart.chart_options['time'] != opts_a
    assert chart.chart_options['time'] == opts_r


def test_axis_option_max_greater_than_min():
    with pytest.raises(ValueError):
        AxisOption(1, 0, 'evil', 1, 2)


def test_ts_chart_with_axes():
    axis_of_evil = AxisOption(1, 2, 'evil', 1, 2)
    opts = [axis_of_evil.to_dict()]

    chart = TimeSeriesChart().with_axes([axis_of_evil])

    assert chart.chart_options['axes'] == opts


def test_ts_chart_with_linechart_options():
    opts = {'showDataMarkers': False}
    chart = TimeSeriesChart()\
        .with_default_plot_type(PlotType.line_chart)\
        .with_line_chart_options()
    assert chart.chart_options['lineChartOptions'] == opts


def test_ts_chart_with_areachart_options():
    opts = {'showDataMarkers': False}
    chart = TimeSeriesChart()\
        .with_default_plot_type(PlotType.area_chart)\
        .with_area_chart_options()
    assert chart.chart_options['areaChartOptions'] == opts


def test_ts_chart_with_modified_linechart_options():
    opts = {'showDataMarkers': True}
    chart = TimeSeriesChart()\
        .with_default_plot_type(PlotType.area_chart)\
        .with_area_chart_options(show_data_markers=True)
    assert chart.chart_options['areaChartOptions'] == opts


def test_ts_chart_with_wrong_chart_options():
    with pytest.raises(ValueError):
        TimeSeriesChart()\
            .with_default_plot_type(PlotType.area_chart)\
            .with_line_chart_options()


def test_ts_chart_with_field_options():
    opt = FieldOption('foo')
    chart = TimeSeriesChart().with_legend_options([opt])
    assert chart.chart_options['fields'] == [opt.to_dict()]


def test_ts_chart_with_field_options_disabled():
    opt = FieldOption('bar', enabled=False)
    chart = TimeSeriesChart().with_legend_options([opt])
    assert chart.chart_options['fields'] == [opt.to_dict()]


not_implemented_methods = [
                             "with_publish_label_options",
                             "with_chart_legend_options"
                          ]


@pytest.mark.parametrize("fn", not_implemented_methods)
def test_not_implemented(fn):
    with pytest.raises(NotImplementedError):
        chart = TimeSeriesChart()
        getattr(chart, fn)()
