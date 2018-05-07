import pytest
from signal_analog.eventoverlays import *


@pytest.mark.parametrize("value", [None, ""])
def test_event_signal_with_empties(value):
    with pytest.raises(ValueError):
        EventSignals().with_event_search_text(value)
    with pytest.raises(ValueError):
        EventSignals().with_event_type(value)


@pytest.mark.parametrize("value", [None, ""])
def test_events_overlay_with_empties(value):
    with pytest.raises(ValueError):
        EventOverlays().with_event_color_index(value)
    with pytest.raises(ValueError):
        EventOverlays().with_event_line(value)
    with pytest.raises(ValueError):
        EventOverlays().with_event_signals(value)


@pytest.mark.parametrize("value", [None, ""])
def test_selected_events_overlay_with_empties(value):
    with pytest.raises(ValueError):
        SelectedEventOverlays().with_event_signals(value)


def test_event_with_valid_color_index():
    event_color_index = 1
    eventcolor = EventOverlays().with_event_color_index(event_color_index)
    assert eventcolor.opts['eventColorIndex'] == event_color_index


def test_event_with_color_index_out_of_range():
    event_color_index = 42
    with pytest.raises(ValueError):
        EventOverlays().with_event_color_index(event_color_index)


def test_event_with_event_line():
    expected = True
    event = EventOverlays().with_event_line(expected)
    assert event.opts['eventLine'] == expected


def test_event_with_invalid_event_line():
    expected = "Grizzly Tuna"
    with pytest.raises(ValueError):
        EventOverlays().with_event_line(expected)


def test_event_signal_with_event_search_text():
    expected = 'Taco Snek vs Snaco Tek'
    event = EventSignals().with_event_search_text(expected)
    assert event.options['eventSearchText'] == expected


def test_event_signal_with_invalid_event_search_text():
    expected = 555
    with pytest.raises(ValueError):
        EventSignals().with_event_search_text(expected)


def test_event_signal_with_event_type():
    expected = 'eventTimeSeries'
    event = EventSignals().with_event_type(expected)
    assert event.options['eventType'] == expected


def test_event_signal_with_invalid_event_type():
    expected = 'Caution! Do not step on danger noodle!'
    with pytest.raises(ValueError):
        EventSignals().with_event_type(expected)
