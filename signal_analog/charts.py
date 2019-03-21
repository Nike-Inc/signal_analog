"""Chart objects representable in the SignalFX API."""

from copy import deepcopy
from enum import Enum
from six import string_types

import signal_analog.util as util
from signal_analog.errors import ResourceMatchNotFoundError, \
    ResourceHasMultipleExactMatchesError, ResourceAlreadyExistsError
from signal_analog.resources import Resource
from signal_analog.flow import Program

from signal_analog import __version__

import deprecation


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

        Arguments:
            id: String identifying chart

        Useful when updating/deleting charts.
        """
        util.assert_valid(id)
        self.options.update({'id': id})
        return self

    def with_program(self, program):
        """The SignalFlow program to execute for this chart.

        See 'Program' class.

        Example:

        >>> Program(
        >>>     Plot(
        >>>         assigned_name="A",
        >>>         signal_name="ConsumedReadCapacityUnits",
        >>>         filter=And(
        >>>             Filter("TableName", table_name),
        >>>             Filter("stat", "sum")
        >>>         ),
        >>>         rollup=RollupType.sum,
        >>>         fx=[Sum(by=["TableName", "aws_account_id"])],
        >>>         label="ConsumedReadCapacity"
        >>>     ),
        >>>     Plot(
        >>>         assigned_name="B",
        >>>         signal_name="ConsumedWriteCapacityUnits",
        >>>         filter=And(
        >>>             Filter("TableName", table_name),
        >>>             Filter("stat", "sum")
        >>>         ),
        >>>         rollup=RollupType.sum,
        >>>         fx=[Sum(by=["TableName", "aws_account_id"])],
        >>>         label="ConsumedWriteCapacity"
        >>>     )
        >>> )

        Arguments:
            program: Valid json defining a program

        For more information SignalFlow consult the `signal_analog.flow`
        module or the upstream SignalFlow documentation here:

        https://developers.signalfx.com/docs/signalflow-overview
        """
        util.assert_valid(program)
        # Chart's don't require you to use a Program object, so make a best
        # effort to validate if we can.
        if isinstance(program, Program):
            program.validate()

        self.options.update({'programText': program})
        return self

    def to_dict(self):
        """Creates a dict of entire chart.

        """
        curr_chart_opts = deepcopy(self.options.get('options', {}))
        curr_chart_opts.update(self.chart_options)

        chart_opts_copy = deepcopy(self.options)
        chart_opts_copy.update({
            'options': curr_chart_opts
        })

        # TextCharts don't have programText
        if 'programText' in chart_opts_copy:
            chart_opts_copy.update({
                'programText': str(chart_opts_copy['programText'])
            })

        return chart_opts_copy

    def create(self, dry_run=False):
        """Create a chart in the SignalFx API.

        Arguments:
            dry_run: Boolean to determine if this invocation will be a dry run

        See: https://developers.signalfx.com/v2/reference#create-chart
        """
        self.options = self.to_dict()
        return super(Chart, self).create(dry_run=dry_run)

    def update(self, name=None, description=None, resource_id=None, dry_run=False):
        """Update a chart in the SignalFx API.

        Arguments:
            name: String defining chart name
            description: String defining chart description
            resource_id: String defining the chart resource id in signalfx
            dry_run: Boolean to determine if this invocation will be a dry run

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
        """Return a dict of ChartOptions
        """
        return self.opts


class AxisOption(ChartOption):
    """Encapsulation for options on chart axes."""

    def __init__(self, min=None, max=None, label="", high_watermark=None, low_watermark=None):
        """Initialize this class with valid values, raises ValueError
           if any values are missing.

        Arguments:
            min: the minimum value for the axis
            max: the maximum value for the axis
            label: label of the axis
            high_watermark: a line ot draw as a high watermark
            low_watermark: a line to draw as a low watermark
        """

        if min is not None and max is not None and max < min:
            msg = "min cannot be less than max in axis with label {0}"
            raise ValueError(msg.format(label))

        self.opts = {
            'min': min,
            'max': max,
            'label': label,
            'lowWatermark': low_watermark,
            'highWatermark': high_watermark
        }


