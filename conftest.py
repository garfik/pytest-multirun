# -*- coding: utf-8 -*-
import sys
from py._code.code import ReprExceptionInfo
import pytest


def pytest_unconfigure():
    if hasattr(sys, '_called_from_test'):
        del sys._called_from_test


def pytest_configure():
    sys._called_from_test = True


@pytest.fixture(scope='function')
def tsf(request, multirun):
    def fin():
        if not multirun:
            return
        multirun.add_to_report('screenshot', '123123123123213_dasdasdasd.png')

    request.addfinalizer(fin)
    return 'some custom driver'
