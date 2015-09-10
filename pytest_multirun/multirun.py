# -*- coding: utf-8 -*-
import time
import json
import sys
import os
from datetime import datetime
from subprocess import Popen, PIPE
from multiprocessing import Pool
# from _pytest.runner import TestReport
import py
import pytest
from pytest_multirun.wait_thread import WaitThread
from pytest_multirun.multirun_client import MultiRunClient


def _executer(test_cmd, port):
    # TODO: Для мака и линукса надо :, а для винды надо ;
    env_path = ';'.join(sys.path)
    cmd = 'py.test ' + test_cmd + ' --multirun-port=' + str(port) + ' --multirun-slave'
    with Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, env={'PATH': env_path, 'SystemRoot': 'C:\\Windows'}) as proc:
        out, err = proc.communicate()


class MultiRun(object):
    PORT_NUMBER = 0

    def __init__(self, config):
        self.config = config
        self.PORT_NUMBER = config.option.multirun_port
        self.mclient = MultiRunClient(self.PORT_NUMBER)
        self.reports = {}
        self.stats = {}
        self.tw = py.io.TerminalWriter()
        if not self.tw:
            # сообщаем об ошибке
            pass

    def pytest_runtest_setup(self, item):
        item.multirun_client = self.mclient

    @pytest.mark.tryfirst
    def pytest_runtest_makereport(self, item, call, __multicall__):
        rep = __multicall__.execute()

        if not item.config.option.multirun_slave:
            return rep

        if rep.when != 'call':
            return rep

        self.mclient.send_report(rep)

        return rep

    def message_handler(self, msg):
        # TODO: Сделать поддержку verbose
        # TODO: Сделать поддержку xfail
        if 'TestReport' in str(type(msg)) and hasattr(msg, 'nodeid'):
            # пришел отчет о тесте
            if msg.nodeid not in self.reports:
                self.reports[msg.nodeid] = {}
            self.reports[msg.nodeid]['report'] = msg
            self.tw.write(msg.location[0])

            if msg.outcome.lower() not in self.stats:
                self.stats[msg.outcome.lower()] = 0
            self.stats[msg.outcome.lower()] += 1

            if msg.outcome.lower() == 'passed':
                self.tw.line(s=' .', green=True)
            elif msg.outcome.lower() == 'failed':
                self.tw.line(s=' F', red=True)
                if msg.longrepr:
                    self.tw.write(msg.longrepr)
                    self.tw.line()
                    self.tw.sep('_')
            else:
                self.tw.line(' ' + msg.outcome)
                if msg.longrepr:
                    self.tw.write(msg.longrepr)
                    self.tw.line()
                    self.tw.sep('_')
        elif type(msg) == dict and msg['type'] == 'extra':
            if msg['nodeid'] not in self.reports:
                self.reports[msg['nodeid']] = {}
            rep = self.reports[msg['nodeid']]
            if 'extra' not in rep:
                rep['extra'] = {}
            rep['extra'][msg['key']] = msg['value']
        else:
            print(msg)

    def convert_test_report_to_dict(self, tr):
        # TODO: Конвертировать в нормальные строки без всяких \u4352
        if type(tr) != dict:
            return None
        if 'report' not in tr or type(tr['report']) != 'TestReport':
            return None
        res = {
            'nodeid': tr['report'].nodeid,
            'duration': tr['report'].duration,
            'keywords': tr['report'].keywords,
            'location': tr['report'].location,
            'outcome': tr['report'].outcome,
            'failed': tr['report'].failed,
            'name': tr['report'].location[2],
            'path': tr['report'].location[0],
            'passed': tr['report'].passed,
            'skipped': tr['report'].skipped,
            'longrepr': None,
            'when': tr['report'].when,
            'sections': tr['report'].sections,
            'extra': tr['extra'] if 'extra' in tr else None
        }

        if tr['report'].longrepr and hasattr(tr['report'].longrepr, 'reprcrash'):
            res['longrepr'] = {
                'trace': str(tr['report'].longrepr),
                'text': tr['report'].longrepr.reprcrash.message,
                'lineno': tr['report'].longrepr.reprcrash.lineno,
                'path': tr['report'].longrepr.reprcrash.path
            }
        elif tr['report'].longrepr and type(tr['report'].longrepr) == tuple:
            res['longrepr'] = {
                'trace': '',
                'text': tr['report'].longrepr[2],
                'lineno': tr['report'].longrepr[1],
                'path': tr['report'].longrepr[0]
            }
        elif tr['report'].longrepr:
            res['longrepr'] = str(tr['report'].longrepr)

        return res

    def pytest_cmdline_main(self, config):
        # if run as slave node, then run as usually
        if config.option.multirun_slave:
            return

        # if multirun is disabled, then run as usually
        if not config.option.multirun:
            return

        MAX_PROCESS = config.getini('multirun-process')
        if type(MAX_PROCESS) == list:
            MAX_PROCESS = int(MAX_PROCESS[0])
        elif type(MAX_PROCESS) == str:
            MAX_PROCESS = int(MAX_PROCESS)

        categories = [group.split(',') for group in config.getini("multirun-list")]

        # check, that we have categories list
        if not categories:
            # TODO: сообщаем об ошибке
            return

        if MAX_PROCESS < 2 or MAX_PROCESS > 20:
            # TODO: неправильно значение мультизапуска, сообщаем об ошибке
            return

        # check, that we run not specified test or group
        # TODO: looks bad :(
        if not config.args or '.py' in config.args[0].lower() or '::' in config.args[0].lower():
            # TODO: сообщаем об ошибке
            return

        time_start = time.time()

        self.tw.sep('=', title='test session start')
        self.tw.line(s='### Parallel run mode activated ###', green=True)
        self.tw.line()
        self.tw.line(s='Run order:')
        for i in range(len(categories)):
            self.tw.line(s='{0} - {1}'.format(i+1, ', '.join(categories[i])))
        self.tw.line(s='Maximum process in one time: ' + str(MAX_PROCESS))
        self.tw.line()
        self.tw.line(s='lets go...')
        self.tw.line()

        listener = WaitThread(self.PORT_NUMBER, self.message_handler)
        listener.start()

        for group in categories:
            with Pool(processes=MAX_PROCESS) as pool:
                pool.starmap(_executer, [(test, self.PORT_NUMBER) for test in group])

        listener.stop()
        listener.join(10)

        report = {
            'datetime': datetime.now().isoformat(),
            'duration': time.time() - time_start,
            'cases': [self.convert_test_report_to_dict(self.reports[x]) for x in self.reports],
            'stats': self.stats
        }

        if config.option.multirun_logfile:
            # cleanup old log file
            # TODO: Проверка на возможность создать файл где надо
            with open(config.option.multirun_logfile, mode='w') as f:
                json.dump(report, f, indent=4)

        if 'failed' in self.stats and self.stats['failed'] > 0:
            markup = {'red': True}
        else:
            markup = {'green': True}

        parts = ['{1} {0}'.format(x, self.stats[x]) for x in self.stats if self.stats[x] > 0]
        msg = "%s in %.2f seconds" % (', '.join(parts), report['duration'])
        self.tw.sep('=', title=msg, **markup)

        return 0