class SignalFxFieldOption(Enum):
    """Common SignalFx field options intended to be combined with FieldOption.

    When using these values via the API it's non-obvious how you would filter
    them out of your charts. Using 'Plot Name' in your FieldOption would not
    hide 'Plot Name' in the UI, you would use 'sf_originatingMetric' instead.
    This enum is intended to make the behavior of the UI consistent with the
    UI.

    Values:
        metric: the 'sf_metric' field option.
        plot_name: the 'Plot Name' field option.
    """
    metric = 'sf_metric'
    plot_name = 'sf_originatingMetric'


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

        if isinstance(property, SignalFxFieldOption):
            # <insert home buying joke here>
            value = property.value
        elif isinstance(property, string_types):
            value = property
        else:
            msg = 'FieldOption property should be a string or' +\
                  'SignalFxFieldOption, got "{0}" instead.'
            raise ValueError(msg.format(property))

        self.opts = {'property': value, 'enabled': enabled}


class PublishLabelOptions(ChartOption):
    """Options for displaying published timeseries data.

    These options are applied at the individual plot level (vs. the chart level).

    Also see method 'with_publish_label_options()'
    """

    def __init__(self, label, y_axis=None, palette_index=None, plot_type=None,
                 display_name=None, value_prefix=None, value_suffix=None,
                 value_unit=None):
        """Initializes and validates publish label options.

        These options are applied at the individual plot level (vs. the chart level).

        Also see method 'with_publish_label_options()'

        Arguments:
            label: label used in the publish statement that displays the plot.
                    If you defined your plot with the 'Plot' class this should be
                    the same as the 'label' in that class.  Otherwise it should be
                    the same label used in 'Function.publish(label)'
            y_axis: the y-axis associated with values for this plot.
                    Must be 0 (left) or 1 (right).
            palette_index: the indexed palette color to use for all plot lines,
                    e.g. PaletteColor.green
            plot_type: the visualization style to use, e.g. PlotType.area_chart.
                    This value overrides the value defined in the 'TimeSeriesChart'
                    for a single plot.
                    Also see 'TimeSeriesChart.with_default_plot_type()'.
            display_name: an alternate name to show in the legend
            value_prefix: Indicates a string to prepend to the values displayed
                          when you are viewing a single value or list chart,
                          the data table for a chart, and the tooltip when
                          hovering over a point on a chart.
            value_suffix: Indicates a string to append to the values displayed
                          when you are viewing a single value or list chart,
                          the data table for a chart, and the tooltip when
                          hovering over a point on a chart.
            value_unit: Indicates display units for the values in the chart.
                        The plot values will be presented in a readable way
                        based on the assumption that the raw values are
                        denominated in the selected unit. E.g. 60,000 milliseconds
                        will be displayed 1 minute in the chart. Example values
                        include 'Millisecond', 'Nanosecond', 'Byte', 'Kibibyte',
                        'Bit', 'Kilobit', 'Megabit', etc. (as seen in the SignalFx UI)
        """

        util.assert_valid(label)
        self.opts = {
            'label': label
        }

        if y_axis and y_axis not in [0, 1]:
            msg = "YAxis for chart must be 0 (Left) or 1 (Right); " +\
                    "'{0}' provided."
            raise ValueError(msg.format(y_axis))
        else:
            self.opts.update({'yAxis': y_axis})

        # A little ditty to translate optional simple parameters into a map
        # of camelCased keys to values
        for elem in ['display_name', 'value_prefix', 'value_suffix',
                     'value_unit']:
            for key, value in locals().items():
                if key is elem and value:
                    self.opts.update({util.snake_to_camel(key): value})

        if palette_index:
            util.in_given_enum(palette_index, PaletteColor)
            self.opts.update({'paletteIndex': palette_index.value})

        if plot_type:
            util.in_given_enum(plot_type, PlotType)
            self.opts.update({'plotType': plot_type.value})


