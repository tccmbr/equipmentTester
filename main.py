#!/usr/bin/env python
# -*- coding: utf-8 -*-

import equipment

__author__ = "Ewerton Oliveira"
__credits__ = ["Ewerton Oliveira"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Ewerton Oliveira"
__email__ = "ewerton.tccmbr@gmail.com"
__status__ = "Development"


class Application:

    def __init__(self):
        print 60*'='
        print 11*' '+'Equipment Tester - version: '+__version__
        print 60*'='

        self.menu()

    @staticmethod
    def menu():
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
                equipment.Ubiquiti()
            elif opcao == 2:
                equipment.Intelbras()
            else:
                exit()

if __name__ == '__main__':
    app = Application()
