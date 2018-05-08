"""Event objects representable in the SignalFX API."""

import signal_analog.util as util


class EventSignals(object):
    """
    A set of variables for defining event signals
    """

    def __init__(self):
        self.options = {}

    def to_dict(self):
        return self.options

    def with_event_search_text(self, event_search_text):
        util.assert_valid(event_search_text, error_message='"event_search_text" cannot be empty. Expects a string.', expected_type=str)
        self.options.update({'eventSearchText': event_search_text})
        return self

    def with_event_type(self, event_type):
        util.assert_valid(event_type, error_message='"event_type" cannot be empty. '
                                                    'Supported values are: "detectorEvent" and "eventTimeSeries"',
                          expected_type=str)
        if event_type not in ('eventTimeSeries', 'detectorEvent'):
            raise ValueError('"event_type" expects either "detectorEvent" or "eventTimeSeries"')
        self.options.update({'eventType': event_type})
        return self


class EventOverlays(object):
    """Options for displaying event overlays chosen from drop down and determining which color they will use,
        and if they will show an event line."""
    def __init__(self):
        self.opts = {}

    def to_dict(self):
        return self.opts

    def with_event_signals(self, eventsignals):
        util.assert_valid(eventsignals, error_message='"eventsignals" cannot be empty. '
                                                    'expects EventSignals()',
                          expected_type=object)
        ev = eventsignals.to_dict()
        self.opts.update({'eventSignal': ev})
        return self

    def with_event_color_index(self, event_color_index):
        """Expects an integer from 0-20 to define event color"""
        util.assert_valid(event_color_index, error_message='"event_color_index" expects an int between 0-20',
                          expected_type=int)
        if event_color_index > 20:
            msg = "event_color_index expects an int between 0-20."
            raise ValueError(msg.format(event_color_index))

        self.opts.update({'eventColorIndex': event_color_index})
        return self

    def with_event_line(self, event_line):
        """Expects a boolean as input"""
        util.assert_valid(event_line, expected_type=bool)
        self.opts.update({'eventLine': event_line})
        return self


class SelectedEventOverlays(object):
    """Options for displaying selected event overlays by default. Event overlay settings will be used to determine
        their color and if they will show an event line."""
    def __init__(self):
        self.opts = {}

    def to_dict(self):
        return self.opts

    def with_event_signals(self, eventsignals):
        util.assert_valid(eventsignals, error_message='"eventsignals" cannot be empty. '
                                                    'expects EventSignals()',
                          expected_type=object)
        ev = eventsignals.to_dict()
        self.opts.update({'eventSignal': ev})
        return self
