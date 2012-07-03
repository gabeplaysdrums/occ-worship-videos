import os
import os.path
import re
import sys
from occ_stream_common import *

def print_usage():
  print 'python trim.py input ["start end" ...]\n'

def print_usage_and_exit():
  print_usage()
  exit(1)

if len(sys.argv) <= 1:
  print_usage_and_exit()

input = sys.argv[1]
outfile_prefix = get_file_prefix(input)
ffmpeg_cmd = 'ffmpeg -i %s -acodec copy -vcodec copy -f flv' % input
count = 0

for arg in sys.argv[2:]:
  m = re.search('^\s*(\d\d)\:(\d\d)\:(\d\d)\s+(\d\d)\:(\d\d)\:(\d\d)\s*$', arg)
  start_sec = hhmmss_to_seconds(m.group(1), m.group(2), m.group(3))
  end_sec = hhmmss_to_seconds(m.group(4), m.group(5), m.group(6))
  delta_sec = end_sec - start_sec
  start_hhmmss = '%s:%s:%s' % (m.group(1), m.group(2), m.group(3))
  delta_hhmmss = seconds_to_hhmmss(delta_sec)
  outfile = '%s-part%d.flv' % (outfile_prefix, (count + 1))
  temp_ffmpeg_cmd = '%s -ss %s -t %s %s' % (
    ffmpeg_cmd, start_hhmmss, delta_hhmmss, outfile
  )
  os.system(temp_ffmpeg_cmd)
  count = count + 1
