import os
import re
from datetime import datetime
from datetime import timedelta
from subprocess import Popen
import shlex

def hhmmss_to_seconds(hh, mm, ss):
  return int(ss) + 60 * int(mm) + 60 * 60 * int(hh)

def seconds_to_hhmmss(seconds, delim=None):
  if delim == None:
    delim = ':'
  ss = seconds % 60
  mm = int(seconds / 60) % 60
  hh = int(seconds / (60 * 60))
  return '%02d%s%02d%s%02d' % (hh, delim, mm, delim, ss)

def get_file_prefix(path):
  return os.path.splitext(path)[0]

def parse_hhmmss(str):
  m = re.search('^\s*(\d\d)\:(\d\d)\:(\d\d)\s*$', str)
  return (m.group(1), m.group(2), m.group(3))

def parse_timedelta(str):
  m = re.search('^\s*(\d+)\:(\d\d)\:(\d\d)\s*$', str)
  return timedelta(
    hours=int(m.group(1)),
    minutes=int(m.group(2)),
    seconds=int(m.group(3))
  )

def timedelta_to_ffmpeg_string(d, delim=None):
  return seconds_to_hhmmss(d.seconds, delim)

def compute_datetime_path_string(now=None):
  if (now == None):
    now = datetime.now()
  return now.strftime('%Y%m%d-%H%M')

logger = None
logfile_path = None

def run_and_log(cmd):
  if logger != None:
    logger.info('Running command: %s' % cmd)
  logfile = None
  p = None
  if logfile_path != None:
    logfile = open(logfile_path, 'a')
    p = Popen(shlex.split(cmd), stdout=logfile, stderr=logfile, universal_newlines=True)
  else:
    p = Popen(shlex.split(cmd), universal_newlines=True)
  result = p.wait()
  if logfile != None:
    logfile.write('\r\n')
    logfile.flush()
    logfile.close()
  if logger != None:
    logger.info('Finished running command.  Result: %d' % result)
  return result

def dump_frames(
  input_file, end, start=timedelta(), 
  step=None, output_dir=None
):
  if step == None:
    step = timedelta(minutes=5)
  if output_dir == None:
    output_dir = '%s.frames' % input_file 
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)
  for secs in range(start.seconds, end.seconds, step.seconds):
    curr = timedelta(seconds=secs)
    output_file = '%s/%s.png' % (
      output_dir, timedelta_to_ffmpeg_string(curr, '-')
    )
    ffmpeg_cmd = 'ffmpeg -ss %s -i %s -an -vcodec png -r 1 -vframes 1 -y %s' % (
      timedelta_to_ffmpeg_string(curr), input_file, output_file
    )
    result = run_and_log(ffmpeg_cmd)
