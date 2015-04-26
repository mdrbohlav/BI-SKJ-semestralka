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
from urllib.error import URLError, HTTPError
import math
import random

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

def percentage_done(done, total):
    percent = done/total*100
    print("{0:3d} % done \r".format(int(percent)), end="")

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
    if settings["max_time"] not in [ "max", "auto" ]:
        pattern = pattern_time_format(settings["time_format"])
        if not re.compile("^" + pattern + "$").match(settings["max_time"]):
            soft_error("WARNING: 'max_time' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["max_time"] = constants["max_time"]
        else:
            try:
                settings["max_time"] = int(datetime.strptime(settings["max_time"], settings["time_format"]).strftime('%s')) + int(datetime.today().strftime('%s')) - int(datetime.utcnow().strftime('%s'))
            except ValueError:
                soft_error("WARNING: 'max_time' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["max_time"] = constants["max_time"]
    return settings["max_time"]

def check_min_time(settings, constants):
    """Fce 'check_min_time' kontroluje hodnotu 'min_time' a převádí ji na vteřiny."""
    if settings["min_time"] not in [ "min", "auto" ]:
        pattern = pattern_time_format(settings["time_format"])
        if not re.compile("^" + pattern + "$").match(settings["min_time"]):
            soft_error("WARNING: 'min_time' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["min_time"] = constants["min_time"]
        else:
            try:
                settings["min_time"] = int(datetime.strptime(settings["min_time"], settings["time_format"]).strftime('%s')) + int(datetime.today().strftime('%s')) - int(datetime.utcnow().strftime('%s'))
            except ValueError:
                soft_error("WARNING: 'min_time' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["min_time"] = constants["min_time"]
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
                if value == "on":
                    settings["border"] = "bo"
        elif directive == "color":
            for c in value.split(','):
                if c not in constants["colors"]:
                    soft_error("WARNING: wrong effect parameter: unknown color '{}'.".format(c), settings["verbose"], 1, settings["ignore_error"])
                    verbose(" - Skipping.", settings["verbose"], 1)
                else:
                    if "colors" not in settings:
                        settings["colors"] = []
                    settings["colors"].append(c)
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
    """Fce, která se podívá, jestli se má soubor stáhnout, pokud ne, tak ho zkontroluje"""
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
                settings["speed"] = float(value)
            elif directive == "time":
                if settings["time"]:
                    continue
                settings["time"] = float(value)
            elif directive == "fps":
                if settings["fps"]:
                    continue
                settings["fps"] = float(value)
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

def load_data_file(i_file):
    data = []
    for i, line in enumerate(i_file):
        decodedLine = re.sub("\n", "", line.decode("utf-8"))
        data.append(decodedLine.strip())
    if len(data) == 0:
        del data
        return None
    return data

def check_data_line(time, value, time_format):
    """Fce, která zkontroluje vstupní data (čas a hodnotu)"""
    pattern = pattern_time_format(settings["time_format"])
    if not re.compile("^" + pattern + "$").match(time):
        return 1
    elif not is_number(value):
        return 2
    return 0

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
        "max_columns": 40,
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
        "steps": 200,
        "colors": [ "web-green", "black", "dark-grey", "red", "web-blue", "dark-magenta", "dark-cyan", "dark-orange", "dark-yellow", "royalblue", "goldenrod", "dark-spring-green", "purple", "steelblue", "dark-red", "dark-chartreuse", "orchid", "aquamarine", "brown", "yellow", "turquoise", "grey0", "grey10", "grey20", "grey30", "grey40", "grey50", "grey60", "grey70", "grey", "grey80", "grey90", "grey100", "light-red", "light-green", "light-blue", "light-magenta", "light-cyan", "light-goldenrod", "light-pink", "light-turquoise", "gold", "green", "dark-green", "spring-green", "forest-green", "sea-green", "blue", "dark-blue", "midnight-blue", "navy", "medium-blue", "skyblue", "cyan", "magenta", "dark-turquoise", "dark-pink", "coral", "light-coral", "orange-red", "salmon", "dark-salmon", "khaki", "dark-khaki", "dark-goldenrod", "beige", "olive", "orange", "violet", "dark-violet", "plum", "dark-plum", "dark-olivegreen", "orangered4", "brown4", "sienna4", "orchid4", "mediumpurple3", "slateblue1", "yellow4", "sienna1", "tan1", "sandybrown", "light-salmon", "pink", "khaki1", "lemonchiffon", "bisque", "honeydew", "slategrey", "seagreen", "antiquewhite", "chartreuse", "greenyellow", "white", "gray", "light-gray", "light-grey", "dark-gray", "slategray", "gray0", "gray10", "gray20", "gray30", "gray40", "gray50", "gray60", "gray70", "gray80", "gray90", "gray100" ]
    }

    settings = {
        "border": constants["border"],
        "transparent": constants["transparent"],
        "delay": constants["delay"],
        "method": constants["method"],
        "width": constants["width"],
        "columns": None,
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

    "Zkopírování argumentů do dict settings"
    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "speed", "time", "fps", "legend", "gnuplot", "effect", "config", "name", "ignore_error", "verbose", "input"]:
        settings[key] = user[key]

    "Pokud je zadaný config soubor, tak ho načteme"
    if settings["config"]:
        settings = load_config(settings)

    "Pokud zadané hodnoty 'speed', 'time' a 'fps', které navzájem nesedí, použijeme defaultní hodnoty"
    if settings["speed"] and settings["time"] and settings["fps"] and not float(settings["speed"]) * float(settings["fps"]) == float(settings["time"]):
        soft_error("WARNING: Mutually exclusive arguments defined. (-S speed, -T time, -F fps)", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default values.", settings["verbose"], 1)
        settings["speed"] = constants["speed"]
        settings["time"] = None
        settings["fps"] = constants["fps"]

    "Pokud zadána pouze jedna hodnota z 'speed', 'time' a 'fps', nastaví se druhá podle defaultních hodnot"
    if settings["time"] and not settings["fps"] and not settings["speed"]:
        settings["fps"] = constants["fps"]
    elif not settings["time"] and settings["fps"] and not settings["speed"]:
        settings["speed"] = constants["speed"]
    elif not settings["time"] and not settings["fps"] and settings["speed"]:
        settings["fps"] = constants["fps"]
    elif not settings["time"] and not settings["fps"] and not settings["speed"]:
        settings["fps"] = constants["fps"]
        settings["speed"] = constants["speed"]

    "Pokud jedna ze zmíněných hodnot nebyla nastavena uživatelem, použijeme defaultní hodnotu"
    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "name", "ignore_error", "verbose" ]:
        if not settings[key]:
            settings[key] = constants[key]

    "Kontrolu načtených hodnot"
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

    "Načtení dat ze souborů"
    data = {}
    for input_file in settings["input"][0]:
        if "http" in input_file:
            "Všechny soubory začínající na 'http' se načítají z internetu"
            file_name = input_file[input_file.rfind("/"):]
            verbose("Downloading file '{}'".format(input_file), settings["verbose"], 2)
            try:
                with urllib.request.urlopen(input_file) as i_file:
                    data[input_file] = load_data_file(i_file)
                        
            except HTTPError as e:
                soft_error("ERROR: The server couldn\'t fulfill the request.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - error code: {}".format(e.code), settings["verbose"], 1)
            except URLError as e:
                soft_error("ERROR: We failed to reach a server.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - reason: {}".format(e.code), settings["verbose"], 1)
        else:
            verbose("Opening file '{}'".format(input_file), settings["verbose"], 2)
            with open(input_file, mode='rb') as i_file:
                data[input_file] = load_data_file(i_file)

    if len(data) == 0:
        error("No input data were loaded.")

    verbose("Validating input files data...", settings["verbose"], 2)

    suitable_data = []

    "Kontrola dat ze vstupních souborů, zdali je čas ve správném formátu a pořadí a hodnoty jsou číselné"
    for index_file, i_file in enumerate(data):
        lines = len(data[i_file])
        prev = 0
        suitable_data.append("")
        for index_line, line in enumerate(data[i_file]):
            if line == "":
                continue
            delim = line.rfind(" ")
            time = line[:delim].strip()
            value = line[delim+1:]
            
            "Pokud nastala chyba, 1 pro chybu v čase, 2 pro chybu v hodnotě"
            res = check_data_line(time, value, settings["time_format"])
            if res == 1:
                soft_error("WARNING: file '{}':\n - line #{}: wrong time format.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                verbose(" - skipping".format(e.code), settings["verbose"], 1)
            elif res == 2:
                soft_error("WARNING: file '{}':\n - line #{}: wrong value.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                verbose(" - skipping".format(e.code), settings["verbose"], 1)

            "Kontrola dalších chyb v datu (13. měsíc apod.)"
            try:
                time = int(datetime.strptime(time, settings["time_format"]).strftime('%s')) + int(datetime.today().strftime('%s')) - int(datetime.utcnow().strftime('%s'))
            except ValueError:
                soft_error("WARNING: file '{}':\n - line #{}: wrong date.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                verbose(" - skipping", settings["verbose"], 1)
                continue
            
            "Pokud čas na aktuálním řádku mimo požadovaný rozsah, pokračuje se dál"
            if settings["min_time"] not in ["min", "auto"] and time < settings["min_time"]:
                continue
            elif settings["max_time"] not in ["max", "auto"] and time > settings["max_time"]:
                continue

            size = len(suitable_data)
            "Pokud se nejedná o první řádek ze souboru, tak testujeme pořadí datumů"
            if index_line == 0:
                suitable_data[size-1] = "{} {}".format(time, value)
            else:
                if time - prev <= 0:
                    soft_error("WARNING: file '{}':\n - line #{}: wrong order of the input data.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                    verbose(" - skipping", settings["verbose"], 1)
                    continue
                suitable_data[size-1] = suitable_data[size-1] + "\n{} {}".format(time, value)
            prev = time
        
        if suitable_data[len(suitable_data)-1] == "":
            soft_error("WARNING: file '{}':\n - no suitable data found.".format(i_file), settings["verbose"], 1, settings["ignore_error"])
            del suitable_data[len(suitable_data)-1]

    if len(suitable_data) == 0:
        error("ERROR: No suitable data found in any of the input files.")

    "Bubble sortem seřadíme jednotlivé vstupní soubory podle prvního datumu vzestupně"
    for index_file in range(len(suitable_data)-1, 0, -1):
        for i in range(index_file):
            time = suitable_data[i].split()[0]
            timeNext = suitable_data[i+1].split()[0]
            if time > timeNext:
                tmp = suitable_data[i]
                suitable_data[i] = suitable_data[i+1]
                suitable_data[i+1] = tmp

    "Zjistíme, zdali se rozsahy datumů v jednolivých souborech překrývají"
    overlaping = False
    for index, i_data in enumerate(suitable_data):
        if index == 0:
            continue
        prevEnd = suitable_data[index-1].split()[-2:-1][0]
        start = suitable_data[index].split()[0]
        if start <= prevEnd:
            overlaping = True
            break

    if settings["multiplot"] == "on":
        verbose("Multiplot set to 'on'. One graph for each input file will be generated.", settings["verbose"], 1)
        """Pro každý soubor zvlášť"""
        """Spočítat columns, distance"""
    elif not overlaping:
        verbose("One curve for all input files in one graph will be generated.", settings["verbose"], 1)
        joinedData = ""

        "Datumy se nepřekrývají, spojíme je do jednoho grafu"
        for index, i_data in enumerate(suitable_data):
            joinedData += "\n" + i_data if index > 0 else i_data
        
        "Pokud uživatel nezadal 'columns', vypočítáme nějakou schůdnou hodnotu"
        if not settings["columns"]:
            tmp = math.ceil((joinedData.count("\n")+1)/2) 
            print(tmp)
            settings["columns"] = tmp if tmp <= constants["max_columns"] else constants["max_columns"]

        "Najdeme minimální a maximální hodnotu mezi datumy."
        xmax = int(joinedData.split()[-2:-1][0])
        xmin = int(joinedData.split()[0])

        "Spočítáme dobu mezi jednotlivými záznamy, po které budeme tisknout bod do grafu."
        distance = (xmax-xmin) / settings["columns"]

        print(distance)

        out = ""
        lines = joinedData.split("\n")
        col_num = 1
        count = 0
        height = 0
        ymax = None
        ymin = None
        start = None
        for index_line, i_line in enumerate(lines):
            time, value = i_line.split()
            time = int(time)
            value = float(value)
            if index_line == 0:
                start = time
            count += 1

            if (start + col_num * distance) < time or start == time:
                if settings["method"] == "average":
                    height += value
                else:
                    height = value if math.fabs(value) > math.fabs(height) else height
                continue

            if settings["method"] == "average":
                height = height / (count-1)

            if col_num == 1:
                ymax = height
                ymin = height
            else:
                ymax = height if height > ymax else ymax
                ymin = height if height < ymin else ymin

            tmp = start + distance * col_num - distance / 2
            out += "{} {}\n".format(tmp, height)

            height = value
            count = 1
            col_num += 1

            while start + col_num * distance < time:
                col_num += 1

        "Pokud jsme končili uprostřed rozsahu jednoho zápisu do grafu, musíme přidat i poslední záznam, který byl přeskočen."
        if start + col_num * distance < time:
            if settings["method"] == "average":
                height = height / (count-1)
            ymax = height if height > ymax else ymax
            ymin = height if height < ymin else ymin
            tmp = start + distance * col_num - distance / 2
            out += "{} {}".format(tmp, height)

        "Kontrola hodnot, zdali jsou v zadaném rozsahu"
        if settings["min_val"] not in ["min", "auto"]:
            if ymax < settings["min_val"]:
                soft_error("WARNING: 'y_min' out of range.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - 'y_min' not set", settings["verbose"], 1)
            else:
                ymin = settings["min_val"]

        if settings["max_val"] not in ["max", "auto"]:
            if ymin > settings["max_val"]:
                soft_error("WARNING: 'y_max' out of range.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - 'y_max' not set", settings["verbose"], 1)
            else:
                ymax = settings["max_val"]

        "Skok, o který se má posunout tečka v každém kroku."
        jump = (ymax - ymin) / settings["steps"]

        "Pokud není nastavena maximální/minimální hodnota, upraví se 'ymax'/'ymin', aby byla nahoře/dole mezera."
        if settings["max_val"] == "max":
            ymax = 0 if ymax <= 0 and ymax + 20 * jump > 0 else ymax + 20 * jump
        if settings["min_val"] == "min":
            ymin = 0 if ymin >= 0 and ymin - 20 * jump < 0 else ymin - 20 * jump

        "Spočítáme, kolik obrázků bude potřeba pro dokončení každého sloupce a uložíme si nejvyšší hodnotu."
        frames = None
        tmp_min = ymin if ymin > 0 else ymax if ymax < 0 else 0
        for index, line in enumerate(out):
            time, value = i_line.split()
            value = float(value)

            tmp_val = (value - tmp_min) / jump if (value - tmp_min) / jump >= 0 else -(value - tmp_min) / jump
            tmp_val += index * settings["delay"]
            if not frames or tmp_val > frames:
                frames = tmp_val

        if not settings["speed"]:
            settings["speed"] = round(frames / (settings["time"] * settings["fps"]), 2)
        if not settings["fps"]:
            settings["fps"] = round(frames / (settings["speed"] * settings["time"]), 2)

        "max_frames udává počet kroků pro  zvolený 'speed', pokud 'frames' není jeho násobkem ,je potřeba upravit"
        max_frames = frames if int(frames / settings["speed"]) == frames / settings["speed"] else int(frames + settings["speed"])

        digits = len(str(max_frames))

        yrange = ""
        if settings["min_val"] != "auto":
            yrange = "{}:".format(ymin)
        if settings["max_val"] != "auto":
            yrange += ":{}".format(ymax) if yrange == "" else "{}".format(ymax)

        "Nastavení popisků na ose x."
        xtics = ""
        tmp = xmin + (xmax-xmin) // 20
        while tmp < xmax:
            xtics += "'{:2d}:{:02d}:{:02d}' {:d},".format((tmp//60//60) % 24, (tmp//60) % 60, tmp % 60, tmp)
            tmp += (xmax - xmin) // 10

        general_gnuplot = 'set term png truecolor\n\
                           set key off\n\
                           set xrange ["{xmin}":"{xmax}"] noreverse nowriteback\n\
                           set yrange [{yrange}] noreverse nowriteback\n\
                           set style fill transparent solid {transparent} {border}\n\
                           set xtics rotate by -45 scale 1 font ",10" ({xtics})\n'\
                           .format(xmin = xmin, xmax = xmax, yrange = yrange, transparent = settings["transparent"],
                                   border = settings["border"], xtics = xtics[0:len(xtics)-1])

        if settings["legend"]:
            general_gnuplot += 'set title "{legend}"\n'.format(legend = settings["legend"])

        general_gnuplot += 'set output "test.png"\n'

        if "colors" not in settings:
            general_gnuplot += 'plot "-" u 1:2:({circle_size}) w circles lc rgb "{color}" fill solid\n'.format(circle_size = 1500*settings["width"], color = constants["colors"][random.randrange(len(constants["colors"]))])
        else:
            general_gnuplot += 'plot "-" u 1:2:({circle_size}) w circles lc rgb "{color}" fill solid\n'.format(circle_size = 1500*settings["width"], color = settings["colors"][random.randrange(len(settings["colors"]))])

        minimum = ymin if ymin >= 0 else 0 if ymax >= 0 else ymax
        inc = settings["delay"]

        print(general_gnuplot)
        general_gnuplot += out

        with tempfile.TemporaryDirectory() as tmpdirname:
            """with open(os.path.join(tmpdirname, 'gnuplot.gp'), mode='w+b') as gp_file:
                gp_file.write(general_gnuplot.encode())"""
            gnuplot = subprocess.Popen(["gnuplot", "-persist"], stdin=subprocess.PIPE).stdin

            gnuplot.write(general_gnuplot.encode())
            gnuplot.write(b"\ne")
            gnuplot.flush()



    else:
        verbose("One curve for each input file in one graph will be generated.", settings["verbose"], 1)
        """Spočítat columns, distance"""
        for i_data in suitable_data:
            print(i_data)

