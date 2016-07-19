#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import paramiko
import json
import re


class Ubiquiti:
    result = {}
    ssh = None
    ip = '192.168.1.254'
    port = 2250
    username = 'suportemax'
    password = 'max2suporte'

    def __init__(self):
        if self.ping() == 0:
            self.survey()
        else:
            print '[Fail] Ping'
            exit()

    def ping(self):
        print ''
        print 'Testando ping...'
        print ''

        command = ('/bin/ping %s -c1 -s1472' % self.ip)
        return os.system(command)

    def survey(self):
        print ''

        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=self.ip, port=self.port, username=self.username, password=self.password)

            stdin, stdout, stderr = self.ssh.exec_command('/usr/www/./survey.json.cgi')

            if not stderr.readlines():
                survey_file = open('survey.json', 'w')
                result = stdout.readlines()
                result.pop(0)
                for l in result:
                    survey_file.write(l)

                survey_file.close()
                with open('survey.json') as data_file:
                    data = json.load(data_file)

                    print 123 * '='
                    print 50 * ' ' + 'SCAN Access Point'
                    print 123 * '='

                    print '%9s %28s %5s %10s %s %s %20s %15s %s' % ('mac', 'frequency', 'quality', 'signal_level',
                                                                    'noise_level', 'encryption', 'essid', 'auth_suites',
                                                                    'ieee_mode')
                    i = 0
                    indice = ''
                    essid_connect_list = {}
                    for ap in data:
                        i += 1
                        if i < 10:
                            indice = '0%d' % i

                        print '%s %20s %10s %10s %10s %10s %11s %24s %10s %12s' % (indice, ap['mac'], ap['frequency'],
                                                                                   ap['quality'], ap['signal_level'],
                                                                                   ap['noise_level'], ap['encryption'],
                                                                                   ap['essid'], ap['auth_suites'],
                                                                                   ap['ieee_mode'])
                        essid_connect_list[indice] = (ap['essid'], ap['encryption'])

                    connect_test = raw_input('Deseja testar conectar no painel? [y,n] ')

                    if connect_test == 'y':
                        ap_connect = raw_input('Informe número do painel: ')

                        if essid_connect_list[ap_connect][0]:
                            print ''
                            print 'Conectando no ESSID %s ...' % essid_connect_list[ap_connect][0]

                            stdin, stdout, stderr = self.ssh.exec_command('cat /tmp/system.cfg')

                            if not stderr.readlines():
                                system_file = open('system.cfg', 'w')

                                for l in stdout.readlines():
                                    exp = re.search('wireless.1.ssid=', l)
                                    if exp:
                                        l = "wireless.1.ssid=%s\n" % essid_connect_list[ap_connect][0]

                                    if essid_connect_list[ap_connect][1] == 'wpa2':
                                        exp = re.search('wpasupplicant.profile.1.network.1.psk=', l)
                                        if exp:
                                            l = "wpasupplicant.profile.1.network.1.psk=amorajackson\n"

                                        exp = re.search('wpasupplicant.profile.1.network.1.ssid=', l)
                                        if exp:
                                            l = "wpasupplicant.profile.1.network.1.ssid=%s\n" % essid_connect_list[ap_connect][0]

                                    system_file.write(l)

                                system_file.close()

                self.ssh.exec_command('exit')
            else:
                return False
        except paramiko.SSHException:
            print 'Não foi possível conectar.'


class Intelbras:
    def __init__(self):
        pass
