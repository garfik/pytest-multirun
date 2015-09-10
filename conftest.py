# -*- coding: utf-8 -*-
import sys
import pytest


def pytest_unconfigure():
    if hasattr(sys, '_called_from_test'):
        del sys._called_from_test


def pytest_configure():
    sys._called_from_test = True


@pytest.fixture(scope='function')
def tsf(request, multirun):
    def fin():
        multirun.add_to_report(request.node.nodeid, 'screenshot', {
            'filename': '123123123123213_dasdasdasd.png',
            'duration': 123123
        })

    request.addfinalizer(fin)
    return 'какой-то там драйвер'
