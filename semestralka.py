#   Switches
# =======================================================================================
#  opt. | direktiva     | popis               | typ hodnoty         | výchozí hodnota
# ------+---------------+---------------------+---------------------+--------------------
#  -t   | TimeFormat    | timestamp format    | strftime(3c)        | [%Y-%m-%d %H:%M:%S]
#  -Y   | Ymax          | y-max               | „auto“,“max“,value  | auto
#  -y   | Ymin          | y-min               | „auto“,“min“,value  | auto
#  -S   | Speed         | speed               | int/float           | 1 record/frame
#  -T   | Time          | time (duration)     | int/float           | n/a
#  -F   | FPS           | fps                 | int/float           | 25
#  -l   | Legend        | legend              | text                | n/a
#  -g   | GnuplotParams | gnuplot params*     | parameter           | n/a
#  -e   | EffectParams  | effect params*      | param=val:param=val | n/a
#  -f   | n/a           | config file         | pathname            | n/a
#  -n   | Name          | name                | text                | n/a
#

#   Usage Example
# =======================================================================================
#  python3.4 semestralka.py -t %y/%m/%d -Y 1000 -y -1000 -S 5 -F 15 -l "Example animation - Simple effect" -g "grid xtics ytics" -g "pointsize 10" -g "tics textcolor rgbcolor \"blue\"" -e bgcolor=red:width=32:shadow=none -n test_animation input_file_1 input_file_2 input_file_3
#

#   ToDo List
# =======================================================================================
#  výstup errorů na stderr
#  Xmax a Xmin default hodnota
#  set plot parameters
#
a
import argparse
import sys
import os
import time
import shutil
import subprocess
import signal
import datetime

specified_options = {} # dictionary s parametry a jejich hodnotami
ts = time.time()
temp_dir = str("tmp" + str(ts))[:13] # název dočasného adresáře

options = {"timeformat" : "t", "ymax" : "Y", "ymin" : "y", "speed" : "S", "time" : "T",
           "fps" : "F", "legend" : "l", "name" : "n", "gnuplotparams" : "g", "effectparams" : "e"} # podporované parametry
multiple_options = {"gnuplotparams" : "g", "effectparams" : "e", "input" : "input"} # parametry s více výskyty

def is_number(num):
  """ Kontroluje, zdali je 'num' číslo """
  try:
    float(num)
    return True
  except ValueError:
    pass
  return False

def TimeFormat(specified_value, used_value = "", file_num = 0, line = 0):
  """ Kontroluje formát časové značky 'used_value' s formátem zadaným, 'specified_value', při chybě vypíše soubor a řádek """
  if used_value == "":
    return specified_value
  timefmt_len = len(specified_value) + 2
  try:
    time.strptime(used_value[:timefmt_len], specified_value)
  except:
    print("Error: line %d, input file '%s': specified timestamp format was '%s' but used is '%s'" %
          (line, specified_options["input"][file_num], specified_value, used_value[:timefmt_len]))
    sys.exit()

def Ymax(value):
  """ Kontroluje argument Ymax, zdali je číslo, 'auto', nebo 'max' """
  if not (is_number(value) or value == "auto" or value == "max"):
    print("Error: invalid Ymax value '%s', see -h for help" % (value))
    sys.exit()
  return value

def Ymin(value):
  """ Kontroluje argument Ymin, zdali je číslo, 'auto', nebo 'min' """
  if not (is_number(value) or value == "auto" or value == "min"):
    print("Error: invalid Ymin value '%s', see -h for help" % (value))
    sys.exit()
  return value

def Speed(value):
  """ Kontroluje argument Speed, zdali je číslo """
  if not is_number(value):
    print("Error: invalid Speed value '%s', see -h for help" % (value))
    sys.exit()
  return value

def Time(value):
  """ Kontroluje argument Time, zdali je číslo """
  if not is_number(value):
    print("Error: invalid Time value '%s', see -h for help" % (value))
    sys.exit()
  return value

def FPS(value):
  """ Kontroluje hodnotu FPs, zdali je číslo """
  if not is_number(value):
    print("Error: invalid FPS value '%s', see -h for help" % (value))
    sys.exit()
  return value

def Legend(value):
  return value

def GnuplotParams(value):
  return value

def EffectParams(value):
  return value

def Name(value):
  """ Kontroluje argument Name """