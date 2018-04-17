import signal_analog.util as util


class FilterVariable(object):
    """
    A set of predefined filters that are available by default at the top of the dashboard.
    The properties of the included objects are indicated as filters.variables[x].propertyName.
    This notation means the propertyName property is part of the object in each element of the variables array.
    """

    def __init__(self):
        self.options = {}

    def with_alias(self, alias):
        util.assert_valid(alias, error_message='"alias" cannot be empty', expected_type=str)
        self.options.update({'alias': alias})
        return self

    def with_apply_if_exists(self, apply_if_exists):
        util.assert_valid(apply_if_exists, expected_type=bool)
        self.options.update({'apply_if_exists': apply_if_exists})
        return self

    def with_description(self, description):
        self.options.update({'description': description})
        return self

    def with_preferred_suggestions(self, *preferred_suggestions):
        self.options.update({'preferredSuggestions': []})
        for preferred_suggestion in preferred_suggestions:
            self.options['preferredSuggestions'].append(preferred_suggestion)
        return self

    def with_property(self, property):
        util.assert_valid(property, error_message='"property" cannot be empty', expected_type=str)
        self.options.update({'property': property})
        return self

    def with_replace_only(self, replace_only):
        util.assert_valid(replace_only, expected_type=bool)
        self.options.update({'replaceOnly': replace_only})
        return self

    def with_is_required(self, required):
        util.assert_valid(required, expected_type=bool)
        self.options.update({'required': required})
        return self

    def with_is_restricted(self, restricted):
        util.assert_valid(restricted, expected_type=bool)
        self.options.update({'restricted': restricted})
        return self

    def with_value(self, *values):
        self.options.update({'value': []})
        for value in values:
            self.options['value'].append(value)
        return self


class FilterSource(object):
    """
    Each element represents an adhoc filter to apply to the charts within the dashboard. Each filter can key off of one
    dimension or custom property (either user defined or supplied by default) and can either include or exclude all data
    matching the supplied criteria. The properties of the included objects are indicated as
    filters.sources[x].propertyName; this notation means the propertyName property is part of the object in each element
    of the sources array.
    """

    def __init__(self):
        self.options = {}

    def with_property(self, property):
        util.assert_valid(property, error_message='"property" cannot be empty', expected_type=str)
        self.options.update({'property': property})
        return self

    def with_value(self, *values):
        util.assert_valid(*values, error_message='"value" cannot be empty')
        self.options.update({'value': []})
        for value in values:
            self.options['value'].append(value)
        return self

    def with_is_not(self, is_not):
        util.assert_valid(is_not, expected_type=bool, error_message='"NOT" cannot be empty. It should be a boolean')
        self.options.update({'NOT': is_not})
        return self


class FilterTime(object):
    """
    The properties of the included objects are indicated as filters.time.propertyName.
    """

    def __init__(self):
        self.options = {}

    def with_start(self, start):
        util.assert_valid(start, error_message='"start" cannot be empty')
        self.options.update({'start': start})
        return self

    def with_end(self, end):
        util.assert_valid(end, error_message='"end" cannot be empty')
        self.options.update({'end': end})
        return self


class DashboardFilters(object):
    """
    A filters model to be attached to a dashboard. Filters allow fine grained control over the data displayed
    in the charts within the dashboard. They can be adhoc or saved as variables to allow easy reuse of filter criteria.
    Filters can also be used to apply a custom time window to all of the charts in the dashboard.
    The properties of the included object are indicated as filters.propertyName.
    """

    def __init__(self):
        """Initialize filters object"""
        self.options = {}

    def with_variables(self, *variables):
        self.options.update({'variables': []})
        for variable in variables:
            if 'alias' not in variable.options and 'property' not in variable.options:
                raise ValueError('"alias" and "property" are required parameters')
            elif 'alias' not in variable.options:
                raise ValueError('"alias" is a required parameter')
            elif 'property' not in variable.options:
                raise ValueError('"property" is a required parameter')
            self.options['variables'].append(variable.options)
        return self

    def with_sources(self, *sources):
        self.options.update({'sources': []})
        for source in sources:
            if 'value' not in source.options and 'property' not in source.options:
                raise ValueError('"property" and "value" are required parameters')
            elif 'property' not in source.options:
                raise ValueError('"property" is a required parameter')
            elif 'value' not in source.options:
                raise ValueError('"value" is a required parameter')
            self.options['sources'].append(source.options)
        return self

    def with_time(self, time):
        # Checking if either start or end time is defined
        if bool(time.options):
            """
            All the code below evaluates the following conditions and throws an error if any of them are not met

            filters.time.start-->	Type: 
                                        string or integer	
                                    Must be an integer if filters.time.end is an integer
                                    Must be a string if filters.time.end is a string
                                    If integer:
                                        Minimum value = 0
                                        Value must be smaller than value of filters.time.end
                                    If string:
                                        Value must start with a negative sign
                                        A positive integer must follow the negative sign
                                        Value must end with a units indicator. Allowed units indicators are m, h, d, w 
                                        representing minutes, hours, days, and weeks respectively

            filters.time.end-->	    Type:
                                        enumerated string or integer	
                                    Must be an integer if filters.time.start is an integer
                                    Must be a string if filters.time.start is a string
                                    If integer:
                                        Minimum value = 0
                                        Value must be larger than value of filters.time.start
                                    If string:
                                        Allowed value is "Now"

            """
            if 'start' in time.options and 'end' not in time.options:
                raise ValueError("End time should be provided")
            elif 'end' in time.options and 'start' not in time.options:
                raise ValueError("Start time should be provided")
            elif not isinstance(time.options['start'], type(time.options['end'])):
                raise ValueError("Start and End times should be of the same data type."
                                 "Instead, got Start time as {0} and End time as {1}"
                                 .format(type(time.options['start']), type(time.options['end'])))
            else:
                st = time.options['start']
                et = time.options['end']
                st_type = type(st)

                # We have to validate bool separately as it is a subclass of int
                if not isinstance(st, (str, int)) or isinstance(st, bool):
                    raise ValueError("Start and End times must be either a String or an Integer. "
                                     "Instead, got a {0}".format(st_type))
                elif isinstance(st, str):
                    if st[:1] is not "-":
                        raise ValueError("Start time value must start with a negative sign")
                    elif st[-1:] not in ['m', 'h', 'd', 'w']:
                        raise ValueError(
                            "Start time value must end with a units indicator. Allowed units indicators are "
                            "m, h, d, w(case-sensitive) representing minutes, hours, days, and weeks respectively. "
                            "Instead, got '{0}'".format(st[-1:]))
                    else:
                        try:
                            val = int(st[1:-1])
                            if val < 0:
                                raise ValueError("A positive integer must follow the negative sign for Start time. "
                                                 "Instead, got '{0}'".format(st[1:-1]))
                        except ValueError:
                            raise ValueError("A positive integer must follow the negative sign for Start time. "
                                             "Instead, got '{0}'".format(st[1:-1]))
                    if et != "Now":
                        raise ValueError('End time value should be "Now"(case-sensitive) when Start time '
                                         'is defined as a string. Instead, got "{0}"'.format(et))
                elif isinstance(st, int):
                    if st < 0 and et < 0:
                        raise ValueError("Start time and End time cannot be Negative values")
                    elif st < 0:
                        raise ValueError("Start time cannot be a Negative value")
                    elif et < 0:
                        raise ValueError("End time cannot be a Negative value")
                    elif st > et:
                        raise ValueError("Start time should be smaller than End time")

            self.options.update({'time': time.options})
            return self
        else:
            raise ValueError("Start and End time are required")

