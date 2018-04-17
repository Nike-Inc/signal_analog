"""Chart objects representable in the SignalFX API."""

from copy import deepcopy
from enum import Enum

import signal_analog.util as util
from signal_analog.errors import ResourceMatchNotFoundError, \
    ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError
from signal_analog.resources import Resource


class Chart(Resource):
    """Base representation of a chart in SignalFx."""

    def __init__(self, session=None):
        super(Chart, self).__init__(endpoint='/chart', session=session)
        self.options = {}

    def __str__(self):
        s = "{0}(options={1})"
        return s.format(self.__class__.__name__, self.options)

    def with_id(self, id):
        """The unique identifier for this chart.

        Useful when updating/deleting charts.
        """
        util.assert_valid(id)
        self.options.update({'id': id})
        return self

    def with_program(self, program):
        """The SignalFlow program to execute for this chart.

        For more information SignalFlow consult the `signal_analog.flow`
        module or the upstream SignalFlow documentation here:

        https://developers.signalfx.com/docs/signalflow-overview
        """
        util.assert_valid(program)
        self.options.update({'programText': program})
        return self

    def to_dict(self):
        curr_chart_opts = deepcopy(self.options.get('options', {}))
        curr_chart_opts.update(self.chart_options)

        chart_opts_copy = deepcopy(self.options)
        chart_opts_copy.update({
            'options': curr_chart_opts
        })

        chart_opts_copy.update({
            'programText': str(chart_opts_copy['programText'])
        })

        return chart_opts_copy

    def create(self, dry_run=False):
        """Create a chart in the SignalFx API.

        See: https://developers.signalfx.com/v2/reference#create-chart
        """
        self.options = self.to_dict()
        return super(Chart, self).create(dry_run=dry_run)

    def update(self, name=None, description=None, resource_id=None, dry_run=False):
        """Update a chart in the SignalFx API.

        WARNING: Users are strongly discouraged from updating charts outside
        of a Dashboard. Due to the nature of how charts are created in the
        SignalFx API it is much more difficult to determine which is the right
        chart to update. Updating charts via dashboards is the better way to go.

        See: https://developers.signalfx.com/v2/reference#update-chart
        """

        updated_opts = dict(self.options)
        if name:
            updated_opts.update({'name': name})
        if description:
            updated_opts.update({'description': description})

        if dry_run:
            return updated_opts

        query_result = self.__find_existing_resources__()

        try:
            self.__find_existing_match__(query_result)

        except ResourceAlreadyExistsError:
            self.options = self.to_dict()
            return super(Chart, self).update(name=name, description=description, resource_id=resource_id)

        except ResourceHasMultipleExactMatchesError as e:
            if 'id' in self.options:
                self.options = self.to_dict()
                return super(Chart, self).update(name=name, description=description, resource_id=self.options['id'])
            else:
                raise e

        except ResourceMatchNotFoundError:
            return self.create(dry_run=dry_run)


class UnitPrefix(Enum):
    """Enum for unit prefix types in TimeSeriesCharts."""
    metric = "Metric"
    binary = "Binary"


class ColorBy(Enum):
    """Enum for types of coloring options in TimeSeriesCharts."""
    dimension = "Dimension"
    metric = "Metric"
    scale = "Scale"


class SortBy(Enum):
    """Enum for sorting by values in ListCharts."""
    value_desc = "-value"
    value_asc = "+value"


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


class ChartOption(object):
    """Base option class for chart options that require validation."""

    def __init__(self):
        self.opts = {}

    def to_dict(self):
        return self.opts


class AxisOption(ChartOption):
    """Encapsulation for options on chart axes."""

    def __init__(self, min, max, label, high_watermark, low_watermark):
        """Initializes this class with valid values, raises ValueError
           if any values are missing.

        Arguments:
            min: the minimum value for the axis
            max: the maximum value for the axis
            label: label of the axis
            high_watermark: a line ot draw as a high watermar
            low_watermark: a line to draw as a low watermark
        """
        for arg in [min, max, label, high_watermark, low_watermark]:
            if arg is None:
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


class FieldOption(ChartOption):
    """Field options used to display columns in a chart's table."""

    def __init__(self, property, enabled=True):
        """Initialize a field option, raise ValueError if property is not
           defined.

        Arguments:
            property: property that may be part of a MTS in the visualization
            enabled: whether the property should be displayed in the legend
        """
        if not property:
            raise ValueError('Field option cannot be blank')

        self.opts = {'property': property, 'enabled': enabled}


