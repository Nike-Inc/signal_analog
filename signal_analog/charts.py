from signal_analog.resources import Resource
import signal_analog.util as util
from enum import Enum


class Chart(Resource):

    def __init__(self):
        """Base representation of a chart in SignalFx."""
        super(Chart, self).__init__(endpoint='/chart')
        self.options = {}

    def with_name(self, name):
        """The name to give this chart."""
        util.is_valid(name)
        self.options.update({'name': name})
        return self

    def with_description(self, description):
        """The description to attach to this chart."""
        util.is_valid(description)
        self.options.update({'description': description})
        return self

    def with_program(self, program):
        """The SignalFlow program to execute for this chart.

        For more information SignalFlow consult the `signal_analog.flow`
        module or the upstream SignalFlow documentation here:

        https://developers.signalfx.com/docs/signalflow-overview
        """
        util.is_valid(program)
        self.options.update({'programText': str(program)})
        return self


class UnitPrefix(Enum):
    """Enum for unit prefix types in TimeSeriesCharts."""
    metric = "Metric"
    binary = "Binary"


class ColorBy(Enum):
    """Enum for types of coloring options in TimeSeriesCharts."""
    dimension = "Dimension"
    metric = "Metric"


class PlotType(Enum):
    """The default plot display style for the visualization."""
    line_chart = "LineChart"
    area_chart = "AreaChart"
    column_chart = "ColumnChart"
    histogram = "Histogram"


class PaletteColor(Enum):
    """All available colors for use in charts.

    Semantic names for colors mostly pulled from:
        http://www.htmlcsscolor.com/
    """
    gray = 0
    navy_blue = 1
    sky_blue = 2
    shakespeare = 3
    rust = 4
    tangerine = 5
    sunflower = 6
    mulberry = 7
    hot_pink = 8
    rose = 9
    slate_blue = 10
    violet = 11
    plum = 12
    green = 13
    light_green = 14
    mountain_green = 15


class AxisOption(object):
    """Encapsulation for options on chart axes."""

    def __init__(self, min, max, label, high_watermark, low_watermark):
        for arg in [min, max, label, high_watermark, low_watermark]:
            if not arg:
                raise ValueError("{0} cannot be empty".format(arg))

        if max < min:
            msg = "min cannot be less than max in axis with label {0}"
            raise ValueError(msg.format(label))

        self.opts = {
            'min': min,
            'max': max,
            'label': label,
            'lowWatermark': low_watermark,
            'highWatermark': high_watermark
        }

    def to_dict(self):
        return self.opts


class FieldOption(object):
    """Field options used to display columns in a chart's table."""

    def __init__(self, property, enabled=True):
        if not property:
            raise ValueError('Field option cannot be blank')

        self.opts = {'property': property, 'enabled': enabled}

    def to_dict(self):
        return self.opts


class PublishLabelOptions(object):
    """Options for displaying published timeseries data."""

    def __init__(self, label, y_axis, palette_index, plot_type, display_name):
        for arg in [label, display_name]:
            util.is_valid(arg)
        util.in_given_enum(palette_index, PaletteColor)
        util.in_given_enum(plot_type, PlotType)
        if y_axis not in [0, 1]:
            msg = "YAxis for chart must be 0 (Left) or 1 (Right); " +\
                    "'{0}' provided."
            raise ValueError(msg.format(y_axis))

        self.opts = {
            'label': label,
            'yAxis': y_axis,
            'paletteIndex': palette_index.value,
            'plotType': plot_type.value,
            'displayName': display_name
        }

    def to_dict(self):
        return self.opts