class DisplayOptionsMixin(object):
    """A mixin for chart types that share display option builders.

    The assumption is made that all classes using this mixin have
    a member dict called 'chart_options'.
    """

    def with_color_by(self, color_by):
        """Determine how timeseries are colored in this chart.

        Arguments:
            color_by: String that defines how to color a chart (dimension, metric, scale)
        """
        util.assert_valid(color_by)
        util.in_given_enum(color_by, ColorBy)
        self.chart_options.update({'colorBy': color_by.value})
        return self

    def with_sort_by(self, sort_by):
        """Determine how values are sorted.

        Arguments:
            sort_by: String that defines how we sort values (-value, +value)
        """
        util.assert_valid(sort_by)
        util.in_given_enum(sort_by, SortBy)
        self.chart_options.update({'sortBy': sort_by.value})
        return self

    def with_unit_prefix(self, prefix):
        """Add a unit prefix to this chart.

        Arguments:
            prefix: String defining unit prefix (metric, binary)
        """
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
        """Plot-level customization, associated with a publish statement.

        See 'PublishLabelOptions' class.

        Example:

        >>> TimeSeriesChart().with_publish_label_options(PublishLabelOptions(
        >>>     label='Latency',
        >>>     palette_index=PaletteColor.gray,
        >>>     value_unit='Millisecond'
        >>> ))

        Arguments:
            *publish_opts: Non-keyworded List containing published label options
        """
        util.assert_valid(publish_opts)
        opt = list(map(lambda o: o.to_dict(), publish_opts))
        self.chart_options.update({'publishLabelOptions': opt})
        return self


class LegendOptionsMixin(object):
    """A mixin for chart types that share legend options setting.

    The assumption is made that all classes using this mixin have
    a member dict called 'chart_options'.

    Example:

    >>> TimeSeriesChart().with_chart_legend_options("sf_metric", show_legend=True)

    """

    def with_legend_options(self, field_opts):
        """Options for the behavior of this chart's legend."""
        util.assert_valid(field_opts)
        opts = {'fields': list(map(lambda x: x.to_dict(), field_opts))}
        self.chart_options.update({'legendOptions': opts})
        return self


class TimeSeriesChart(Chart, DisplayOptionsMixin, LegendOptionsMixin):
    """A time series chart."""

    def __init__(self, session=None):
        super(TimeSeriesChart, self).__init__(session=session)
        self.chart_options = {'type': 'TimeSeriesChart'}

    def with_time_config_relative(self, range):
        """Options to set the relative view window into the given chart.

        Arguments:
            range: Int absolute millisecond offset from now to visualize.

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

        Arguments:
            axes: List of objects to configure axis identifiers

        See AxisOption class.

        Y axis configuration for the left and right side of a chart.
        The first element of the array corresponds to the left side of the chart
        and the second element of the array corresponds to the right side of the array.
        Don't leave your axes laying about or this guy might show up:
        https://youtu.be/Ln71u1nu6L4
        """
        util.assert_valid(axes, expected_type=list)
        self.chart_options.update({
            'axes': list(map(lambda x: x.to_dict(), axes))
        })
        return self

    def show_event_lines(self, boolean):
        """Whether vertical highlight lines should be drawn in the
           visualizations at times when events occurred.

           Arguments:
                boolean: Boolean defining if event lines will be shown on the chart
        """
        self.chart_options.update({'showEventLines': str(boolean).lower()})
        return self

    def __has_opt(self, opt_name):
        """Identify if the given option exists in this TimeSeriesChart.

            Arguments:
                opt_name: object defining a chart option to check for
        """
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
        """Modify options on line plot types.

            Arguments:
                show_data_markers: Boolean to turn data markers on and off in line charts
        """
        return self.__with_chart_options('lineChartOptions', show_data_markers)

    def with_area_chart_options(self, show_data_markers=False):
        """Modify options on line plot types.

            Arguments:
                show_data_markers: Boolean to turn data markers on and off in area charts
        """
        return self.__with_chart_options('areaChartOptions', show_data_markers)

    def stack_chart(self, boolean):
        """Should area/bar charts in the visualization be stacked.

            Arguments:
                boolean: Boolean to turn on/off chart stacking
        """
        self.chart_options.update({'stacked': boolean})
        return self

    def with_default_plot_type(self, plot_type):
        """The default plot display style for the visualization.

            Arguments:
                plot_type: Enumerated string to define default plot type in TimeSeriesChart
        """
        util.assert_valid(plot_type)
        util.in_given_enum(plot_type, PlotType)
        self.chart_options.update({'defaultPlotType': plot_type.value})
        return self

    def with_axis_precision(self, num):
        """Force a specific number of significant digits in the y-axis.

            Arguments:
                num: Int
        """
        util.assert_valid(num)
        self.chart_options.update({'axisPrecision': num})
        return self

    def with_chart_legend_options(self, dimension, show_legend=False):
        """Show the on-chart legend using the given dimension.

            Arguments:
                dimension: Object defining dimension to show on legend
                show_legend: Boolean to turn legend on/off
        """
        util.assert_valid(dimension)
        opts = {
            'showLegend': show_legend,
            'dimensionInLegend': dimension
        }
        self.chart_options.update({'onChartLegendOptions': opts})
        return self

    def with_include_zero(self, include_zero=False):
        self.chart_options.update({'includeZero': include_zero})
        return self


