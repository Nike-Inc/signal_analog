from signal_analog.resources import Resource
from enum import Enum


class Chart(Resource):

    def __init__(self):
        """Base representation of a chart in SignalFx."""
        super(Chart, self).__init__(endpoint='/chart')
        self.options = {}

    def with_name(self, name):
        """The name to give this chart."""
        self.is_valid(name)
        self.options.update({'name': name})
        return self

    def with_description(self, description):
        """The description to attach to this chart."""
        self.is_valid(description)
        self.options.update({'description': description})
        return self

    def with_program(self, program):
        """The SignalFlow program to execute for this chart.

        For more information SignalFlow consult the `signal_analog.flow`
        module or the upstream SignalFlow documentation here:

        https://developers.signalfx.com/docs/signalflow-overview
        """
        self.is_valid(program)
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


class TimeSeriesChart(Chart):

    def __init__(self):
        """A time series chart."""
        super(TimeSeriesChart, self).__init__()
        self.chart_options = {'type': 'TimeSeriesChart'}

    def in_given_enum(self, value, enum):
        if type(value) != enum or value not in enum:
            msg = '"{0}" must be one of {1} for given {2}.'
            valid_values = [x.value for x in enum]
            raise ValueError(
                msg.format(value, valid_values, type(self).__name__))

    def with_unit_prefix(self, prefix):
        """Add a unit prefix to this chart."""
        self.is_valid(prefix)
        self.in_given_enum(prefix, UnitPrefix)
        self.chart_options.update({'unitPrefix': prefix.value})
        return self

    def with_color_by(self, color_by):
        """Determine how timeseries are colored in this chart."""
        self.is_valid(color_by)
        self.in_given_enum(color_by, ColorBy)
        self.chart_options.update({'colorBy': color_by.value})
        return self

    def with_program_options(
            self, min_resolution, max_delay, disable_sampling=False):
        """Specify the options to apply to the given SignalFlow program."""

        self.is_valid(min_resolution)
        self.is_valid(max_delay)
        program_opts = {
            'minimumResolution': min_resolution,
            'maxDelay': max_delay,
            'disableSampling': disable_sampling
        }
        self.chart_options.update({'programOptions': program_opts})
        return self

    def with_time_config_relative(self, range):
        """Options to set the relative view window into the given chart."""
        self.is_valid(range)
        opts = {'type': 'relative', 'range': range}
        self.chart_options.update({'time': opts})
        return self

    def with_time_config_absolute(self, start, end):
        """Options to set the absolute view window into the given chart."""
        self.is_valid(start)
        self.is_valid(end)
        opts = {'type': 'absolute', 'start': start, 'end': end}
        self.chart_options.update({'time': opts})
        return self

    def with_axes(self, axes):
        """Options for labeling axes on TimeSeries charts.

        Don't leave your axes laying about or this guy might show up:
        https://youtu.be/V2FygG84bg8
        """
        self.is_valid(axes)
        self.chart_options.update({
            'axes': list(map(lambda x: x.to_dict(), axes))
        })
        return self

    def with_legend_options(self, field_opts):
        self.is_valid(field_opts)
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
        self.is_valid(plot_type)
        self.in_given_enum(plot_type, PlotType)
        self.chart_options.update({'defaultPlotType': plot_type.value})
        return self

    def with_publish_label_options(self):
        raise NotImplementedError()

    def with_axis_precision(self, num):
        """Force a specific number of significant digits in the y-axis."""
        self.is_valid(num)
        self.chart_options.update({'axisPrecision': num})
        return self

    def with_chart_legend_options(self):
        raise NotImplementedError()

    def create(self):
        # We want to make sure TimeSeriesChart options are passed
        # before creating resources in SignalFx
        curr_chart_opts = self.options.get('options', {})
        curr_chart_opts.update(self.chart_options)
        self.options.update({
            'options': curr_chart_opts
        })
        return super(TimeSeriesChart, self).create()
