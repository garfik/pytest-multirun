# -*- coding: utf-8 -*-
import pytest
import sys
from multirun.multirun import MultiRun


def pytest_unconfigure():
    if hasattr(sys, '_called_from_test'):
        del sys._called_from_test


def pytest_configure():
    sys._called_from_test = True


@pytest.fixture(scope='function')
def multirun(request):
    return request.node.multirun_client


@pytest.fixture(scope='function')
def tsf(request, multirun):
    def fin():
        multirun.add_to_report(request.node.nodeid, 'screenshot', {
            'filename': '123123123123213_dasdasdasd.png',
            'duration': 123123
        })
        # request.node['asdasd'] = 'айлалала'

    request.addfinalizer(fin)
    return 'какой-то там драйвер'


def pytest_cmdline_main(config):
    # if multirun is disabled, then run as usually
    if not config.option.multirun_slave and not config.option.multirun:
        return

    m = MultiRun(config)
    config.pluginmanager.register(m, 'multirun')
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

"""

def pytest_runtestloop(session):
    if len(session.items) <= 1:
        return
    if not session.config.option.multirun:
        return
    time_start = time.time()

    categories = []
    try:
        mlist = session.config.getini("multirun-list")
        for group in mlist:
            tests = group.split(',')
            for test in tests:
                ok = False
                for item in session.items:
                    if path.dirname(item.location[0]) == test:
                        ok = True
                        break
                if not ok:
                    print('Unknown category in pytest.ini - ' + test)
                    return
            categories.append(tests)
    except ValueError:
        return

    print('### Parallel run mode activated ###')
    results = Manager().list()
    for group in categories:
        with Pool(processes=3) as pool:
            pool.starmap(execute, [(test, results) for test in group])

    stats = {
        'skipped': 0,
        'passed': 0,
        'failed': 0
    }
    tr = session.config.pluginmanager.getplugin('terminalreporter')
    for x in results:
        if x['skipped']: stats['skipped'] += 1
        if x['passed']: stats['passed'] += 1
        if x['failed']: stats['failed'] += 1
        if tr and hasattr(tr, 'stats') and type(tr.stats) == dict:
            if x['outcome'] not in tr.stats:
                tr.stats[x['outcome']] = []
            x['sections'] = []
            rep_object = BaseReport(**x)
            tr.stats[x['outcome']].append(rep_object)

    if session.config.option.multirun_logfile:
        # cleanup old log file
        report = {
            'datetime': datetime.now().isoformat(),
            'duration': time.time() - time_start,
            'cases': [x for x in results],
            'stats': stats
        }
        with open(session.config.option.multirun_logfile, mode='w') as f:
            json.dump(report, f, indent=4)

    # print(results, len(results))
    return True
"""