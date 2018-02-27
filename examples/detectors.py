#!/usr/bin/env python

"""Examples for the `signal_analog.detectors` module.
"""

from signal_analog.charts import TimeSeriesChart
from signal_analog.detectors import Detector, Rule, EmailNotification, Severity
from signal_analog.flow import Data, Detect, Filter, Program
from signal_analog.combinators import And, LT

"""
Example 1: from scratch

This is useful when you want to monitor something that isn't tied to an
existing chart or dashboard.
"""

alert_label = 'CPU is too low!'

filters = And(Filter('app', 'shoeadmin'), Filter('env', 'test'))
data = Data('cpu.utilization', filter=filters).publish(label='A')
cpu_too_low = Detect(LT(data, 50)).publish(alert_label)
program = Program(cpu_too_low)

info_rule = Rule()\
    .for_label(alert_label)\
    .with_severity(Severity.Info)\
    .with_notifications(EmailNotification('fernando.freire@nike.com'))

detector = Detector()\
    .with_name('TEST: example detector')\
    .with_program(program)\
    .with_rules(info_rule)

"""
Example 2: from an existing chart

This is useful when you want to alert on behavior seen in a chart that was
created using the signal_analog library.
"""

test_program = Program(data)

chart = TimeSeriesChart()\
    .with_name('TEST: example chart for detector')\
    .with_program(test_program)  # Defined above


def detector_helper(prog):
    d = prog.find_label('A')
    return Program(Detect(LT(d, 1)).publish(alert_label))


c_detector = Detector()\
    .with_name('TEST: example detector from chart')\
    .from_chart(chart, detector_helper)\
    .with_rules(info_rule)

if __name__ == '__main__':
    from signal_analog.cli import CliBuilder
    cli = CliBuilder().with_resources(detector, c_detector).build()
    cli()
