#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


class Ubiquiti:

    def __init__(self):
        self.ip = '192.168.1.20'
        self.ping()

    def ping(self):
        print 'Testando ping...'
        print ''
        command = ('/bin/ping %s -c20 -s1472' % self.ip)
        os.system(command)


class Intelbras:

    def __init__(self):
        pass
