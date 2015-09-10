# -*- coding: utf-8 -*-
import pytest
import sys


def check_pytest(file_name):
    if not hasattr(sys, '_called_from_test'):
        pytest.main(file_name)
