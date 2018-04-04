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
        util.is_valid(alias, error_message='"alias" cannot be empty', expected_type=str)
        self.options.update({'alias': alias})
        return self

    def with_apply_if_exists(self, apply_if_exists):
        util.is_valid(apply_if_exists, expected_type=bool)
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
        util.is_valid(property, error_message='"property" cannot be empty', expected_type=str)
        self.options.update({'property': property})
        return self

    def with_replace_only(self, replace_only):
        util.is_valid(replace_only, expected_type=bool)
        self.options.update({'replaceOnly': replace_only})
        return self

    def with_is_required(self, required):
        util.is_valid(required, expected_type=bool)
        self.options.update({'required': required})
        return self

    def with_is_restricted(self, restricted):
        util.is_valid(restricted, expected_type=bool)
        self.options.update({'restricted': restricted})
        return self

    def with_value(self, *values):
        self.options.update({'value': []})
        for value in values:
            self.options['value'].append(value)
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
