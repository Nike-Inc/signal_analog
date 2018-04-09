#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `signal_analog` package."""
import hypothesis
from hypothesis import settings, HealthCheck

from signal_analog import flow


settings.register_profile("ci", deadline=9600, suppress_health_check=[HealthCheck.too_slow, HealthCheck.hung_test], timeout=hypothesis.unlimited)
settings.load_profile("ci")


def test_data_example():
    """Ensure that the data function can be correctly serialized"""
    assert str(flow.Data('cpu.utilization')) == 'data("cpu.utilization")'
