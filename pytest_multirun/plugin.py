# -*- coding: utf-8 -*-
import pytest
from pytest_multirun.multirun import MultiRun


@pytest.fixture(scope='function')
def multirun(request):
    if not hasattr(request.node, 'multirun_client'):
        return None

    return request.node.multirun_client


def pytest_cmdline_main(config):
    # if multirun is disabled, then run as usually
    if not config.option.multirun_slave and not config.option.multirun:
        return

    m = MultiRun(config)
    config.pluginmanager.register(m, '_multirun')
    return m.pytest_cmdline_main(config)


def pytest_addoption(parser):
    # TODO: multirun-list принимать и как параметр командной строки
    # TODO: сделать поддержку teamcity

    group = parser.getgroup("Run in multiple processes", "multirun")
    group.addoption(
        '--multirun',
        action='store_true',
        default=False,
        help='Enable parallel running for tests described in multirun-list'
    )
    group.addoption(
        '--multirun-logfile',
        action='store',
        default=None,
        help='Write results to file in JSON format'
    )
    group.addoption(
        '--multirun-port',
        action='store',
        default=6432,
        help='Port to communicate between processes'
    )
    group.addoption(
        '--multirun-slave',
        action='store_true',
        default=False,
        help='Internal option to say pytest, that this session in subprocess'
    )
    parser.addini(
        'multirun-list',
        help='List of commands divided by space for group and divided by "," for tests in group',
        type='args',
        default=[]
    )
    parser.addini(
        'multirun-process',
        help='Maximum processes at one time',
        type='args',
        default=5
    )
