#!/usr/bin/env python

"""Examples for the `signal_analog.filters` module."""

from signal_analog.flow import Data
from signal_analog.charts import TimeSeriesChart
from signal_analog.dashboards import Dashboard
from signal_analog.eventoverlays import EventSignals, EventOverlays, SelectedEventOverlays

"""
Example 1: Creating a new Dashboard with event overlay markers set to show by default

This creates a new dashboard which will show event markers marked with "deploy" by default.
"""
program = Data('cpu.utilization').publish()
chart = TimeSeriesChart().with_name('Chart_Name').with_program(program)

events = EventSignals().with_event_search_text("test")\
    .with_event_type("eventTimeSeries")\
    .to_dict()

eventoverlay = EventOverlays().with_event_signals(events)\
    .with_event_color_index(2)\
    .with_event_line(True)\
    .to_dict()

selectedeventoverlay = SelectedEventOverlays().with_event_signals(events)\
    .to_dict()

dashboard_with_event_overlays = Dashboard().with_name('Dashboard Named George')\
    .with_charts(chart)\
    .with_event_overlay(eventoverlay)\
    .with_selected_event_overlay(selectedeventoverlay)

if __name__ == '__main__':
    from signal_analog.cli import CliBuilder
    cli = CliBuilder().with_resources(dashboard_with_event_overlays)\
        .build()
    cli()
