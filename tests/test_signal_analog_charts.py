import pytest
from enum import Enum

from signal_analog.charts import Chart, TimeSeriesChart, UnitPrefix, ColorBy, \
                                 PlotType, AxisOption, FieldOption,\
                                 PublishLabelOptions, PaletteColor,\
                                 SingleValueChart, ListChart, SortBy,\
                                 HeatmapChart, SignalFxFieldOption, TextChart
from signal_analog.flow import Data
import signal_analog.util as util
import deprecation


@pytest.mark.parametrize("value", [None, ""])
def test_chart_with_empties(value):
    with pytest.raises(ValueError):
        Chart().with_name(value)
        Chart().with_description(value)
        Chart().with_program()
        FieldOption(value, False)
        PublishLabelOptions(value, value, value, value, value)


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
    assert chart.options['programText'] == expected


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
    assert chart.chart_options['stacked'] is False


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
    field_opt = FieldOption('foo')
    opt = {'fields': [field_opt.to_dict()]}
    chart = TimeSeriesChart().with_legend_options([field_opt])
    assert chart.chart_options['legendOptions'] == opt


def test_ts_chart_with_field_options_disabled():
    field_opt = FieldOption('bar', enabled=False)
    opt = {'fields': [field_opt.to_dict()]}
    chart = TimeSeriesChart().with_legend_options([field_opt])
    assert chart.chart_options['legendOptions'] == opt


def test_ts_chart_with_publish_label_options():
    """'Legacy' behavior, verified still working."""
    opts = PublishLabelOptions(
        'somelabel', 0, PaletteColor.mountain_green, PlotType.area_chart, 'foo'
    )
    chart = TimeSeriesChart().with_publish_label_options(opts)
    assert chart.chart_options['publishLabelOptions'] == [opts.to_dict()]


def test_ts_chart_with_publish_label_options_happy():
    opts = PublishLabelOptions(
        'somelabel', y_axis=1, palette_index=PaletteColor.mountain_green,
        plot_type=PlotType.area_chart, display_name='lol', value_prefix='hi',
        value_suffix='weee', value_unit='hithere')
    chart = TimeSeriesChart().with_publish_label_options(opts)
    assert chart.chart_options['publishLabelOptions'] == [opts.to_dict()]


publish_opts_optionals = ["display_name", "value_prefix", "value_suffix",
                          "value_unit"]
keyword_args = map(lambda x: {x: "foo"}, publish_opts_optionals)
@pytest.mark.parametrize("arg", keyword_args)
def test_ts_chart_with_publish_label_options_missing_option(arg):
    """Test that optional simple keyword arguments can be passed without
       clobbering each other."""
    [(key, value)] = arg.items()
    opts = PublishLabelOptions('someLabel', **arg).to_dict()

    assert opts[util.snake_to_camel(key)] == value
    remaining_values = [x for x in publish_opts_optionals if x is not key]
    for k in opts.keys():
        assert k not in remaining_values


def test_publish_label_options_invalid_y_axis():
    with pytest.raises(ValueError) as ve:
        PublishLabelOptions(
            'somelabel', 2,
            PaletteColor.mountain_green, PlotType.area_chart, 'foo'
        )

        assert "chart must be 0" in ve.message


def test_ts_chart_with_legend_options():
    opts = {'showLegend': True, 'dimensionInLegend': 'foo'}
    chart = TimeSeriesChart()\
        .with_chart_legend_options('foo', show_legend=True)
    assert chart.chart_options['onChartLegendOptions'] == opts


def test_ts_chart_include_zero_options():
    chart = TimeSeriesChart().with_include_zero(True)
    assert chart.chart_options['includeZero'] is True


def test_sv_chart_with_refresh_interval():
    chart = SingleValueChart().with_refresh_interval(5)
    assert chart.chart_options['refreshInterval'] == 5


def test_sv_chart_with_maximum_precision():
    chart = SingleValueChart().with_maximum_precision(6)
    assert chart.chart_options['maximumPrecision'] == 6


def test_sv_chart_with_timestamp_hidden():
    chart = SingleValueChart().with_timestamp_hidden()
    assert chart.chart_options['timestampHidden'] is False

    chart.with_timestamp_hidden(hidden=True)
    assert chart.chart_options['timestampHidden'] is True

