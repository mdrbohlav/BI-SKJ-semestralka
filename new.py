#!/usr/bin/env python3
# -*- coding: utf-8 -*-

debug = True

import os
import sys
import subprocess
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime
import re

def soft_error(message, req_lvl = 1, verbose_lvl = 1, ignore_error = True):
    """Fce 'soft_error' vytiskne na stderr chybovou hlášku a pokud se neignorují chyby, tak ukončí skript, pokud se chyby ignorují, vypíše pouze varování."""
    if ignore_error:
        verbose(message, verbose_lvl, req_lvl)
    else:
        print(message, file = sys.stderr)
        print("Stopping script.")
        sys.exit(1)

def error(message):
    """Fce 'error' vytiskne hlášku na stderr, vždy ukončí skript, používá se pro chyby, které nelze ignorovat."""
    print("ERROR: " + message, file = sys.stderr)
    print("Stopping script.")
    sys.exit(1)

def verbose(message, req_lvl, verbose_lvl):
    """Fce 'verbose' vytiskne hlášku na 'stderr' v závislosti na nastavení 'verbose_lvl'."""
    if verbose_lvl == req_lvl:
        print(message, file = sys.stderr)

def is_number(val):
  """Fce 'is_number' kontroluje, zdali je 'val' číslo."""
  try:
    num = float(val)
    return True
  except ValueError:
    return False

def check_time_format(val):
    """Fce 'check_time_format' kontroluje formát času."""
    correct = False
    for option in [ "%d", "%H", "%m", "%M", "%S", "%y", "%Y" ]:
        if option in val:
            correct = True
            break

    if not correct:
        message = "Wrong time format. It has to be in 'strftime(3c)'."
        error(message)

    tmp = re.sub('%', ' %', re.sub('[^%YymdHMS ]', ' ', val))
    occurences = {}
    for i in tmp.split(" "):
        if (i == ""):
            continue
        if i in occurences:
            message = "time format: '{}'' used more than once.".format(i)
            error(message)
        else:
            occurences[i] = 1

    if "%Y" in occurences and "%y" in occurences:
        message = "time format: options '%Y' and '%y' are mutually exclusive."
        error(message)

def check_max(val, from_file = False):
    """Fce 'check_max' kontroluje, zdali specifikovaná hodnota je buď číslo, nebo 'max", nebo 'auto'."""
    if val == "auto" or val == "max": 
        return val
    elif is_number(val):
        return float(val)
    else:
        message = "'" + val + "' is an invalid choice, see help for more info"
        error(message)

def check_min(val, from_file = False):
    """Fce 'check_min' kontroluje, zdali specifikovaná hodnota je buď číslo, nebo 'min", nebo 'auto'."""
    if val == "auto" or val == "min":
        return val
    elif is_number(val):
        return float(val)
    else:
        message = "'" + val + "' is invalid choice"
        error(message)

def check_max_time(val, from_file = False):
    """Fce 'check_gnuplot' kontroluje zadané parametry pro 'gnuplot'."""
    return 1

def check_min_time(val, from_file = False):
    """Fce 'check_effect' kontroluje zadané parametry pro efekt."""
    return 1

def check_gnuplot(val, from_file = False):
    """Fce 'check_gnuplot' kontroluje zadané parametry pro 'gnuplot'."""
    return 1

def check_effect(val, from_file = False):
    """Fce 'check_effect' kontroluje zadané parametry pro efekt."""
    return 1

def check_pathname(val):
    """Fce 'check_pathname' kontroluje, zdali zadaný soubor existuje a má práva pro čtení."""
    try:
        abs_path = os.path.abspath(val)
        if not os.path.isfile(abs_path):
            message = "File '" + val + "' is missing."
            raise ArgumentTypeError(message)
        elif not os.access(abs_path, os.R_OK):
            message = "File '" + "' is not readable."
            raise ArgumentTypeError(message)
        else:
            return abs_path
    except ValueError:
        message = "Invalid file name."
        raise ArgumentTypeError(message)

def check_file(val):
    return 1

