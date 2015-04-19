#!/usr/bin/env python3
# -*- coding: utf-8 -*-

debug = True

import os
import sys
import subprocess
from argparse import ArgumentParser

#funkce soft_err vytiskne na stderr chybovou hlášku a pokud se neignorují chyby
#tak ukončí skript, pokud se chyby ignorují, vypíše pouze varování
def soft_err(message, err = None, ignore_err = True, verbose_lvl = 1, req_lvl = 1):
    if ignore_err:
        verbose(message, verbose_lvl, req_lvl)
    else:
        print("ERROR: " + message, file = sys.stderr)
        sys.exit(err)

#funkce err vytiskne hlášku na stderr
#funkce err vždy ukončí skript, používá se pro chyby, které nelze ignorovat
def err(message, err):
    print("ERROR: " + message, file = sys.stderr)
    sys.exit(err)

#funkce vytiskne hlášku na stderr v závislosti na nastavení verbose_lvl
def verbose(message, verbose_lvl, req_lvl):
    if verbose_lvl == req_lvl:
        print(message, file = sys.stderr)

if __name__ == '__main__':
    constants = {
        "time_format": "[%Y-%m-%d %H:%M:%S]",
        "col_num": 60,
        "speed": 1,
        "fps": 25,
        "name": "test",
        "delay": 10,
        "verbose": 2,
        "error": 0,
        "multiplot": "off",
        "min_val": "auto",
        "max_val": "auto",
        "min_time": "min",
        "max_time": "max",
        "border": "",
        "method": "avarge",
        "transparent": 0.65,
        "width": 1,
        "steps": 200
    }

    executables = [ "ffmpeg", "gnuplot" , "wget" ]

    for prg in executables:
        try:
            FNULL = open(os.devnull, 'w')
            subprocess.Popen([prg, "--help"], stdout=FNULL, stderr=FNULL)
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                print("ERROR: '" + prg + "' is not installed")
                sys.exit()
            else:
                print("ERROR: something went wrong when running '" + prg + "'")
                sys.exit()

    if debug:
        print("DEBUG: All required executables are installed")

    default = {
        "error": constants["error"],
        "verbose": constants["verbose"],
        "border": constants["border"],
        "transparent": constants["transparent"],
        "delay": constants["delay"],
        "method": constants["method"],
        "width": constants["width"],
        "columns": "",
        "time_format": constants["time_format"],
        "min_val": constants["min_val"],
        "max_val": constants["max_val"],
        "min_time": constants["min_time"],
        "max_time": constants["max_time"],
        "name": constants["name"],
        "multiplot": constants["multiplot"],
        "steps": constants["steps"]
    }

    if debug:
        print("DEBUG: Default settings: {}".format(default))

    parser = ArgumentParser()
    parser.add_argument('--version', action='version', version='1.0')




