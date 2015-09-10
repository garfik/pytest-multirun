# -*- coding: utf-8 -*-
import pytest
import sys
import time
import os


def check_pytest(file_name):
    if not hasattr(sys, '_called_from_test'):
        pytest.main(file_name)


def get_lock(timeout=30):
    start_time = time.time()
    while True:
        try:
            return open('.lock', mode='x')
        except FileExistsError:
            time.sleep(0.2)
            current_time = time.time()
            if current_time - start_time > timeout:
                raise TimeoutError('Too long cant get lock')


def free_lock(lock=None):
    if lock:
        lock.close()
    try:
        os.unlink('.lock')
    except FileNotFoundError:
        pass
