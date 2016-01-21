# -*- coding: utf-8 -*-


class MultiRunClient(object):

    def __init__(self, multirun, node):
        self.__multirun = multirun
        self.__node = node

    def add_to_report(self, key, value=''):
        self.__node._report_sections.append((key, 'multirun', value))
