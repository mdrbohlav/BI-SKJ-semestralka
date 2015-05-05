#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime
import urllib.request
from urllib.error import URLError, HTTPError

import functions

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
        "max_columns": 30,
        "speed": 1,
        "fps": 25,
        "name": "circles_graph",
        "delay": 10,
        "verbose": 0,
        "ignore_error": False,
        "min_val": "min",
        "max_val": "max",
        "min_time": "min",
        "max_time": "max",
        "method": "average",
        "steps": 50,
        "colors": [ "web-green", "black", "dark-grey", "red", "web-blue", "dark-magenta", "dark-cyan", "dark-orange", "dark-yellow", "royalblue", "goldenrod", "dark-spring-green", "purple", "steelblue", "dark-red", "dark-chartreuse", "orchid", "aquamarine", "brown", "yellow", "turquoise", "grey0", "grey10", "grey20", "grey30", "grey40", "grey50", "grey60", "grey70", "grey", "grey80", "grey90", "grey100", "light-red", "light-green", "light-blue", "light-magenta", "light-cyan", "light-goldenrod", "light-pink", "light-turquoise", "gold", "green", "dark-green", "spring-green", "forest-green", "sea-green", "blue", "dark-blue", "midnight-blue", "navy", "medium-blue", "skyblue", "cyan", "magenta", "dark-turquoise", "dark-pink", "coral", "light-coral", "orange-red", "salmon", "dark-salmon", "khaki", "dark-khaki", "dark-goldenrod", "beige", "olive", "orange", "violet", "dark-violet", "plum", "dark-plum", "dark-olivegreen", "orangered4", "brown4", "sienna4", "orchid4", "mediumpurple3", "slateblue1", "yellow4", "sienna1", "tan1", "sandybrown", "light-salmon", "pink", "khaki1", "lemonchiffon", "bisque", "honeydew", "slategrey", "seagreen", "antiquewhite", "chartreuse", "greenyellow", "gray", "light-gray", "light-grey", "dark-gray", "slategray", "gray0", "gray10", "gray20", "gray30", "gray40", "gray50", "gray60", "gray70", "gray80", "gray90", "gray100" ]
    }

    settings = {
        "delay": constants["delay"],
        "method": constants["method"],
        "columns": None,
        "steps": constants["steps"],
        "verbose": constants["verbose"]
    }

    parser = ArgumentParser(description="Under construction...", epilog="Thank you for reading this.")
    parser.add_argument('--version', action='version', version='1.0')
    parser.add_argument('-t', dest='time_format', help='Format of the timestamp. Available are values %Y, %y, %m, %d, %H, %M, %S.')
    parser.add_argument('-Y', dest='max_val', help='Sets maximal value of the X axis. Options are int/float or "max".')
    parser.add_argument('-y', dest='min_val', help='Sets minimal value of the X axis. Options are int/float or "min".')
    parser.add_argument('-X', dest='max_time', help='Sets maximal value of the Y axis. Options are int/float or "max".')
    parser.add_argument('-x', dest='min_time', help='Sets minimal value of the Y axis. Options are int/float or "min".')
    parser.add_argument('-S', dest='speed')
    parser.add_argument('-T', dest='time')
    parser.add_argument('-F', dest='fps')
    parser.add_argument('-l', dest='legend')
    parser.add_argument('-g', dest='gnuplot', action='append')
    parser.add_argument('-e', dest='effect', action='append')
    parser.add_argument('-f', dest='config', type=functions.check_pathname)
    parser.add_argument('-n', dest='name')
    parser.add_argument('-E', dest='ignore_error', action='store_true')
    parser.add_argument('-v', dest='verbose', action='count')
    parser.add_argument('input', type=functions.check_file, action='append', nargs='+')

    args = parser.parse_args()

    user = vars(args)

    "Copy arguments the the dict settings"
    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "speed", "time", "fps", "legend", "gnuplot", "effect", "config", "name", "ignore_error", "verbose", "input"]:
        settings[key] = user[key]

    "Loads config file"
    if settings["config"]:
        settings = functions.load_config(settings)

    "Checks speed, time and FPS if they are set all three."
    if settings["speed"] and settings["time"] and settings["fps"] and not float(settings["speed"]) * float(settings["fps"]) == float(settings["time"]):
        functions.soft_error("WARNING: Mutually exclusive arguments defined. (-S speed, -T time, -F fps)", settings["verbose"], 1, settings["ignore_error"])
        functions.verbose(" - Using default values.", settings["verbose"], 1)
        settings["speed"] = constants["speed"]
        settings["time"] = None
        settings["fps"] = constants["fps"]

    "If only one of the values time, speed and FPS set we have to compute the rest."
    if settings["time"] and not settings["fps"] and not settings["speed"]:
        settings["fps"] = constants["fps"]
    elif not settings["time"] and settings["fps"] and not settings["speed"]:
        settings["speed"] = constants["speed"]
    elif not settings["time"] and not settings["fps"] and settings["speed"]:
        settings["fps"] = constants["fps"]
    elif not settings["time"] and not settings["fps"] and not settings["speed"]:
        settings["fps"] = constants["fps"]
        settings["speed"] = constants["speed"]

    "Using default values if they have not been set by the user."
    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "name", "ignore_error", "verbose" ]:
        if not settings[key]:
            settings[key] = constants[key]

    "Checking loaded values."
    functions.check_time_format(settings["time_format"])
    settings["min_val"] = functions.check_min(settings, constants)
    settings["max_val"] = functions.check_max(settings, constants)
    settings["max_time"] = functions.check_max_time(settings, constants)
    settings["min_time"] = functions.check_min_time(settings, constants)

    if settings["time"]:
        settings = functions.check_time(settings, constants)

    if settings["fps"]:
        settings["fps"] = functions.check_fps(settings, constants)

    if settings["speed"]:
        settings["speed"] = functions.check_speed(settings, constants)

    if settings["legend"]:
        settings["legend"] = functions.check_legend(settings["legend"])

    if settings["gnuplot"]:
        settings["gnuplot"] = functions.check_gnuplot(settings)

    if settings["effect"]:
        settings["effect"] = functions.check_effect(settings, constants)

    settings["name"] = functions.check_name(settings["name"], constants["name"])

    if settings["max_val"] not in [ "max" ] and settings["min_val"] not in [ "min" ] and settings["max_val"] <= settings["min_val"]:
        functions.soft_error("WARNING: 'max_val' has to be bigger than 'min_val", settings["verbose"], 1, settings["ignore_error"])
        functions.verbose(" - Using default values.", settings["verbose"], 1)
        settings["max_val"] = constants["max_val"]
        settings["min_val"] = constants["min_val"]

    if settings["max_time"] not in [ "max" ] and settings["min_time"] not in [ "min" ] and settings["max_time"] <= settings["min_time"]:
        functions.soft_error("WARNING: 'max_time' has to be bigger than 'min_time", settings["verbose"], 1, settings["ignore_error"])
        functions.verbose(" - Using default values.", settings["verbose"], 1)
        settings["max_time"] = constants["max_time"]
        settings["min_val"] = constants["min_time"]

    "Loading data from files"
    data = {}
    for input_file in settings["input"][0]:
        if "http" in input_file:
            "All files starting with 'http'"
            file_name = input_file[input_file.rfind("/"):]
            functions.verbose("Downloading file '{}'".format(input_file), settings["verbose"], 2)
            try:
                with urllib.request.urlopen(input_file) as i_file:
                    data[input_file] = functions.load_data_file(i_file)
                        
            except HTTPError as e:
                functions.soft_error("ERROR: The server couldn\'t fulfill the request.", settings["verbose"], 1, settings["ignore_error"])
                functions.verbose(" - error code: {}".format(e.code), settings["verbose"], 1)
            except URLError as e:
                functions.soft_error("ERROR: We failed to reach a server.", settings["verbose"], 1, settings["ignore_error"])
                functions.verbose(" - reason: {}".format(e.code), settings["verbose"], 1)
        else:
            functions.verbose("Opening file '{}'".format(input_file), settings["verbose"], 2)
            with open(input_file, mode='rb') as i_file:
                data[input_file] = functions.load_data_file(i_file)

    if len(data) == 0:
        functions.error("No input data were loaded.")

    functions.verbose("Validating input files data...", settings["verbose"], 2)

    suitable_data = []

    "Checks data from input files - if the time is in correct format, order an if the values are numeric."
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
            
            "Returns 1 for error in time and 2 for error in value."
            res = functions.check_data_line(time, value, settings["time_format"])
            if res == 1:
                functions.soft_error("WARNING: file '{}':\n - line #{}: wrong time format.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                functions.verbose(" - skipping", settings["verbose"], 1)
            elif res == 2:
                functions.soft_error("WARNING: file '{}':\n - line #{}: wrong value.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                functions.verbose(" - skipping", settings["verbose"], 1)

            "Checks another mistakes in date (month # 13 etc.)"
            try:
                time = int(datetime.strptime(time, settings["time_format"]).strftime('%s')) + int(datetime.today().strftime('%s')) - int(datetime.utcnow().strftime('%s'))
            except ValueError:
                functions.soft_error("WARNING: file '{}':\n - line #{}: wrong date.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                functions.verbose(" - skipping", settings["verbose"], 1)
                continue
            
            "Skip if the time is out of desired range."
            if settings["min_time"] not in [ "min" ] and time < settings["min_time"]:
                continue
            elif settings["max_time"] not in [ "max" ] and time > settings["max_time"]:
                continue

            size = len(suitable_data)
            "If not first row in the file we have to check the order."
            if index_line == 0:
                suitable_data[size-1] = "{} {}".format(time, value)
            else:
                if time - prev <= 0:
                    functions.soft_error("WARNING: file '{}':\n - line #{}: wrong order of the input data.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                    functions.verbose(" - skipping", settings["verbose"], 1)
                    continue
                suitable_data[size-1] = suitable_data[size-1] + "\n{} {}".format(time, value)
            prev = time
        
        if suitable_data[len(suitable_data)-1] == "":
            functions.soft_error("WARNING: file '{}':\n - no suitable data found.".format(i_file), settings["verbose"], 1, settings["ignore_error"])
            del suitable_data[len(suitable_data)-1]

    if len(suitable_data) == 0:
        functions.error("ERROR: No suitable data found in any of the input files.")

    "Sorst input files using the date. (bubble sort)"
    for index_file in range(len(suitable_data)-1, 0, -1):
        for i in range(index_file):
            time = suitable_data[i].split()[0]
            timeNext = suitable_data[i+1].split()[0]
            if time > timeNext:
                tmp = suitable_data[i]
                suitable_data[i] = suitable_data[i+1]
                suitable_data[i+1] = tmp

    "Checks overlaping of the dates in all input files."
    overlaping = False
    for index, i_data in enumerate(suitable_data):
        if index == 0:
            continue
        prevEnd = suitable_data[index-1].split()[-2:-1][0]
        start = suitable_data[index].split()[0]
        if start <= prevEnd:
            overlaping = True
            break

    if not overlaping:
        functions.verbose("One curve for all input files in one graph will be generated.", settings["verbose"], 1)
        joinedData = ""

        "File are not overlaping - we can merge the data."
        for index, i_data in enumerate(suitable_data):
            joinedData += "\n" + i_data if index > 0 else i_data

        data = [ joinedData ]
        
        functions.process_data(data, settings, constants)

    else:
        functions.verbose("One curve for each input file in one graph will be generated.", settings["verbose"], 1)

        data = suitable_data

        functions.process_data(data, settings, constants)