class PublishLabelOptions(ChartOption):
    """Options for displaying published timeseries data."""

    def __init__(self, label, y_axis, palette_index, plot_type, display_name):
        """Initializes and validates publish label options.

        Arguments:
            label: label used in the publish statement that displayes the plot
            y_axis: the y-axis associated with values for this plot.
                    Must be 0 (left) or 1 (right).
            palette_index: the indexed palette color to use for all plot lines
            plot_type: the visualization style to use
            display_name: an alternate name to show in the legend
        """
        for arg in [label, display_name]:
            util.assert_valid(arg)
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


class DisplayOptionsMixin(object):
    """A mixin for chart types that share display option builders.

    The assumption is made that all classes using this mixin have
    a member dict called 'chart_options'.
    """

    def with_color_by(self, color_by):
        """Determine how timeseries are colored in this chart."""
        util.assert_valid(color_by)
        util.in_given_enum(color_by, ColorBy)
        self.chart_options.update({'colorBy': color_by.value})
        return self

    def with_sort_by(self, sort_by):
        """Determine how values are sorted."""
        util.assert_valid(sort_by)
        util.in_given_enum(sort_by, SortBy)
        self.chart_options.update({'sortBy': sort_by.value})
        return self

    def with_unit_prefix(self, prefix):
        """Add a unit prefix to this chart."""
        util.assert_valid(prefix)
        util.in_given_enum(prefix, UnitPrefix)
        self.chart_options.update({'unitPrefix': prefix.value})
        return self

    def with_program_options(
            self, min_resolution, max_delay, disable_sampling=False):
        """How should the program underlying the visualization be run.

        Arguments:
            min_resolution: min resolution to use for computing program
            max_delay: How long to wait for late datapoints, in ms.
            disable_sampling: samples a subset of output MTS unless enabled.
                              Improves chart performance for heavier MTS.

        Consult this page for more information on min resolution:
            https://docs.signalfx.com/en/latest/reference/analytics-docs/how-choose-data-resolution.html

        Consult this page for more information on late datapoints:
            https://docs.signalfx.com/en/latest/charts/chart-options-tab.html#max-delay

        Returns:
            This TimeSeriesChart with program options.
        """

        util.assert_valid(min_resolution)
        util.assert_valid(max_delay)
        program_opts = {
            'minimumResolution': min_resolution,
            'maxDelay': max_delay,
            'disableSampling': disable_sampling
        }
        self.chart_options.update({'programOptions': program_opts})
        return self

    def with_publish_label_options(self, *publish_opts):
        """Plot-level customization, associated with a publish statement."""
        util.assert_valid(publish_opts)
        opt = list(map(lambda o: o.to_dict(), publish_opts))
        self.chart_options.update({'publishLabelOptions': opt})
        return self


