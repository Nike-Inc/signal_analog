#!/usr/bin/env python

"""Examples of how to use the `signal_analog.flow` module.

Some basic understanding of SignalFx is assumed.
"""

from signal_analog.flow import Data, Filter, Program

# A program is a convenient wrapper around SignalFlow statements with a few
# utilities like `find_label` that returns a SignalFlow statement based on it's
# label.
program = Program()

# A timeseries representing the 'cpu.utilization' metric that is filtered
# down to just the 'shoeadmin' application. Also analyze the mean over the
# previous minute and compare it to the data from last week.
data = Data('cpu.utilization', filter=Filter('app', 'shoeadmin'))\
    .mean(over='1m')\
    .timeshift('1w')\
    .publish('A')

program.add_statements(data)

print('{0}\n\t{1}'.format(
    program, str(program) == str(program.find_label('A'))))