class TimeSeriesChart(Chart):

    def __init__(self):
        """A time series chart."""
        super(TimeSeriesChart, self).__init__()
        self.chart_options = {'type': 'TimeSeriesChart'}

    def with_unit_prefix(self, prefix):
        """Add a unit prefix to this chart."""
        util.is_valid(prefix)
        util.in_given_enum(prefix, UnitPrefix)
        self.chart_options.update({'unitPrefix': prefix.value})
        return self

    def with_color_by(self, color_by):
        """Determine how timeseries are colored in this chart."""
        util.is_valid(color_by)
        util.in_given_enum(color_by, ColorBy)
        self.chart_options.update({'colorBy': color_by.value})
        return self

    def with_program_options(
            self, min_resolution, max_delay, disable_sampling=False):
        """Specify the options to apply to the given SignalFlow program."""

        util.is_valid(min_resolution)
        util.is_valid(max_delay)
        program_opts = {
            'minimumResolution': min_resolution,
            'maxDelay': max_delay,
            'disableSampling': disable_sampling
        }
        self.chart_options.update({'programOptions': program_opts})
        return self

    def with_time_config_relative(self, range):
        """Options to set the relative view window into the given chart."""
        util.is_valid(range)
        opts = {'type': 'relative', 'range': range}
        self.chart_options.update({'time': opts})
        return self

    def with_time_config_absolute(self, start, end):
        """Options to set the absolute view window into the given chart."""
        util.is_valid(start)
        util.is_valid(end)
        opts = {'type': 'absolute', 'start': start, 'end': end}
        self.chart_options.update({'time': opts})
        return self

    def with_axes(self, axes):
        """Options for labeling axes on TimeSeries charts.

        Don't leave your axes laying about or this guy might show up:
        https://youtu.be/V2FygG84bg8
        """
        util.is_valid(axes)
        self.chart_options.update({
            'axes': list(map(lambda x: x.to_dict(), axes))
        })
        return self

    def with_legend_options(self, field_opts):
        util.is_valid(field_opts)
        opts = list(map(lambda x: x.to_dict(), field_opts))
        self.chart_options.update({'fields': opts})
        return self

    def show_event_lines(self, boolean):
        """Whether vertical highlight lines should be drawn in the
           visualizations at times when events occurred.
        """
        self.chart_options.update({'showEventLines': str(boolean).lower()})
        return self

    def __has_opt(self, opt_name):
        return self.chart_options.get(opt_name, None) is not None

    def __with_chart_options(self, clazz, show_data_markers=False):
        plot_type = self.chart_options.get('defaultPlotType', '')
        if plot_type.lower() not in clazz.lower():
            msg = "Attempted to define '{0}' but chart is of type '{1}'"
            raise ValueError(msg.format(clazz, plot_type))

        opts = {'showDataMarkers': show_data_markers}
        self.chart_options.update({clazz: opts})
        return self

    def with_line_chart_options(self, show_data_markers=False):
        return self.__with_chart_options('lineChartOptions', show_data_markers)

    def with_area_chart_options(self, show_data_markers=False):
        return self.__with_chart_options('areaChartOptions', show_data_markers)

    def stack_chart(self, boolean):
        """Whether area and bar charts in the visualization should be
           stacked.
        """
        self.chart_options.update({'stack': str(boolean).lower()})
        return self

    def with_default_plot_type(self, plot_type):
        util.is_valid(plot_type)
        util.in_given_enum(plot_type, PlotType)
        self.chart_options.update({'defaultPlotType': plot_type.value})
        return self

    def with_publish_label_options(self, publish_opts):
        util.is_valid(publish_opts)
        self.chart_options.update(
            {'PublishLabelOptions': publish_opts.to_dict()})
        return self

    def with_axis_precision(self, num):
        """Force a specific number of significant digits in the y-axis."""
        util.is_valid(num)
        self.chart_options.update({'axisPrecision': num})
        return self

    def with_chart_legend_options(self, dimension, show_legend=False):
        """Show the on-chart legend using the given dimension."""
        util.is_valid(dimension)
        opts = {
            'showLegend': show_legend,
            'dimensionInLegend': dimension
        }
        self.chart_options.update({'onChartLegendOptions': opts})
        return self

    def create(self):
        # We want to make sure TimeSeriesChart options are passed
        # before creating resources in SignalFx
        curr_chart_opts = self.options.get('options', {})
        curr_chart_opts.update(self.chart_options)
        self.options.update({
            'options': curr_chart_opts
        })
        return super(TimeSeriesChart, self).create()