class SingleValueChart(Chart, DisplayOptionsMixin):

    def __init__(self, session=None):
        super(SingleValueChart, self).__init__(session=session)
        self.chart_options = {'type': 'SingleValue'}

    def with_refresh_interval(self, interval):
        """How often (in milliseconds) to refresh the values of the list.

            Arguments:
                interval: Int
        """
        util.assert_valid(interval)
        self.chart_options.update({'refreshInterval': interval})
        return self

    def with_maximum_precision(self, precision):
        """The maximum precision to for values displayed in the list.

            Arguments:
                precision: Int

            Indicates the number of significant digits included for values plotted on a chart but only applies to
            fractional portions of the number.
            For example, if the values of the represented data typically fluctuates between 0.001 and 0.01,
            significant information will be lost unless the precision is set to at least 4.
        """
        util.assert_valid(precision)
        self.chart_options.update({'maximumPrecision': precision})
        return self

    def with_timestamp_hidden(self, hidden=False):
        """Whether to hide the timestamp in the chart.

            Arguments:
                hidden: Boolean
        """
        self.chart_options.update({'timestampHidden': hidden})
        return self

    @deprecation.deprecated(deprecated_in="2.2.0", removed_in="3.0",
                            current_version=__version__,
                            details="Use the with_secondary_visualization function instead")
    def with_sparkline_hidden(self, hidden=True):
        """Whether to show a trend line below the current value.

            Arguments:
                hidden: Boolean
        """
        self.chart_options.update({'showSparkLine': hidden})
        return self

    def with_secondary_visualization(self, visualization=None):
        """Whether to show a trend line below the current value.

            Arguments:
                visualization: Enumerated string equal to None, Radial, Linear, Sparkline
        """
        if visualization not in [None, "Radial", "Linear", "Sparkline"]:
            msg = "Secondary visualization for chart must be either None, Radial, Linear, or Sparkline"
            raise ValueError(msg.format(visualization))
        else:
            self.chart_options.update({'secondaryVisualization': visualization})
        return self

    def with_colorscale(self, thresholds, inverted=False):
        """Values for each color in the range.

        Arguments:
            thresholds: The thresholds to set for the color range being used.
            inverted: Boolean If false, values are red if they are above
                      the highest specified value. If true, values are red if
                      they are below the lowest specified value.
        """
        util.assert_valid(thresholds)
        thresholds.sort(reverse=True)
        opts = {'thresholds': thresholds, 'inverted': inverted}
        self.chart_options.update({'colorScale': opts})
        return self


class ListChart(Chart, DisplayOptionsMixin, LegendOptionsMixin):

    def __init__(self, session=None):
        super(ListChart, self).__init__(session=session)
        self.chart_options = {'type': 'List'}

    def with_refresh_interval(self, interval):
        """How often (in milliseconds) to refresh the values of the list.

            Arguments:
                interval: Int
        """
        util.assert_valid(interval)
        self.chart_options.update({'refreshInterval': interval})
        return self

    def with_maximum_precision(self, precision):
        """The maximum precision to for values displayed in the list.

            Arguments:
                precision: Int
        """
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


class TextChart(Chart, DisplayOptionsMixin):

    def __init__(self, session=None):
        super(TextChart, self).__init__(session=session)
        self.chart_options = {'type': 'Text'}

    def with_markdown(self, markdown):
        """The markdown text that needs to be displayed"""
        util.check_markdown(markdown, error_message='"text" cannot be empty. ')
        self.chart_options.update({'markdown': markdown})
        return self
