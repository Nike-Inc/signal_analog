#!/usr/bin/env python

"""Examples for the `signal_analog.eventoverlays` module."""

from signal_analog.flow import Data
from signal_analog.charts import TimeSeriesChart
from signal_analog.dashboards import Dashboard
from signal_analog.eventoverlays import EventSignals, EventOverlays, SelectedEventOverlays

"""
Example 1: Creating a new Dashboard with event overlay markers set to show by default

This creates a new dashboard which will show event markers marked with "deploy" by default.
"""
program = Data('cpu.utilization').publish()
chart = TimeSeriesChart().with_name('TacoChart').with_program(program).show_event_lines(True)

events = EventSignals().with_event_search_text("deploy")\
    .with_event_type("eventTimeSeries")

eventoverlay = EventOverlays().with_event_signals(events)\
    .with_event_color_index(1)\
    .with_event_line(True)

selectedeventoverlay = SelectedEventOverlays()\
    .with_event_signals(events)

dashboard_with_event_overlays = Dashboard().with_name('Dashboard Named Snek')\
    .with_charts(chart)\
    .with_event_overlay(eventoverlay)\
    .with_selected_event_overlay(selectedeventoverlay)

if __name__ == '__main__':
    from signal_analog.cli import CliBuilder
    cli = CliBuilder().with_resources(dashboard_with_event_overlays)\
        .build()
    cli()
