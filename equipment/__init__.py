#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import paramiko
import scp
import json
import re
import time
import struct
import main


class Ubiquiti(main.GUI):
    ssh_client = None

    def __init__(self, app_config):
        self.head('UBIQUITI')
        self.app_config = app_config
        self.host = self.app_config['connection']['host']
        self.username = self.app_config['connection']['username']
        self.password = self.app_config['connection']['password']
        self.port = self.app_config['connection']['port']

        if self.host:
            os.system('ifconfig eth0:100 192.168.1.254 netmask 255.255.255.0 up')
            self.menu()
        else:
            print 'Configure o IP do host nas configurações da aplicação!'

    def menu(self):
        print ''
        print 'Menu:'
        print ''
        print '[1] - Testar Latência'
        print '[2] - Testar /10Mbs'
        print '[3] - Testar SCAN'
        print '[4] - Testar AP Connection'
        print '[5] - Atualizar Firmware'
        print '[6] - Todos'
        print '[0] - Sair'
        print ''

        try:
            opcao = int(raw_input('Opção: '))
        except ValueError:
            print 'Informe apenas números!'
        else:
            if opcao in range(7):
                if opcao == 1:
                    self.ping()
                if opcao == 2:
                    self.verify_teen_bar()
                elif opcao == 3:
                    self.survey()
                    self.default_config()
                elif opcao == 4:
                    self.head('AP Connection')
                    self.verify_ap_connection()
                elif opcao == 5:
                    self.firmware_update()
                elif opcao == 6:
                    if self.ping() == 0:
                        self.verify_teen_bar()
                        self.survey()
                        self.firmware_update()
                        self.default_config()
                elif opcao == 0:
                    self.exit()
                    return True
                else:
                    print 'Opção inválida!'

        self.menu()

    def connect(self):
        try:
            if not type(self.port) is int:
                raise ValueError('Configure o número da porta SSH nas configurações da aplicação!')

            self.disconnect()
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(hostname=self.host, port=self.port, username=self.username,
                                    password=self.password)
        except paramiko.ssh_exception.SSHException as e:
            print 'SSH error: %s .' % e.message
            print 'Verifique as informações de conexão nas configurações desta aplicação!'
            return False
        except paramiko.ssh_exception.NoValidConnectionsError:
            print 'Não foi possível conectar'
            print 'Verifique as informações de conexão nas configurações desta aplicação!'
            return False
        except ValueError:
            print 'Informações de conexão inválidas!'
            return False
        except AttributeError as e:
            print 'Error: %s' % e.message
            return False
        else:
            return True

    def disconnect(self):
        if type(self.ssh_client) is paramiko.SSHClient:
            self.ssh_client.close()

        self.ssh_client = None

    @staticmethod
    def exit():
        os.system('ifconfig eth0:100 down')

    def ping(self):
        self.head('Testando ping')

        command = ('/bin/ping %s -c10 -s1472' % self.host)
        return os.system(command)

    def verify_teen_bar(self):
        self.head('Teste 10Mb/s')
        if self.connect():
            stdin, stdout, stderr = self.ssh_client.exec_command('ethtool eth0')

            if not stderr.readlines():
                info = stdout.read()
                result = re.search('([Speed]{5}:\s)+([0-9]+)+([M?G]b/s)+', info)
                if result:
                    speed = result.group(2)
                    if speed == '10':
                        print 'Falha no teste! A interface esta dando 10Mb/s!'
                    else:
                        print 'Teste OK! A interface esta dando %s%s' % (speed, result.group(3))
                else:
                    print 'Falha no teste!'

    def survey(self):
        self.head('SCAN Access Point')
        if self.connect():
            stdin, stdout, stderr = self.ssh_client.exec_command('/usr/www/./survey.json.cgi')

            if not stderr.readlines():
                try:
                    survey_file = open('survey.json', 'w')
                except IOError:
                    print 'Mão foi possível criar o arquivo survey.json!'
                else:
                    result = stdout.readlines()
                    result.pop(0)
                    for l in result:
                        survey_file.write(l)

                    survey_file.close()
                    with open('survey.json', 'r') as data_file:
                        data = json.load(data_file)

                        print '%9s %28s %5s %10s %s %s %20s %15s' % ('mac', 'frequency', 'quality', 'signal_level',
                                                                     'noise_level', 'encryption', 'essid',
                                                                     'auth_suites')
                        print 123*'-'
                        i = 0
                        essid_connect_list = {}
                        for ap in data:
                            i += 1
                            if i < 10:
                                indice = '0%d' % i
                            else:
                                indice = str(i)

                            print '%s %20s %10s %10s %10s %10s %8s %24s %10s' % (indice, ap['mac'], ap['frequency'],
                                                                                 ap['quality'], ap['signal_level'],
                                                                                 ap['noise_level'], ap['encryption'],
                                                                                 ap['essid'], ap['auth_suites'],)
                            essid_connect_list[indice] = (ap['essid'], ap['encryption'])

                        print ''
                        connect_test = raw_input('Deseja testar conectar no painel? [y,n] ')

                        if connect_test.lower() == 'y':
                            def ap_connect():
                                num_painel = raw_input('Informe o número do painel: ')
                                try:
                                    self.alter_default_config(access_point=essid_connect_list[num_painel])
                                    self.head('AP Connection')
                                    self.verify_ap_connection()
                                except KeyError:
                                    print 'Nº do painel inválido!'
                                    ap_connect()

                            ap_connect()

                    os.system('rm survey.json')
        else:
            print 'Falha no teste!'

    def alter_default_config(self, access_point):
        if self.connect():
            print ''

            stdin, stdout, stderr = self.ssh_client.exec_command('cat /etc/default.cfg')

            if not stderr.readlines():
                system_file = open('config/system.cfg', 'w')
                wpa_config = self.wpa_config(essid=access_point[0], secret=self.app_config['ubiquiti']['wpasecret'])

                print u'Alterando arquivo de configuração para permitir conexão no AP %s ...' % access_point[0]

                systemcfg = stdout.readlines()

                for l in systemcfg:
                    exp = re.search('wireless.1.ssid=', l)
                    if exp:
                        l = "wireless.1.ssid=%s\n" % access_point[0]

                    if access_point[1] != 'wpa2':
                        if l in wpa_config:
                            l = ''

                    exp = re.search('sshd.port=', l)
                    if exp:
                        if type(self.app_config['ubiquiti']['ssh_port']) is int:
                            ssh_port = self.app_config['ubiquiti']['ssh_port']
                        else:
                            ssh_port = 22

                        l = "sshd.port=%s\n" % ssh_port

                    exp = re.search('system.eirp.status=', l)
                    if exp:
                        l = "system.eirp.status=enabled\n"

                    exp = re.search('radio.1.reg_obey=', l)
                    if exp:
                        l = "radio.1.reg_obey=disabled\n"

                    system_file.write(l)

                if access_point[1] == 'wpa2':
                    for i in wpa_config:
                        system_file.write(i)

                if 'httpd.port=' not in systemcfg:
                    if type(self.app_config['ubiquiti']['http_port']) is int:
                        http_port = self.app_config['ubiquiti']['http_port']
                    else:
                        http_port = 80

                    system_file.write("httpd.port=%d\n" % http_port)

                if 'httpd.session.timeout=' not in systemcfg:
                    system_file.write("httpd.session.timeout=900\n")

                if 'discovery.cdp.status=' not in systemcfg:
                    system_file.write("discovery.cdp.status=disabled\n")

                system_file.close()

                print 'enviando arquivo de configuração para o dispositivo...'
                self.send_file('config/system.cfg', '/tmp/')

                os.system('rm config/system.cfg')

                print 'Aplicando configuração....'
                self.ssh_client.exec_command('cd / ; cfgmtd -w -p /tmp ; reboot')
                time.sleep(90)

    def verify_ap_connection(self, verification_time=6):
        if self.connect():
            print 'Tentativa nº %d' % verification_time

            if verification_time > 0:
                stdin, stdout, stderr = self.ssh_client.exec_command('wstalist')

                if not stderr.readlines():
                    wstalist = stdout.read()

                    if re.search('[a-z]+', wstalist):
                        print 'Conectado no painel com sucesso!'
                        return True
                    else:
                        success = False
                else:
                    success = False

                if not success:
                    time.sleep(10)
                    verification_time -= 1
                    self.verify_ap_connection(verification_time)
            else:
                print 'O equipamento não conectou no AP. Verifique a senha PSK na configuração desta aplicação ou '\
                      'se você usa autenticação via\n Radius, cheque se o atributo "Auth-Type" esta com o valor ' \
                      '"Accept"!'
        else:
            print 'Falha no teste!'

    def firmware_update(self):
        self.head('FIRMWARE UPDATE')
        if self.connect():
            stdin, stdout, stderr = self.ssh_client.exec_command('cat /etc/version')

            if not stderr.readlines():
                firmware_atual = stdout.read()
                type_firmware_atual = firmware_atual[:2]

                if type_firmware_atual == 'XW':
                    filename = self.app_config['ubiquiti']['file_XW_update']
                elif type_firmware_atual == 'XM':
                    filename = self.app_config['ubiquiti']['file_XM_update']
                else:
                    print 'O Tipo da versão do firmware não é compativel com nenhuma configuração deste aplicativo.'
                    return False

                try:
                    file_ = open(filename, mode='rb')
                    content = file_.read()
                    dados = struct.unpack('30s', content[:30])

                    type_firmware = re.search('X[M?W]+', dados[0])
                    version_firmware = re.search('v[\d]+.[\d]+.[\d]+', dados[0])

                    if type_firmware and version_firmware:
                        firmware_novo = '%s.%s' % (type_firmware.group(0), version_firmware.group(0))

                        if type_firmware.group(0) in firmware_atual:
                            if not self.verify_firmware_version(firmware_novo):
                                print 'Iniciando atualização do firmware para %s' % firmware_novo
                                self.ssh_client.exec_command('rm /tmp/fwupdate.bin')
                                print 'Removendo arquivo temporário de atualização anterior...'
                                print 'Enviando arquivo...'

                                if self.send_file(filename, '/tmp/fwupdate.bin'):
                                    print 'Aplicando atualização...'
                                    self.ssh_client.exec_command('/sbin/fwupdate -m')
                                    print 'Aplicada com sucesso e reiniciando...'
                                    time.sleep(60)
                                    self.verify_firmware_version(firmware_novo)
                        else:
                            print 'Firmware %s incompativel com %s !' % (type_firmware.group(0), firmware_atual)
                    else:
                        print 'Não foi possível verificar o arquivo de atualização do firmware.'
                except IOError:
                    print 'Não foi possível abrir os arquivos de firmware update!'
        else:
            print 'Falha no teste!'

    def verify_firmware_version(self, firmware_version):
        print ''
        if self.connect():
            print 'verificando se a versão atual é igual a %s ...' % firmware_version
            stdin, stdout, stderr = self.ssh_client.exec_command('cat /etc/version')

            if not stderr.readlines():
                firmware_atual = stdout.read()
                firmware_atual = firmware_atual.strip()
                firmware_version = firmware_version.strip()

                if firmware_version == firmware_atual:
                    print 'Verificação concluida!'
                    return True
                else:
                    print 'Versão atual %s' % firmware_atual
            else:
                print 'Ocorreu um problema na verificação!'

            return False

    def send_file(self, local, remote):
        try:
            client = scp.SCPClient(self.ssh_client.get_transport())
            client.put(files=local, remote_path=remote)
            print 'Arquivo enviado com sucesso!'
            return True
        except scp.SCPException:
            print 'Ocorreu um problema ao tentar enviar o arquivo!'

        return False

    @staticmethod
    def wpa_config(essid, secret):
        config = [
            "wpasupplicant.profile.1.network.1.psk=%s\n" % secret,
            "aaa.1.wpa.psk=%s\n" % secret,
            "wpasupplicant.profile.1.network.1.ssid=%s\n" % essid,
            "wpasupplicant.status=enabled\n",
            "wpasupplicant.device.1.status=enabled\n",
            "wpasupplicant.device.1.devname=ath0\n",
            "wpasupplicant.device.1.driver=madwifi\n",
            "wpasupplicant.profile.1.network.1.proto.1.name=RSN\n",
            "wpasupplicant.profile.1.network.1.pairwise.1.name=CCMP\n",
            "wpasupplicant.device.1.profile=WPA-PSK\n",
            "wpasupplicant.profile.1.name=WPA-PSK\n",
            "wpasupplicant.profile.1.network.1.key_mgmt.1.name=WPA-PSK\n",
            "wpasupplicant.profile.1.network.1.bssid=\n",
            "wpasupplicant.profile.1.network.1.eap.1.status=disabled\n"
        ]

        return config

    def default_config(self):
        if self.connect():
            self.ssh_client.exec_command('cp /etc/default.cfg /tmp/system.cfg')
            self.ssh_client.exec_command('cd / ; cfgmtd -w -p /tmp/ ; reboot')


class Intelbras:
    def __init__(self):
        pass
