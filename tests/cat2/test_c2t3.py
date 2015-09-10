# -*- coding: utf-8 -*-
import common
import time
import pytest
common.check_pytest(__file__)


def test_c2t3():
    """
    этот тест добавлен в исключения, то бишь в групповом запуске вообще никак не участвует. Однако легко можно запустить
    просто введя нечто в духе py.test tests/cat2/test_c2t3.py
    """
    time.sleep(3)
    assert 0
