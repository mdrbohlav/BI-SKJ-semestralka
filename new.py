#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import shlex

def soft_error(message, req_lvl = 1, verbose_lvl = 1, ignore_error = True):
    """Prints error message to the stderr and if errors are not ignored it kills script executing."""
    if ignore_error:
        verbose(message, verbose_lvl, req_lvl)
    else:
        print(message, file = sys.stderr)
        print("Stopping script.")
        sys.exit(1)

def error(message):
    """Prints error mesage to the stderr and kills the script always."""
    print("ERROR: " + message, file = sys.stderr)
    print("Stopping script.")
    sys.exit(1)

def verbose(message, verbose_lvl, req_lvl):
    """Prints message to the stderr based on the verbose level."""
    if verbose_lvl == req_lvl:
        print(message, file = sys.stderr)

def percentage_done(done, total):
    """Prints how many percent is done."""
    percent = done/total*100
    print("     {0:3d} % done \r".format(int(percent)), end="")

def is_number(val):
  """Checks if value is a number."""
  try:
    num = float(val)
    return True
  except ValueError:
    return False

def pattern_time_format(val):
    """Retunrs patterns of the time format."""
    pattern = re.sub('[^%YymdHMS]', '.', val)
    pattern = re.sub('%[ymdHMS]', '([0-9]{2})', pattern)
    pattern = re.sub('%[Y]', '([0-9]{4})', pattern)
    return pattern

