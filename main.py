#!/usr/bin/env python
# -*- coding: utf-8 -*-

import equipment
import json

__author__ = "Ewerton Oliveira"
__credits__ = ["Ewerton Oliveira"]
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Ewerton Oliveira"
__email__ = "ewerton.tccmbr@gmail.com"
__status__ = "Development"


class GUI:

    @staticmethod
    def head(title):
        print ''
        print 123 * '='
        print 50*' '+title
        print 123 * '='


class Application(GUI):

    def __init__(self):
        self.head('Equipment Tester - version: '+__version__)

        try:
            self.menu()
        except KeyboardInterrupt:
            print 'Bye'
        else:
            self.__init__()

    def menu(self):
        print ''
        print 'Menu:'
        print ''
        print "[1] - Testar Ubiquiti"
        print "[2] - Testar Intelbras"
        print "[0] - Sair"
        print ''

        try:
            opcao = int(raw_input('Opção = '))
        except ValueError:
            print 'Informe apenas números!'
        else:
            if opcao == 1:
                equipment.Ubiquiti(self.config())
            elif opcao == 2:
                equipment.Intelbras()
            elif opcao == 0:
                exit()
            else:
                print 'Opção inválida!'
                self.menu()

    @staticmethod
    def config():
        with open('config/app_config.json') as config_file:
            return json.load(config_file)

if __name__ == '__main__':
    app = Application()
