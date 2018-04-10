# -*- coding: utf-8 -*-
import hypothesis
from hypothesis import settings, HealthCheck

"""Unit test package for signal_analog."""
settings.register_profile("ci", deadline=9600,
                          suppress_health_check=[HealthCheck.too_slow, HealthCheck.hung_test],
                          timeout=hypothesis.unlimited)