def check_time_format(val):
    """Checks time format if it is in correct form."""
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
    """Checks if the maximum value is number, 'max' or 'auto'."""
    if settings["max_val"] not in [ "max", "auto" ]:
        if is_number(settings["max_val"]):
            settings["max_val"] = float(settings["max_val"])
        else:
            soft_error("WARNING: 'max_val' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["max_val"] = constants["max_val"]
    return settings["max_val"]
        

def check_min(settings, constants):
    """Checks if the minimum value is number, 'min' or 'auto'."""
    if settings["min_val"] not in [ "min", "auto" ]:
        if is_number(settings["min_val"]):
            settings["min_val"] = float(settings["min_val"])
        else:
            soft_error("WARNING: 'min_val' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["min_val"] = constants["min_val"]
    return settings["min_val"]
        

def check_max_time(settings, constants):
    """Checks maximum time value and converts it to the seconds."""
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
    """Checks minimum time value and converts it to the seconds."""
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
    """Checks time value if it is valid and compare it to the FPS and speed."""
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
    """Checks speed value if it is valid."""
    if not is_number(settings["speed"]):
        soft_error("WARNING: 'speed' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default value.", settings["verbose"], 1)
        settings["speed"] = constants["speed"]
    return settings["speed"]

def check_fps(settings, constants):
    """Checks FPS value if it is valid."""
    if not is_number(settings["fps"]):
        soft_error("WARNING: 'fps' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default value.", settings["verbose"], 1)
        settings["fps"] = constants["fps"]
    return settings["fps"]

def check_legend(val):
    """Checks if legend is not an empty string."""
    if val.strip() == "":
        soft_error("WARNING: 'legend' is an empty string.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Removing.", settings["verbose"], 1)
        val = None
    return val

def check_name(val, constants):
    """Checks if name is not an empty string."""
    if val.strip() == "":
        soft_error("WARNING: 'name' is an empty string.", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using script name.", settings["verbose"], 1)
        val = constants
    return val

def check_gnuplot(val):
    """Checks gnuplot parameters."""
    return val

def check_effect(settings, constants):
    """Checks effect parameters."""
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
    """Checks path name. Also checks if the file exists and is readable."""
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
    """Checks if the file should be download from the internet. If not it checks the local file."""
    if "http" in val:
        return val
    else:
        return check_pathname(val)

def load_config(settings):
    """Loads config file."""
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
    """Loads input data file."""
    data = []
    for i, line in enumerate(i_file):
        decodedLine = re.sub("\n", "", line.decode("utf-8"))
        data.append(decodedLine.strip())
    if len(data) == 0:
        del data
        return None
    return data

def check_data_line(time, value, time_format):
    """Checks input data values (time and value)."""
    """Fce, která zkontroluje vstupní data (čas a hodnotu)"""
    pattern = pattern_time_format(settings["time_format"])
    if not re.compile("^" + pattern + "$").match(time):
        return 1
    elif not is_number(value):
        return 2
    return 0

def select_drawable_data(data, distance, settings):
    """Selects data that should be shown in the graph. Depends on te selected method it can compute the value."""
    res_output = ""
    col_num = 1
    counter = 0
    height = 0
    ymax = None
    ymin = None
    start = None
    for index_line, i_line in enumerate(data.split("\n")):
        time, value = i_line.split()
        time = int(time)
        value = float(value)
        if index_line == 0:
            start = time
        counter += 1

        if (start + col_num * distance) > time or start == time:
            if settings["method"] == "average":
                height += value
            else:
                height = value if math.fabs(value) > math.fabs(height) else height
            continue

        if settings["method"] == "average":
            height = height / (counter-1)

        if col_num == 1:
            ymax = height
            ymin = height
        else:
            ymax = height if height > ymax else ymax
            ymin = height if height < ymin else ymin

        tmp = start + distance * col_num - distance / 2
        res_output += "{} {}\n".format(tmp, height)

        height = value
        counter = 1
        col_num += 1

        while start + col_num * distance < time:
            col_num += 1

    "If the loop ended in the middle of the column last value was not added."
    if start + col_num * distance < time:
        if settings["method"] == "average":
            height = height / (counter-1)
        ymax = height if height > ymax else ymax
        ymin = height if height < ymin else ymin
        tmp = start + distance * col_num - distance / 2
        res_output += "{} {}".format(tmp, height)

    "Checks if the values are in the desired range."
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

    return [res_output, ymax, ymin]

def count_frames(data, ymax, ymin, jump):
    """Counts how many frames will take to each circle to get to the position and returns the highest value."""
    frames = None
    tmp_border = math.fabs(ymin) if math.fabs(ymin) < math.fabs(ymax) else math.fabs(ymax)
    for index, line in enumerate(data.split("\n")):
        if line == "":
            continue
        time, value = line.split()
        value = float(value)

        tmp_val = (tmp_border - math.fabs(value)) / jump
        tmp_val += index * settings["delay"]
        if not frames or tmp_val > frames:
            frames = tmp_val
    return frames

def get_max_date(data, prevMax):
    """Finds the maximal dates."""
    if not prevMax or prevMax < int(i_data.split()[-2:-1][0]):
        prevMax = int(i_data.split()[-2:-1][0])
    return prevMax

def get_min_date(data, prevMin):
    """Finds the minimal dates."""
    if not prevMin or prevMin > int(i_data.split()[0]):
        prevMin = int(i_data.split()[0])
    return prevMin

def set_speed_fps_if_needed(settings, frames):
    """Sets FPS and speed it hey are not set."""
    if not settings["speed"]:
        settings["speed"] = round(frames / (settings["time"] * settings["fps"]), 2)
    if not settings["fps"]:
        settings["fps"] = round(frames / (settings["speed"] * settings["time"]), 2)
    return settings

def set_y_range(min_val, max_val, ymin, ymax):
    """Sets range of the y axis"""
    yrange = ""
    if settings["min_val"] != "auto":
        yrange = "{}:".format(ymin)
    if settings["max_val"] != "auto":
        yrange += ":{}".format(ymax) if yrange == "" else "{}".format(ymax)
    return yrange

def set_x_tics(xmin, xmax):
    """Sets labels for the x axis."""
    xtics = ""
    tmp = xmin + (xmax-xmin) // 20
    while tmp < xmax:
        xtics += "'{:2d}:{:02d}:{:02d}' {:d},".format((tmp//60//60) % 24, (tmp//60) % 60, tmp % 60, tmp)
        tmp += (xmax - xmin) // 10
    return xtics

def generate_video(settings, digits, tmp_dir):
    """Creates target directory and generates video (using ffmpeg)."""
    index = 1
    video_name = settings["name"] + '.mp4'
    print("Creating target directory for the video.")
    while os.path.isdir(settings["name"]):
        if index == 1:
            settings["name"] += '_{}'.format(index)
        else:
            settings["name"] = settings["name"][:settings["name"].rfind("_")] + '_{}'.format(index)
        index += 1
    os.makedirs(settings["name"])

    print("Generating video...")
    cmd = ''.join(('ffmpeg -i "{}/%0{}d.png"'.format(tmp_dir, digits),
                  ' -r {}'.format(settings["fps"]),
                  ' {}/{}'.format(settings["name"], video_name)))
    proc = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    output = proc.communicate()[0].decode()
    
    return "Video generated: '{}/{}'".format(settings["name"], video_name)

def process_data(data, settings):
    """Calcualtes all needed values and generates all frames."""
    print("Processing data and generating all frames...")
    count = 0
    xmax = None
    xmin = None
    for i_data in data:
        xmax = get_max_date(i_data, xmax)
        xmin = get_min_date(i_data, xmin)

        "Counts # of input values."
        count += math.ceil((i_data.count("\n")+1)/2)

    if not settings["columns"]:
        settings["columns"] = count if count <= constants["max_columns"] else constants["max_columns"]

    "Counts time between each records after which next circle should appear."
    distance = (xmax-xmin) / settings["columns"]

    "Selects desired data and counts their maximal and minimal value."
    res_output = []
    ymax = None
    ymin = None
    for i_data in data:
        res = select_drawable_data(i_data, distance, settings)
        res_output.append(res[0])
        ymax = res[1] if not ymax or ymax < res[1] else ymax
        ymin = res[2] if not ymin or ymin > res[2] else ymin

    "Counts size of the jump - how much the circle should move each step."
    jump = (ymax - ymin) / settings["steps"]

    "If the minimal and maximal values are not set 'ymax' and 'ymin' are adjusted to create a gap in the top and bottom of the graph."
    if settings["max_val"] == "max":
        ymax = 0 if ymax <= 0 and ymax + 20 * jump > 0 else ymax + 20 * jump
    if settings["min_val"] == "min":
        ymin = 0 if ymin >= 0 and ymin - 20 * jump < 0 else ymin - 20 * jump

    frames = None
    for i_data in res_output:
        if not frames:
            tmp = count_frames(i_data, ymax, ymin, jump)
            frames = tmp
        else:
            tmp = count_frames(i_data, ymax, ymin, jump)
            frames = tmp if tmp > frames else frames

    settings = set_speed_fps_if_needed(settings, frames)

    "Counts # of the frames according to the speed."
    real_frames = frames if int(frames / settings["speed"]) == frames / settings["speed"] else round(frames / settings["speed"])

    digits = len(str(real_frames))

    yrange = set_y_range(settings["min_val"], settings["max_val"], ymin, ymax)

    xtics = set_x_tics(xmin, xmax)

    general_gnuplot = 'set term png truecolor\n\
                       set key off\n\
                       set xrange ["{xmin}":"{xmax}"] noreverse nowriteback\n\
                       set yrange [{yrange}] noreverse nowriteback\n\
                       unset autoscale\n\
                       set style fill transparent solid {transparent} {border}\n\
                       set xtics rotate by -45 scale 1 font ",10" ({xtics})\n'\
                       .format(xmin = xmin, xmax = xmax, yrange = yrange, transparent = settings["transparent"],
                               border = settings["border"], xtics = xtics[0:len(xtics)-1])

    if settings["legend"]:
        general_gnuplot += 'set title "{legend}"\n'.format(legend = settings["legend"])

    partial_out = []
    selected_colors = []

    for index, i_data in enumerate(res_output):
        partial_out.append([])
        for line in i_data.split("\n"):
            if line == "":
                continue
            time, value = line.split()
            if float(value) < 0:
                partial_out[index].append("{} {}".format(time, ymin))
            else:
                partial_out[index].append("{} {}".format(time, ymax))

        if "colors" not in settings:
            tmp = constants["colors"][random.randrange(len(constants["colors"]))]
            while tmp in selected_colors:
                tmp = constants["colors"][random.randrange(len(constants["colors"]))]
            selected_colors.append(tmp)
        else:
            tmp = settings["colors"][random.randrange(len(settings["colors"]))]
            while tmp in selected_colors:
                if len(selected_colors) >= len(res_output):
                    tmp = constants["colors"][random.randrange(len(constants["colors"]))]
                else:
                    tmp = settings["colors"][random.randrange(len(settings["colors"]))]
            selected_colors.append(tmp)

        general_gnuplot += 'set style line {} lc rgb "{}"\n'.format(index + 1, selected_colors[index], index + 3)


    with tempfile.TemporaryDirectory() as tmp_dir:
        i = int(settings["delay"])
        counter = 0
        while i < real_frames + settings["delay"]:
            percentage_done(i - settings["delay"] + 1, real_frames)
            i += int(settings["speed"])
            counter += 1
            k = i / settings["delay"]
            effect_data = []

            gnuplot_settings = general_gnuplot
            gnuplot_settings += 'set output "{0}/{1:0{2}d}.png"\n'.format(tmp_dir, counter, digits)

            for index in range(0, len(res_output)):
                if index == 0:
                    gnuplot_settings += 'plot'
                else:
                    gnuplot_settings += ','
                gnuplot_settings += ' "-" u 1:2:({}) w circles ls {}'.format(1500*settings["width"], index + 1)
            gnuplot_settings += "\n"

            for index, i_data in enumerate(res_output):
                effect_data.append("")
                for index_line, line in enumerate(i_data.split("\n")):
                    if line == "" or index_line + 1 > k:
                        continue
                    time, value = line.split()
                    value = float(value)
                    partial_time, partial_value = partial_out[index][index_line].split()
                    partial_value = float(partial_value)

                    if value < 0:
                        tmp = -1
                    else:
                        tmp = 1

                    val = partial_value - tmp * jump

                    if math.fabs(val) <= math.fabs(value) or (val > 0 and value < 0) or (val < 0 and value > 0):
                        val = value

                    partial_out[index][index_line] = "{} {}".format(partial_time, val)
                    effect_data[index] += "{} {}\n".format(partial_time, val)
                    
                gnuplot_settings += effect_data[index]
                gnuplot_settings += 'e\n'

            gnuplot = subprocess.Popen(["gnuplot", "-persist"], stdin=subprocess.PIPE).stdin         
            gnuplot.write(gnuplot_settings.encode())
            gnuplot.flush()

        print("All frames generated.")

        print(generate_video(settings, digits, tmp_dir))

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
        "name": "new",
        "delay": 10,
        "verbose": 0,
        "ignore_error": False,
        "min_val": "min",
        "max_val": "max",
        "min_time": "min",
        "max_time": "max",
        "border": "",
        "method": "average",
        "transparent": 0.65,
        "width": 1,
        "steps": 50,
        "colors": [ "web-green", "black", "dark-grey", "red", "web-blue", "dark-magenta", "dark-cyan", "dark-orange", "dark-yellow", "royalblue", "goldenrod", "dark-spring-green", "purple", "steelblue", "dark-red", "dark-chartreuse", "orchid", "aquamarine", "brown", "yellow", "turquoise", "grey0", "grey10", "grey20", "grey30", "grey40", "grey50", "grey60", "grey70", "grey", "grey80", "grey90", "grey100", "light-red", "light-green", "light-blue", "light-magenta", "light-cyan", "light-goldenrod", "light-pink", "light-turquoise", "gold", "green", "dark-green", "spring-green", "forest-green", "sea-green", "blue", "dark-blue", "midnight-blue", "navy", "medium-blue", "skyblue", "cyan", "magenta", "dark-turquoise", "dark-pink", "coral", "light-coral", "orange-red", "salmon", "dark-salmon", "khaki", "dark-khaki", "dark-goldenrod", "beige", "olive", "orange", "violet", "dark-violet", "plum", "dark-plum", "dark-olivegreen", "orangered4", "brown4", "sienna4", "orchid4", "mediumpurple3", "slateblue1", "yellow4", "sienna1", "tan1", "sandybrown", "light-salmon", "pink", "khaki1", "lemonchiffon", "bisque", "honeydew", "slategrey", "seagreen", "antiquewhite", "chartreuse", "greenyellow", "gray", "light-gray", "light-grey", "dark-gray", "slategray", "gray0", "gray10", "gray20", "gray30", "gray40", "gray50", "gray60", "gray70", "gray80", "gray90", "gray100" ]
    }

    settings = {
        "border": constants["border"],
        "transparent": constants["transparent"],
        "delay": constants["delay"],
        "method": constants["method"],
        "width": constants["width"],
        "columns": None,
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

    "Copy arguments the the dict settings"
    for key in ["time_format", "max_val", "min_val", "max_time", "min_time", "speed", "time", "fps", "legend", "gnuplot", "effect", "config", "name", "ignore_error", "verbose", "input"]:
        settings[key] = user[key]

    "Loads config file"
    if settings["config"]:
        settings = load_config(settings)

    "Checks speed, time and FPS if they are set all three."
    if settings["speed"] and settings["time"] and settings["fps"] and not float(settings["speed"]) * float(settings["fps"]) == float(settings["time"]):
        soft_error("WARNING: Mutually exclusive arguments defined. (-S speed, -T time, -F fps)", settings["verbose"], 1, settings["ignore_error"])
        verbose(" - Using default values.", settings["verbose"], 1)
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

    "Loading data from files"
    data = {}
    for input_file in settings["input"][0]:
        if "http" in input_file:
            "All files starting with 'http'"
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
            res = check_data_line(time, value, settings["time_format"])
            if res == 1:
                soft_error("WARNING: file '{}':\n - line #{}: wrong time format.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                verbose(" - skipping", settings["verbose"], 1)
            elif res == 2:
                soft_error("WARNING: file '{}':\n - line #{}: wrong value.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                verbose(" - skipping", settings["verbose"], 1)

            "Checks another mistakes in date (month # 13 etc.)"
            try:
                time = int(datetime.strptime(time, settings["time_format"]).strftime('%s')) + int(datetime.today().strftime('%s')) - int(datetime.utcnow().strftime('%s'))
            except ValueError:
                soft_error("WARNING: file '{}':\n - line #{}: wrong date.".format(i_file, index_line+1), settings["verbose"], 1, settings["ignore_error"])
                verbose(" - skipping", settings["verbose"], 1)
                continue
            
            "Skip if the time is out of desired range."
            if settings["min_time"] not in ["min", "auto"] and time < settings["min_time"]:
                continue
            elif settings["max_time"] not in ["max", "auto"] and time > settings["max_time"]:
                continue

            size = len(suitable_data)
            "If not first row in the file we have to check the order."
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
        verbose("One curve for all input files in one graph will be generated.", settings["verbose"], 1)
        joinedData = ""

        "File are not overlaping - we can merge the data."
        for index, i_data in enumerate(suitable_data):
            joinedData += "\n" + i_data if index > 0 else i_data

        data = [ joinedData ]
        
        process_data(data, settings)

    else:
        verbose("One curve for each input file in one graph will be generated.", settings["verbose"], 1)

        data = suitable_data

        process_data(data, settings)
