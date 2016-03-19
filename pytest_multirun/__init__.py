# -*- coding: utf-8 -*-
import py


u = py.builtin._totext


def ecu(s):
    try:
        return u(s, 'utf-8', 'replace')
    except TypeError:
        return s