@deprecation.fail_if_not_removed
def test_sv_chart_with_sparkline():
    chart = SingleValueChart().with_sparkline_hidden()
    assert chart.chart_options['showSparkLine'] is True

    chart.with_sparkline_hidden(hidden=False)
    assert chart.chart_options['showSparkLine'] is False


def test_sv_chart_with_secondary_visualization():
    chart = SingleValueChart().with_secondary_visualization()
    assert chart.chart_options['secondaryVisualization'] is None

    chart.with_secondary_visualization("Radial")
    assert chart.chart_options['secondaryVisualization'] is "Radial"

    chart.with_secondary_visualization("Linear")
    assert chart.chart_options['secondaryVisualization'] is "Linear"

    chart.with_secondary_visualization("Sparkline")
    assert chart.chart_options['secondaryVisualization'] is "Sparkline"


def test_sv_chart_with_colorscale():
    opts = {'thresholds': [300, 200, 100], 'inverted': True}
    chart = SingleValueChart().with_colorscale([300, 200, 100], inverted=True)
    assert chart.chart_options['colorScale'] == opts


def test_list_chart_with_refresh_interval():
    chart = ListChart().with_refresh_interval(5)
    assert chart.chart_options['refreshInterval'] == 5


def test_list_chart_with_maximum_precision():
    chart = ListChart().with_maximum_precision(1)
    assert chart.chart_options['maximumPrecision'] == 1


@pytest.mark.parametrize("sort_by", SortBy)
def test_list_chart_with_sort_by(sort_by):
    chart = ListChart().with_sort_by(sort_by)
    assert chart.chart_options['sortBy'] == sort_by.value


def test_hm_chart_init():
    assert HeatmapChart().chart_options['type'] == 'Heatmap'


def test_hm_chart_with_colorscale():
    opts = {'thresholds': [70, 50]}
    chart = HeatmapChart().with_colorscale([70, 50])
    assert chart.chart_options['colorScale'] == opts

def test_ts_list_charts_mixin():
    """TimeSeries and ListCharts can set legend options. But not others."""

    opt = {'fields': [{'property': 'foo', 'enabled': False}]}

    ts = TimeSeriesChart()\
            .with_legend_options([FieldOption('foo', enabled=False)])
    assert ts.chart_options['legendOptions'] == opt

    lc = ListChart()\
            .with_legend_options([FieldOption('foo', enabled=False)])
    assert lc.chart_options['legendOptions'] == opt

    with pytest.raises(Exception):
        SingleValueChart().with_legend_options(FieldOption('foo', enabled=False))


def test_sfx_field_options_enum():
    """We expect values from the SignalFxFieldOption enum to be serialized.
    """
    expected = {'fields': [{'property': 'sf_originatingMetric', 'enabled': False}]}

    ts = TimeSeriesChart()\
            .with_legend_options([
                FieldOption(SignalFxFieldOption.plot_name, enabled=False)
            ])

    assert ts.chart_options['legendOptions'] == expected


def test_sfx_field_options_happy():
    """We also expect that string values are still valid."""

    expected = {'fields': [{'property': 'foo', 'enabled': False}]}

    ts = TimeSeriesChart()\
            .with_legend_options([FieldOption('foo', enabled=False)])

    assert ts.chart_options['legendOptions'] == expected


def test_sfx_field_options_invalid():
    """Other enums should not be allowed."""

    class InvalidEnum(Enum):
        foo = 'bar'

    with pytest.raises(ValueError):
        ts = TimeSeriesChart()\
                .with_legend_options([
                    FieldOption(InvalidEnum.foo, enabled=False)
                ])


def test_text_chart_init():
    assert TextChart().chart_options['type'] == 'Text'


def test_text_chart_with_text():
    chart = TextChart().with_markdown("Strong emphasis, aka bold, with **asterisks** or __underscores__.<ol>")
    assert chart.chart_options['markdown'] == 'Strong emphasis, aka bold, with **asterisks** or __underscores__.<ol>'


def test_text_chart_with_empty_text():
    with pytest.raises(ValueError):
        TextChart().with_markdown("")