def load_config(settings):
    with open(settings["config"], 'r', encoding='utf-8') as configFile:
        for line in list(reversed(list(enumerate(configFile)))):
            i = line[0]
            line = line[1]
            commentStart = line.find("#");
            uncommentedLine = line[0 : commentStart].strip().replace('\t', ' ')
            if (uncommentedLine == ""):
                continue
            lineArray = uncommentedLine.split(' ', 1)
            directive = lineArray[0].lower()
            value = "" if len(lineArray) < 2 else lineArray[1].strip()
            if value == "":
                soft_error("WARNING: Config file: row #{} has specified directive but no value.".format(i+1), settings["verbose"], 1, settings["ignore_error"])
                continue
            if directive == "timeformat":
                if settings["time_format"]:
                    continue
                settings["time_format"] = value
            elif directive == "ymax":
                if settings["max_val"]:
                    continue
                settings["max_val"] = value
            elif directive == "ymin":
                if settings["min_val"]:
                    continue
                settings["min_val"] = value
            elif directive == "xmax":
                if settings["max_time"]:
                    continue
                settings["max_time"] = value
            elif directive == "xmin":
                if settings["min_time"]:
                    continue
                settings["min_time"] = value
            elif directive == "speed":
                if settings["speed"]:
                    continue
                settings["speed"] = value
            elif directive == "time":
                if settings["time"]:
                    continue
                settings["time"] = value
            elif directive == "fps":
                if settings["fps"]:
                    continue
                settings["fps"] = value
            elif directive == "legend":
                if settings["legend"]:
                    continue
                settings["legend"] = value
            elif directive == "gnuplotparams":
                if not settings["gnuplot"]:
                    settings["gnuplot"] = []
                settings["gnuplot"].append(value)
            elif directive == "effectparams":
                if not settings["effect"]:
                    settings["effect"] = []
                settings["effect"].append(value)
            elif directive == "name":
                if settings["name"]:
                    continue
                settings["name"] = value
            elif directive == "ignoreerrors":
                if settings["ignore_error"]:
                    continue
                settings["ignore_error"] = True if value.lower() == "true" else False
            elif directive == "verbose":
                if settings["verbose"]:
                    continue
                settings["verbose"] = value
            else:
                soft_error("WARNING: Config file: row #{} contains unknown directive.".format(i+1), settings["verbose"], 1, settings["ignore_error"])

    return settings

if __name__ == '__main__':
    executables = [ "ffmpeg", "gnuplot" , "wget" ]

    for prg in executables:
        try:
            f_null = open(os.devnull, 'w')
            subprocess.Popen([prg, "--help"], stdout=f_null, stderr=f_null)
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                print("ERROR: '" + prg + "' is not installed")
                sys.exit()
            else:
                print("ERROR: something went wrong when running '" + prg + "'")
                sys.exit()

    if debug:
        print("DEBUG: All required executables are installed")

    constants = {
        "time_format": "[%Y-%m-%d %H:%M:%S]",
        "col_num": 60,
        "speed": 1,
        "fps": 25,
        "name": "new",
        "delay": 10,
        "verbose": 0,
        "ignore_error": False,
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

    if debug:
        print("DEBUG: Default settings: {}".format(constants))

    settings = {
        "border": constants["border"],
        "transparent": constants["transparent"],
        "delay": constants["delay"],
        "method": constants["method"],
        "width": constants["width"],
        "columns": "",
        "multiplot": constants["multiplot"],
        "steps": constants["steps"]
    }

    parser = ArgumentParser(description="Under construction...", epilog="Thank you for reading this.")
    parser.add_argument('--version', action='version', version='1.0')
    parser.add_argument('-t', dest='time_format')
    parser.add_argument('-Y', dest='max_val')
    parser.add_argument('-y', dest='min_val')
    parser.add_argument('-X', dest='max_time')
    parser.add_argument('-x', dest='min_time')
    parser.add_argument('-S', dest='speed')
    parser.add_argument('-T', dest='time')
    parser.add_argument('-F', dest='fps')
    parser.add_argument('-l', dest='legend')
    parser.add_argument('-g', dest='gnuplot', action='append')
    parser.add_argument('-e', dest='effect', action='append')
    parser.add_argument('-f', dest='config', type=check_pathname)
    parser.add_argument('-n', dest='name')
    parser.add_argument('-E', dest='ignore_error', action='store_true')
    parser.add_argument('-v', dest='verbose', action='count')
    parser.add_argument('input', type=check_pathname, action='append')

    args = parser.parse_args()

    user = vars(args)

    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "speed", "time", "fps", "legend", "gnuplot", "effect", "config", "name", "ignore_error", "verbose", "input"]:
        settings[key] = user[key]

    settings = load_config(settings)

    if settings["speed"] and settings["time"] and settings["fps"]:
        soft_error("WARNING: Mutually exclusive arguments defined. (-S speed, -T time, -f fps)", settings["verbose"], 1, settings["ignore_error"])
        verbose("WARNING: Using default values.", settings["verbose"], 1)
        settings["speed"] = constants["speed"]
        settings["time"] = None
        settings["fps"] = constants["fps"]

    if not (settings["speed"] or settings["fps"]) or \
        not (settings["speed"] or settings["time"]) or \
        not (settings["fps"] or settings["time"]):
        if settings["time"]:
            settings["fps"] = constants["fps"]
        else:
            settings["fps"] = constants["fps"] if not settings["fps"] else settings["fps"]
            settings["speed"] = constants["speed"] if not settings["speed"] else settings["speed"]

    if debug:
        print("DEBUG: arguments: {}".format(settings))



