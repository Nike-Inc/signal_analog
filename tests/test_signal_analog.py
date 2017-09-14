#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `signal_analog` package."""

from signal_analog import flow


def test_data_example():
    """Ensure that the data function can be correctly serialized"""
    assert str(flow.Data('cpu.utilization')) == 'data("cpu.utilization")'