class TimeSeriesChart(Chart, DisplayOptionsMixin):
    """A time series chart."""

    def __init__(self, session=None):
        super(TimeSeriesChart, self).__init__(session=session)
        self.chart_options = {'type': 'TimeSeriesChart'}

    def with_time_config_relative(self, range):
        """Options to set the relative view window into the given chart.

        Arguments:
            range: Absolute millisecond offset from now to visualize.

        Returns:
            This TimeSeriesChart with absolute time config
        """
        util.assert_valid(range)
        opts = {'type': 'relative', 'range': range}
        self.chart_options.update({'time': opts})
        return self

    def with_time_config_absolute(self, start, end):
        """Options to set the absolute view window into the given chart.

        Arguments:
            start: Milliseconds since epoch to start the visualization.
            end: Milliseconds since epoch to end the visualization.

        Returns:
            This TimeSeriesChart with a relative time config.
        """
        util.assert_valid(start)
        util.assert_valid(end)
        opts = {'type': 'absolute', 'start': start, 'end': end}
        self.chart_options.update({'time': opts})
        return self

    def with_axes(self, axes):
        """Options for labeling axes on TimeSeries charts.

        Don't leave your axes laying about or this guy might show up:
        https://youtu.be/V2FygG84bg8
        """
        util.assert_valid(axes)
        self.chart_options.update({
            'axes': list(map(lambda x: x.to_dict(), axes))
        })
        return self

    def with_legend_options(self, field_opts):
        """Options for the behavior of this chart's legend."""
        util.assert_valid(field_opts)
        opts = {'fields': list(map(lambda x: x.to_dict(), field_opts))}
        self.chart_options.update({'legendOptions': opts})
        return self

    def show_event_lines(self, boolean):
        """Whether vertical highlight lines should be drawn in the
           visualizations at times when events occurred.
        """
        self.chart_options.update({'showEventLines': str(boolean).lower()})
        return self

    def __has_opt(self, opt_name):
        """Identify if the given option exists in this TimeSeriesChart."""
        return self.chart_options.get(opt_name, None) is not None

    def __with_chart_options(self, clazz, show_data_markers=False):
        """Internal helper validating line/area plot options.

        Arguments:
            clazz: the type of plot to set options for
            show_data_markers: whether or not to show data markers in the chart

        Returns:
            This TimeSeriesChart with line/area plot options set.

        Raises:
            ValueError: a line/area option was set on the wrong plot type
        """
        plot_type = self.chart_options.get('defaultPlotType', '')
        if plot_type.lower() not in clazz.lower():
            msg = "Attempted to define '{0}' but chart is of type '{1}'"
            raise ValueError(msg.format(clazz, plot_type))

        opts = {'showDataMarkers': show_data_markers}
        self.chart_options.update({clazz: opts})
        return self

    def with_line_chart_options(self, show_data_markers=False):
        """Modify options on line plot types."""
        return self.__with_chart_options('lineChartOptions', show_data_markers)

    def with_area_chart_options(self, show_data_markers=False):
        """Modify options on line plot types."""
        return self.__with_chart_options('areaChartOptions', show_data_markers)

    def stack_chart(self, boolean):
        """Should area/bar charts in the visualization be stacked."""
        self.chart_options.update({'stacked': str(boolean).lower()})
        return self

    def with_default_plot_type(self, plot_type):
        """The default plot display style for the visualization."""
        util.assert_valid(plot_type)
        util.in_given_enum(plot_type, PlotType)
        self.chart_options.update({'defaultPlotType': plot_type.value})
        return self

    def with_axis_precision(self, num):
        """Force a specific number of significant digits in the y-axis."""
        util.assert_valid(num)
        self.chart_options.update({'axisPrecision': num})
        return self

    def with_chart_legend_options(self, dimension, show_legend=False):
        """Show the on-chart legend using the given dimension."""
        util.assert_valid(dimension)
        opts = {
            'showLegend': show_legend,
            'dimensionInLegend': dimension
        }
        self.chart_options.update({'onChartLegendOptions': opts})
        return self


class SingleValueChart(Chart, DisplayOptionsMixin):

    def __init__(self, session=None):
        super(SingleValueChart, self).__init__(session=session)
        self.chart_options = {'type': 'SingleValue'}

    def with_refresh_interval(self, interval):
        """How often (in milliseconds) to refresh the values of the list."""
        util.assert_valid(interval)
        self.chart_options.update({'refreshInterval': interval})
        return self

    def with_maximum_precision(self, precision):
        """The maximum precision to for values displayed in the list."""
        util.assert_valid(precision)
        self.chart_options.update({'maximumPrecision': precision})
        return self

    def with_timestamp_hidden(self, hidden=False):
        """Whether to hide the timestamp in the chart."""
        self.chart_options.update({'timestampHidden': hidden})
        return self

    def with_sparkline_hidden(self, hidden=True):
        """Whether to show a trend line below the current value."""
        self.chart_options.update({'showSparkLine': hidden})
        return self

    def with_colorscale(self, thresholds, inverted=False):
        """Values for each color in the range.

        Arguments:
            thresholds: The thresholds to set for the color range being used.
            inverted: If false, values are red if they are above
                      the highest specified value. If true, values are red if
                      they are below the lowest specified value.
        """
        util.assert_valid(thresholds)
        thresholds.sort(reverse=True)
        opts = {'thresholds': thresholds, 'inverted': inverted}
        self.chart_options.update({'colorScale': opts})
        return self


class ListChart(Chart, DisplayOptionsMixin):

    def __init__(self, session=None):
        super(ListChart, self).__init__(session=session)
        self.chart_options = {'type': 'List'}

    def with_refresh_interval(self, interval):
        """How often (in milliseconds) to refresh the values of the list."""
        util.assert_valid(interval)
        self.chart_options.update({'refreshInterval': interval})
        return self

    def with_maximum_precision(self, precision):
        """The maximum precision to for values displayed in the list."""
        util.assert_valid(precision)
        self.chart_options.update({'maximumPrecision': precision})
        return self


class HeatmapChart(Chart, DisplayOptionsMixin):

    def __init__(self, session=None):
        super(HeatmapChart, self).__init__(session=session)
        self.chart_options = {'type': 'Heatmap'}

    def with_colorscale(self, thresholds):
        """Values for each color in the range.

        Arguments:
            thresholds: The thresholds to set for the color range being used.
        """
        util.assert_valid(thresholds)
        thresholds.sort(reverse=True)
        opts = {'thresholds': thresholds}
        self.chart_options.update({'colorScale': opts})
        return self
