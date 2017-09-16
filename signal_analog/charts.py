from signal_analog.resources import Resource


class Chart(Resource):

    def __init__(self):
        """Base representation of a chart in SignalFx."""
        super(Chart, self).__init__(endpoint='/chart')
        self.options = {}

    def with_name(self, name):
        self.is_valid(name)
        self.options.update({'name': name})
        return self

    def with_description(self, description):
        self.is_valid(description)
        self.options.update({'description': description})
        return self

    def with_program(self, program):
        self.is_valid(program)
        self.options.update({'programText': str(program)})
        return self


class TimeSeriesChart(Chart):

    def __init__(self):
        """A time series chart."""
        super(TimeSeriesChart, self).__init__()
        self.chart_options = {'type': 'TimeSeriesChart'}

    def with_default_plot_type(self, plot_type):
        self.is_valid(plot_type)
        self.chart_options.update({'defaultPlotType': plot_type})
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
