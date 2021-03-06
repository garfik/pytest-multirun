# -*- coding: utf-8 -*-
import pytest
from pytest_multirun.multirun import MultiRun
from pytest_multirun.multirun_client import MultiRunClient


@pytest.fixture(scope='function')
def multirun(request):
    mr = request.config.pluginmanager.getplugin('_multirun')
    if not mr:
        return

    return MultiRunClient(mr, request.node)


def pytest_cmdline_main(config):
    # if multirun is disabled, then run as usually
    if not config.option.multirun_slave and not config.option.multirun:
        return

    m = MultiRun(config)
    config.pluginmanager.register(m, '_multirun')
    return m.pytest_cmdline_main(config)


def pytest_addoption(parser):
    # cmd options
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
        '--multirun-debugfolder',
        action='store',
        default=None,
        help='Write all output from py.test processes to chosen folder'
    )
    group.addoption(
        '--multirun-slave',
        action='store_true',
        default=False,
        help='Internal option to say pytest, that this session in subprocess'
    )
    group.addoption(
        '--multirun-list',
        action='store',
        help='List of commands divided by ";" for group and divided by "," for tests in group. '
             'This param has priority on INI option',
        default=None
    )
    group.addoption(
        '--multirun-rerun',
        action='store',
        help='Maximum tries before test set as failed',
        default=None
    )

    # INI options
    parser.addini(
        'multirun-list',
        help='List of commands divided by newline for group and divided by "," for tests in group',
        type='linelist',
        default=[]
    )
    parser.addini(
        'multirun-process',
        help='Maximum processes at one time',
        type='args',
        default=5
    )
    parser.addini(
        'multirun-rerun',
        help='Maximum tries before test set as failed',
        type='args',
        default=0
    )
