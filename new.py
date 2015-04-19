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
import tempfile
import urllib.request

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

def verbose(message, verbose_lvl, req_lvl):
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

def pattern_time_format(val):
    pattern = re.sub('[^%YymdHMS]', '.', val)
    pattern = re.sub('%[ymdHMS]', '([0-9]{2})', pattern)
    pattern = re.sub('%[Y]', '([0-9]{4})', pattern)
    return pattern

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

def check_max(settings, constants):
    """Fce 'check_max' kontroluje, zdali specifikovaná hodnota je buď číslo, nebo 'max", nebo 'auto'."""
    if settings["max_val"] not in [ "max", "auto" ]:
        if is_number(settings["max_val"]):
            settings["max_val"] = float(settings["max_val"])
        else:
            soft_error("WARNING: 'max_val' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["max_val"] = constants["max_val"]
    return settings["max_val"]
        

def check_min(settings, constants):
    """Fce 'check_min' kontroluje, zdali specifikovaná hodnota je buď číslo, nebo 'min", nebo 'auto'."""
    if settings["min_val"] not in [ "min", "auto" ]:
        if is_number(settings["min_val"]):
            settings["min_val"] = float(settings["min_val"])
        else:
            soft_error("WARNING: 'min_val' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["min_val"] = constants["min_val"]
    return settings["min_val"]
        

def check_max_time(settings, constants):
    """Fce 'check_max_time' kontroluje hodnotu 'max_time' a převádí ji na vteřiny."""
    if settings["max_time"] in [ "max", "auto" ]:
        return settings["max_time"]
    else:
        pattern = pattern_time_format(settings["time_format"])
        if not re.compile("^" + pattern + "$").match(settings["max_time"]):
            soft_error("WARNING: 'max_time' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["max_time"] = constants["max_time"]
            return settings["max_time"]
        settings["max_time"] = datetime.strptime(settings["max_time"], settings["time_format"]).strftime('%s')
    return settings["max_time"]

def check_min_time(settings, constants):
    """Fce 'check_min_time' kontroluje hodnotu 'min_time' a převádí ji na vteřiny."""
    if settings["min_time"] in [ "min", "auto" ]:
        return settings["min_time"]
    else:
        pattern = pattern_time_format(settings["time_format"])
        if not re.compile("^" + pattern + "$").match(settings["min_time"]):
            soft_error("WARNING: 'min_time' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["min_time"] = constants["min_time"]
            return settings["min_time"]
        settings["min_time"] = datetime.strptime(settings["min_time"], settings["time_format"]).strftime('%s')
    return settings["min_time"]

def check_time(settings, constants):
    if not is_number(settings["time"]):
        soft_error("WARNING: 'time' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
        settings["time"] = None
        if not settings["fps"]:
            verbose(" - Using default value for 'fps'.", settings["verbose"], 1)
            settings["fps"] = constants["fps"]
        if not settings["speed"]:
            verbose(" - Using default value for 'speed'.", settings["verbose"], 1)
            settings["speed"] = constants["speed"]
    return settings

def check_speed(settings, constants):
    if not is_number(settings["speed"]):
        soft_error("WARNING: 'speed' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default value.", settings["verbose"], 1)
        settings["speed"] = constants["speed"]
    return settings["speed"]

def check_fps(settings, constants):
    if not is_number(settings["fps"]):
        soft_error("WARNING: 'fps' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default value.", settings["verbose"], 1)
        settings["fps"] = constants["fps"]
    return settings["fps"]

def check_legend(val):
    if val.strip() == "":
        soft_error("WARNING: 'legend' is an empty string.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Removing.", settings["verbose"], 1)
        val = None
    return val

def check_name(val, constants):
    if val.strip() == "":
        soft_error("WARNING: 'name' is an empty string.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using script name.", settings["verbose"], 1)
        val = constants
    return val

def check_gnuplot(val):
    """Fce 'check_gnuplot' kontroluje zadané parametry pro 'gnuplot'."""
    return val

def check_effect(settings, constants):
    """Fce 'check_effect' kontroluje zadané parametry pro efekt."""
    params = ':'.join(settings["effect"]).split(":")
    for param in params:
        tmp = param.split("=")
        if len(tmp) != 2:
            soft_error("WARNING: wrong effect parameter: {}.".format(param), settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Skipping.", settings["verbose"], 1)
            continue
        directive = tmp[0].lower()
        value = tmp[1].lower()
        if directive == "delay":
            if not value.isdigit():
                soft_error("WARNING: wrong effect parameter: delay has to be integer.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["delay"] = constants["delay"]
            else:
                settings["delay"] = int(value)
        elif directive == "columns":
            if not value.isdigit():
                soft_error("WARNING: wrong effect parameter: columns has to be an integer bigger than 1.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Correct value will be computed automatically.", settings["verbose"], 1)
            else:
                settings["columns"] = int(value)
        elif directive == "multiplot":
            if value not in [ "off", "on" ]:
                soft_error("WARNING: wrong effect parameter: multiplot has to be set to 'on' or 'off'.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["multiplot"] = constants["multiplot"]
            else:
                settings["multiplot"] = value
        elif directive == "border":
            if value not in [ "off", "on" ]:
                soft_error("WARNING: wrong effect parameter: border has to be set to 'on' or 'off'.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["border"] = constants["border"]
            else:
                settings["border"] = value
        elif directive == "color":
            p = subprocess.Popen("gnuplot", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = p.communicate( b"show colornames" )
            colors = re.findall("\\\\n[ ]*([^\\\\ ']+)", str(error))
            for c in value.split(','):
                if c not in colors:
                    soft_error("WARNING: wrong effect parameter: unknown color '{}'.".format(c), settings["verbose"], 1, settings["ignore_error"])
                    verbose(" - Skipping.", settings["verbose"], 1)
                else:
                    if "colors" not in settings:
                        settings["colors"] = []
                    settings["colors"].append(c)

            if "colors" not in settings:
                settings["colors"] = colors
        elif directive == "transparent":
            if is_number(value):
                if float(value) <= 0 and float(value) > 1:
                    soft_error("WARNING: wrong effect parameter: transparent has to be in range (0;1>.", settings["verbose"], 1, settings["ignore_error"])
                    verbose(" - Using default value.", settings["verbose"], 1)
                    settings["transparent"] = constants["transparent"]
                else:
                    settings["transparent"] = float(value)
            else:
                soft_error("WARNING: wrong effect parameter: transparent has to be a number in range (0;1>.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["transparent"] = constants["transparent"]
        elif directive == "method":
            if value not in [ "average", "top" ]:
                soft_error("WARNING: wrong effect parameter: method has to be set to 'average' or 'top'.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["method"] = constants["method"]
            else:
                settings["method"] = value
        elif directive == "width":
            if is_number(value):
                if float(value) <= 0 and float(value) > 1:
                    soft_error("WARNING: wrong effect parameter: width has to be in range (0;1>.", settings["verbose"], 1, settings["ignore_error"])
                    verbose(" - Using default value.", settings["verbose"], 1)
                    settings["width"] = constants["width"]
                else:
                    settings["width"] = float(value)
            else:
                soft_error("WARNING: wrong effect parameter: width has to be a number in range (0;1>.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["width"] = constants["width"]
        elif directive == "steps":
            if not value.isdigit():
                soft_error("WARNING: wrong effect parameter: steps has to be an integer and bigger than 1.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["steps"] = constants["steps"]
            else:
                settings["steps"] = int(value)
        else:
            soft_error("WARNING: unknown effect parameter: {}".format(directive), settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Skipping.", settings["verbose"], 1)

    return settings

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
    if "http" in val:
        return val
    else:
        return check_pathname(val)

def load_config(settings):
    """Fce, která načítá data z config souboru."""
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

    constants = {
        "time_format": "[%Y-%m-%d %H:%M:%S]",
        "columns": 60,
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
        "method": "average",
        "transparent": 0.65,
        "width": 1,
        "steps": 200
    }

    settings = {
        "border": constants["border"],
        "transparent": constants["transparent"],
        "delay": constants["delay"],
        "method": constants["method"],
        "width": constants["width"],
        "columns": constants["columns"],
        "multiplot": constants["multiplot"],
        "steps": constants["steps"],
        "verbose": constants["verbose"]
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
    parser.add_argument('input', type=check_file, action='append', nargs='+')

    args = parser.parse_args()

    user = vars(args)

    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "speed", "time", "fps", "legend", "gnuplot", "effect", "config", "name", "ignore_error", "verbose", "input"]:
        settings[key] = user[key]

    if settings["config"]:
        settings = load_config(settings)

    if settings["speed"] and settings["time"] and settings["fps"] and not float(settings["speed"]) * float(settings["fps"]) == float(settings["time"]):
        soft_error("WARNING: Mutually exclusive arguments defined. (-S speed, -T time, -F fps)", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default values.", settings["verbose"], 1)
        settings["speed"] = constants["speed"]
        settings["time"] = None
        settings["fps"] = constants["fps"]

    if settings["time"] and not settings["fps"] and not settings["speed"]:
        settings["fps"] = constants["fps"]
    elif not settings["time"] and settings["fps"] and not settings["speed"]:
        settings["speed"] = constants["speed"]
    elif not settings["time"] and not settings["fps"] and settings["speed"]:
        settings["fps"] = constants["fps"]
    elif not settings["time"] and not settings["fps"] and not settings["speed"]:
        settings["fps"] = constants["fps"]
        settings["speed"] = constants["speed"]

    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "name", "ignore_error", "verbose" ]:
        if not settings[key]:
            settings[key] = constants[key]

    check_time_format(settings["time_format"])
    settings["min_val"] = check_min(settings, constants)
    settings["max_val"] = check_max(settings, constants)
    settings["max_time"] = check_max_time(settings, constants)
    settings["min_time"] = check_min_time(settings, constants)

    if settings["time"]:
        settings = check_time(settings, constants)

    if settings["fps"]:
        settings["fps"] = check_fps(settings, constants)

    if settings["speed"]:
        settings["speed"] = check_speed(settings, constants)

    if settings["legend"]:
        settings["legend"] = check_legend(settings["legend"])

    if settings["gnuplot"]:
        settings["gnuplot"] = check_gnuplot(settings["gnuplot"])

    if settings["effect"]:
        settings["effect"] = check_effect(settings, constants)

    settings["name"] = check_name(settings["name"], constants["name"])

    if settings["max_val"] not in [ "auto", "max" ] and settings["min_val"] not in [ "auto", "min" ] and settings["max_val"] <= settings["min_val"]:
        soft_error("WARNING: 'max_val' has to be bigger than 'min_val", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default values.", settings["verbose"], 1)
        settings["max_val"] = constants["max_val"]
        settings["min_val"] = constants["min_val"]

    if settings["max_time"] not in [ "auto", "max" ] and settings["min_time"] not in [ "auto", "min" ] and settings["max_time"] <= settings["min_time"]:
        soft_error("WARNING: 'max_time' has to be bigger than 'min_time", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default values.", settings["verbose"], 1)
        settings["max_time"] = constants["max_time"]
        settings["min_val"] = constants["min_time"]

    if debug:
        print("DEBUG: arguments: {}".format(settings))

    for input_file in settings["input"][0]:
        if "http" in input_file:
            file_name = input_file[input_file.rfind("/"):]
            verbose("Downloading file '{}'".format(input_file), settings["verbose"], 2)
            with urllib.request.urlopen(input_file) as i_file:
                for i, line in enumerate(i_file):
                    print(line)
        else:
            print(input_file)


    """with tempfile.TemporaryFile() as tmp_file:"""

