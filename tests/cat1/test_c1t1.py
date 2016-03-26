# -*- coding: utf-8 -*-
import common
import time
import pytest
common.check_pytest(__file__ + ' ')


def test_c1t1(tsf):
    time.sleep(2)
    print('captured stdout error')
    assert 1, 'Assertion error message'
