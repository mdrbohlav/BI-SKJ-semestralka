import os
import sys
import subprocess
import re
import tempfile
import math
import random
import shlex
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime

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
    """Checks if the maximum value is number, 'max'."""
    if settings["max_val"] not in [ "max" ]:
        if is_number(settings["max_val"]):
            settings["max_val"] = float(settings["max_val"])
        else:
            soft_error("WARNING: 'max_val' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["max_val"] = constants["max_val"]
    return settings["max_val"]
        

def check_min(settings, constants):
    """Checks if the minimum value is number, 'min'."""
    if settings["min_val"] not in [ "min" ]:
        if is_number(settings["min_val"]):
            settings["min_val"] = float(settings["min_val"])
        else:
            soft_error("WARNING: 'min_val' has an invalid value.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Using default value.", settings["verbose"], 1)
            settings["min_val"] = constants["min_val"]
    return settings["min_val"]
        

def check_max_time(settings, constants):
    """Checks maximum time value and converts it to the seconds."""
    if settings["max_time"] not in [ "max" ]:
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
    if settings["min_time"] not in [ "min" ]:
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

def check_gnuplot(settings):
    """Checks gnuplot parameters. Allowed are only parameters starting with 'set' or 'unset'."""
    tmp = ""
    for value in settings["gnuplot"]:
        value = value.strip()
        if not re.compile("^(set|unset)..*[^;]$").match(value):
            soft_error("WARNING: wrong gnuplot parameter: '{}'. Allowed are only 'set' and 'unset'.".format(value), settings["verbose"], 1, settings["ignore_error"])
            verbose(" - Skipping.", settings["verbose"], 1)
        else:
            tmp += "{}\n".format(value)
    return tmp

def check_effect(settings, constants):
    """Checks effect parameters."""
    params = ':'.join(settings["effect"]).split(":")
    for param in params:
        tmp = param.split("=")
        if len(tmp) != 2:
            soft_error("WARNING: wrong effect parameter: '{}'.".format(param), settings["verbose"], 1, settings["ignore_error"])
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
        elif directive == "color":
            for c in value.split(','):
                if c not in constants["colors"]:
                    soft_error("WARNING: wrong effect parameter: unknown color '{}'.".format(c), settings["verbose"], 1, settings["ignore_error"])
                    verbose(" - Skipping.", settings["verbose"], 1)
                else:
                    if "colors" not in settings:
                        settings["colors"] = []
                    settings["colors"].append(c)
        elif directive == "method":
            if value not in [ "average", "top" ]:
                soft_error("WARNING: wrong effect parameter: method has to be set to 'average' or 'top'.", settings["verbose"], 1, settings["ignore_error"])
                verbose(" - Using default value.", settings["verbose"], 1)
                settings["method"] = constants["method"]
            else:
                settings["method"] = value
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
    """Checks if the file should be downloaded from the internet. If not it checks the local file."""
    if "http" in val:
        return val
    else:
        return check_pathname(val)

def check_data_line(time, value, time_format):
    """Checks input data values (time and value)."""
    pattern = pattern_time_format(time_format)
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

            if col_num == 1:
                ymax = height
                ymin = height
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
    if start + col_num * distance < time or start == time:
        if settings["method"] == "average":
            height = height if counter == 1 else height / (counter-1)
        ymax = height if height > ymax else ymax
        ymin = height if height < ymin else ymin
        tmp = start + distance * col_num - distance / 2
        res_output += "{} {}".format(tmp, height)

    "Checks if the values are in the desired range."
    if settings["min_val"] not in [ "min" ]:
        if ymax < settings["min_val"]:
            soft_error("WARNING: 'y_min' out of range.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - 'y_min' not set", settings["verbose"], 1)
        else:
            ymin = settings["min_val"]

    if settings["max_val"] not in [ "max" ]:
        if ymin > settings["max_val"]:
            soft_error("WARNING: 'y_max' out of range.", settings["verbose"], 1, settings["ignore_error"])
            verbose(" - 'y_max' not set", settings["verbose"], 1)
        else:
            ymax = settings["max_val"]

    return [res_output, ymax, ymin]

def count_frames(data, ymax, ymin, jump, delay):
    """Counts how many frames will take to each point to get to the position and returns the highest value."""
    frames = None
    tmp_border = math.fabs(ymin) if math.fabs(ymin) > math.fabs(ymax) else math.fabs(ymax)
    for index, line in enumerate(data.split("\n")):
        if line == "":
            continue
        time, value = line.split()
        value = float(value)

        tmp_val = (tmp_border - math.fabs(value)) / jump
        tmp_val += index * delay
        if not frames or tmp_val > frames:
            frames = tmp_val
    return frames

def get_max_date(data, prevMax):
    """Finds the maximal dates."""
    if not prevMax or prevMax < int(data.split()[-2:-1][0]):
        prevMax = int(data.split()[-2:-1][0])
    return prevMax

def get_min_date(data, prevMin):
    """Finds the minimal dates."""
    if not prevMin or prevMin > int(data.split()[0]):
        prevMin = int(data.split()[0])
    return prevMin

def set_speed_fps_if_needed(settings, frames):
    """Sets FPS and speed if they are not set."""
    if not settings["speed"]:
        settings["speed"] = round(frames / (int(settings["time"]) * int(settings["fps"])), 2)
    if not settings["fps"]:
        settings["fps"] = round(frames / (int(settings["speed"]) * int(settings["time"])), 2)
    return settings

def set_y_range(min_val, max_val, ymin, ymax):
    """Sets range of the y axis"""
    yrange = ""
    yrange = "{}:".format(ymin)
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

def generate_video(settings, digits, tmp_dir):
    """Creates target directory and generates video (using ffmpeg)."""
    index = 1
    video_name = settings["name"] + '.mp4'
    print("Creating target directory for the video.")
    
    directories = [x[0] for x in os.walk('./')]
    tmp = None
    for directory in directories:
        if re.compile("^./" + settings["name"] + ".*$").match(directory):
            index = directory.rfind("_")
            if index == -1 or not directory[index+1:].isdigit():
                tmp = 1
            else:
                if tmp < int(directory[index+1:]) + 1:
                    tmp = int(directory[index+1:]) + 1

    if tmp:
        settings["name"] = "{}_{}".format(settings["name"], tmp)

    os.makedirs(settings["name"])

    print("Generating video...")
    cmd = ''.join(('ffmpeg -i "{}/%0{}d.png"'.format(tmp_dir, digits),
                  ' -r {}'.format(settings["fps"]),
                  ' {}/{}'.format(settings["name"], video_name)))
    proc = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    output = proc.communicate()[0].decode()

    verbose(output, settings["verbose"], 2)
    
    return "Video generated: '{}/{}'".format(settings["name"], video_name)

def process_data(data, settings, constants):
    """Calculates all needed values and generates all frames."""
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
            tmp = count_frames(i_data, ymax, ymin, jump, settings["delay"])
            frames = tmp
        else:
            tmp = count_frames(i_data, ymax, ymin, jump, settings["delay"])
            frames = tmp if tmp > frames else frames

    settings = set_speed_fps_if_needed(settings, frames)

    "Counts # of the frames according to the speed."
    real_frames = frames if int(frames) / int(settings["speed"]) == int(frames) / int(settings["speed"]) else round(int(frames) / int(settings["speed"]))

    digits = len(str(real_frames))

    yrange = set_y_range(settings["min_val"], settings["max_val"], ymin, ymax)

    xtics = set_x_tics(xmin, xmax)

    general_gnuplot = 'set term png truecolor\n\
                       set key off\n\
                       set xrange ["{xmin}":"{xmax}"] noreverse nowriteback\n\
                       set yrange [{yrange}] noreverse nowriteback\n\
                       unset autoscale\n\
                       set xtics rotate by -45 scale 1 font ",10" ({xtics})\n'\
                       .format(xmin = xmin, xmax = xmax, yrange = yrange, xtics = xtics[0:len(xtics)-1])

    if settings["gnuplot"]:
        general_gnuplot += settings["gnuplot"]

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

                gnuplot_settings += ' "-" u 1:2 w p ls {}'.format(index + 1)
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

                    "'value' is a target value"
                    tmp = -1 if value < 0 else 1

                    "'partial_value' is a value for the current frame"
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
