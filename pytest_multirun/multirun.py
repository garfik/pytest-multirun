# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE
from threading import Lock
from datetime import datetime, timedelta
import sys
import time
import json
import re
import os
import py
import pytest
from py._code.code import ReprExceptionInfo
from pytest_multirun.thread_pool import ThreadPool

_real_stdout = sys.stdout


def _executer(test_cmd, extra_arguments, lock, msg_handler):
    cmd = 'py.test {} --multirun-slave {}'.format(test_cmd, ' '.join(extra_arguments))
    try:
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, env=os.environ)
        while True:
            line = proc.stdout.readline().decode('windows-1251')
            if line == '' and proc.poll() is not None:
                break
            line = line.strip()
            if line.startswith('##multirun'):
                lock.acquire()
                # print(line)
                msg_handler(line)
                lock.release()
    except KeyboardInterrupt:
        print('\nCatch KeyboardInterrupt. Terminating all processes\n')
        if proc:
            proc.terminate()


class MultiRun(object):
    quote = {"'": "|'", "|": "||", "\n": "|n", "\r": "|r", ']': '|]'}

    def __init__(self, config):
        self.config = config
        self.reports = {}
        self.stats = {}
        self.tw = py.io.TerminalWriter()
        self.teamcity = False
        try:
            if config.option.teamcity >= 1:
                from teamcity.messages import TeamcityServiceMessages
                self.teamcity = TeamcityServiceMessages(_real_stdout)
        except (ImportError, AttributeError):
            pass

        if not self.tw:
            # сообщаем об ошибке
            pass

    def write_message(self, test_id, msg, value=''):
        def escape_value(text):
            return "".join([self.quote.get(x, x) for x in text])

        attrs = escape_value(str(value))
        print('\n##multirun|{0}|{1}|{2}|multirun##'.format(test_id, msg, attrs))

    def convert_msg_to_dict(self, msg):
        """

        :param str msg: String with message from subprocesses
        :return:
        """
        msg = msg.strip()
        if not msg.startswith('##multirun') or not msg.endswith('multirun##'):
            return
        ret = {
            'id': '',
            'key': '',
            'value': ''
        }
        # cut multirun prefix and postfix
        msg = msg[11:-11]
        ret['id'] = msg[:msg.find('|')]
        msg = msg[msg.find('|') + 1:]
        ret['key'] = msg[:msg.find('|')]
        msg = msg[msg.find('|') + 1:]
        if msg:
            for k,v in self.quote.items():
                msg = msg.replace(v, k)
            ret['value'] = msg
        return ret

    def print_crash_info(self, test_id, rep):
        if not rep:
            return

        if type(rep) == ReprExceptionInfo:
            self.write_message(test_id, 'testCrashLineNo', rep.reprcrash.lineno)
            self.write_message(test_id, 'testCrashText', rep.reprcrash.message)
            self.write_message(test_id, 'testCrashPath', rep.reprcrash.path)
            self.write_message(test_id, 'testCrashTrace', rep.reprtraceback)
        elif type(rep) == tuple:
            self.write_message(test_id, 'testCrashLineNo', rep[1])
            self.write_message(test_id, 'testCrashText', rep[2])
            self.write_message(test_id, 'testCrashPath', rep[0])
        else:
            self.write_message(test_id, 'testPluginError', 'longrepr: ' + str(rep))

    def pytest_runtest_setup(self, item):
        # item.multirun_client = self.mclient
        pass

    def pytest_runtest_logstart(self, nodeid, location):
        self.write_message(nodeid, 'testStart')

    @pytest.mark.hookwrapper
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        rep = outcome.get_result()
        print()
        if not rep:
            return
        if rep.when == 'call':
            self.print_crash_info(rep.nodeid, rep.longrepr)
            self.write_message(rep.nodeid, 'testDuration', rep.duration)
            self.write_message(rep.nodeid, 'testOutcome', rep.outcome)
        elif rep.when == 'teardown':
            for el in rep.sections:
                if el[0].lower().startswith('captured stdmultirun'):
                    self.write_message(rep.nodeid, 'MULTIRUN_EXTRA_{}'.format(el[0][21:].replace(' ', '')), el[1])
                if el[0].lower() == 'captured stdout call':
                    self.write_message(rep.nodeid, 'testStdOutCall', el[1])
                if el[0].lower() == 'captured stdout setup':
                    self.write_message(rep.nodeid, 'testStdOutSetup', el[1])
                if el[0].lower() == 'captured stdout teardown':
                    self.write_message(rep.nodeid, 'testStdOutTearDown', el[1])
            self.write_message(rep.nodeid, 'testStop')
        else:
            # если мы на стадии настройки упали, то сообщим об этом
            if rep.failed:
                self.print_crash_info(rep.nodeid, rep.longrepr)
                self.write_message(rep.nodeid, 'testOutcome', rep.outcome)

    def send_test_to_teamcity(self, item):
        def format_test_id(node_id):
            result = node_id

            if result.find("::") < 0:
                result += "::top_level"

            result = result.replace("::()::", "::")
            result = re.sub(r"\.pyc?::", r"::", result)
            result = result.replace(".", "_").replace(os.sep, ".").replace("/", ".").replace('::', '.')

            return result

        tc = self.teamcity
        if not tc:
            return
        test_id = format_test_id(item['id'])
        tc.testStarted(test_id, flowId=test_id)
        if item['report'].get('failed', False):
            location = '{}:{}'.format(item['report']['crash'].get('path', ''), item['report']['crash'].get('line'))
            tc.testFailed(test_id, location, item['report']['crash'].get('trace', ''), flowId=test_id)
        if bool(item['report']['stdout']):
            stdout = ''
            for el in item['report']['stdout']:
                stdout += '\n{0}:\n {1}'.format(el, item['report']['stdout'][el])
            tc.testStdOut(test_id, stdout, flowId=test_id)
        if bool(item['extra']):
            with tc.block('extra', flowId=test_id):
                for el in item['extra']:
                    tc.customMessage(el, item['extra'][el], flowId=test_id)
        duration = timedelta(seconds=item['report']['duration'])
        self.teamcity.testFinished(test_id, testDuration=duration, flowId=test_id)

    def message_handler(self, msg):
        # TODO: Support xfail\xpassed
        msg = self.convert_msg_to_dict(msg)
        if not msg:
            return

        if msg['id'] not in self.reports:
            self.reports[msg['id']] = {
                'id': msg['id'],
                'extra': {},
                'report': {
                    'crash': {},
                    'stdout': {}
                }
            }

        rep = self.reports[msg['id']]['report']
        if msg['key'] == 'testDuration':
            rep['duration'] = float(msg['value'])
        elif msg['key'] == 'testOutcome':
            rep['outcome'] = msg['value'].lower()
        elif msg['key'] == 'testStart':
            pass
        elif msg['key'] == 'testStop':
            # сообщим о том, что тест закончился
            if self.config.option.quiet == 0:
                self.tw.write(msg['id'])
            if rep['outcome'] not in self.stats:
                self.stats[rep['outcome']] = 0
            self.stats[rep['outcome']] += 1

            if rep['outcome'] == 'passed':
                rep['passed'] = True
                if self.config.option.verbose > 0:
                    self.tw.line(s=' PASSED', green=True)
                elif self.config.option.quiet > 0:
                    self.tw.write('.', green=True)
                else:
                    self.tw.line(s=' .', green=True)
            elif rep['outcome'] == 'failed':
                rep['failed'] = True
                if self.config.option.verbose > 0:
                    self.tw.line(s=' FAILED', red=True)
                elif self.config.option.quiet > 0:
                    self.tw.write('F', red=True)
                else:
                    self.tw.line(s=' F', red=True)
            else:
                self.tw.line(' ' + rep['outcome'])
            if rep['outcome'] == 'failed' or rep['outcome'] != 'passed':
                if bool(rep['crash']) and self.config.option.quiet == 0:
                    self.tw.write(rep['crash'].get('trace', ''))
                    self.tw.line()
                    trace_info = 'Catch at {0}:{1}'.format(rep['crash'].get('path', ''), rep['crash'].get('line'))
                    self.tw.line(s=trace_info)
                    self.tw.sep('_')
            self.send_test_to_teamcity(self.reports[msg['id']])
        elif msg['key'] == 'testCrashLineNo':
            rep['crash']['line'] = int(msg['value'])
        elif msg['key'] == 'testCrashText':
            rep['crash']['msg'] = msg['value']
        elif msg['key'] == 'testCrashPath':
            rep['crash']['path'] = msg['value']
        elif msg['key'] == 'testCrashTrace':
            rep['crash']['trace'] = msg['value']

        elif msg['key'] == 'testStdOutCall':
            rep['stdout']['call'] = msg['value']
        elif msg['key'] == 'testStdOutSetup':
            rep['stdout']['setup'] = msg['value']
        elif msg['key'] == 'testStdOutTearDown':
            rep['stdout']['teardown'] = msg['value']

        elif msg['key'].startswith('MULTIRUN_EXTRA_'):
            self.reports[msg['id']]['extra'][msg['key'][15:]] = msg['value']

        else:
            # get an unknown message... what we need to do?
            return

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

        categories = []
        # set categories list in cmd param
        if config.option.multirun_list:
            categories = [group.split(',') for group in config.option.multirun_list.split(':') if group]

        if not categories:
            # well, if cant find in cmd param then search in ini file
            categories = [group.split(',') for group in config.getini("multirun-list") if group]
            pass

        # check, that we have categories list
        if not categories:
            # if not, then tell about it and run as usually
            self.tw.line(s='Can\'t find any test group list. Please specify it by cmd param or in ini file', red=True)
            return

        if MAX_PROCESS < 2 or MAX_PROCESS > 20:
            # strange MAX_PROCESS variable, cancel multirun and run as usually
            self.tw.line(
                s='Strange "{}" value in "multirun-process" variable. Run as usually'.format(MAX_PROCESS), red=True)
            return

        # check, that we run not specified test or group
        # TODO: looks bad :(
        if not config.args or '.py' in config.args[0].lower() or '::' in config.args[0].lower():
            # TODO: сообщаем об ошибке
            self.tw.line(s='Looks like we have only one test. Run as usually', red=True)
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

        # take supported arguments to subprocesses
        extra_args = []
        for arg in config._origargs:
            if arg.startswith('--tb='):
                extra_args.append(arg)

        lock = Lock()
        pool = ThreadPool(MAX_PROCESS)

        for group in categories:
            for test in group:
                pool.add_task(_executer, test, extra_args, lock, self.message_handler)

            pool.start_task()
            pool.wait_completion()

        if config.option.quiet > 0:
            self.tw.line()

        report = {
            'datetime': datetime.now().isoformat(),
            'duration': time.time() - time_start,
            'cases': self.reports,
            'stats': self.stats
        }

        if config.option.multirun_logfile:
            # cleanup old log file
            folder = os.path.dirname(os.path.abspath(config.option.multirun_logfile))
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(config.option.multirun_logfile, mode='w') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)

        if 'failed' in self.stats and self.stats['failed'] > 0:
            markup = {'red': True}
        else:
            markup = {'green': True}

        parts = ['{1} {0}'.format(x, self.stats[x]) for x in self.stats if self.stats[x] > 0]
        msg = "%s in %.2f seconds" % (', '.join(parts), report['duration'])
        self.tw.sep('=', title=msg, **markup)
        return 0
