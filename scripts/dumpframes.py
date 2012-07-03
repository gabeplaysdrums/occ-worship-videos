import sys
from occ_stream_common import *
from datetime import timedelta

logger = setup_logger()
logging_context.register(logger)

def print_usage():
  print 'python dumpframes.py input start end [step]\n'

def print_usage_and_exit():
  print_usage()
  exit(1)

if len(sys.argv) < 4:
  print_usage_and_exit()

input = sys.argv[1]
start = parse_timedelta(sys.argv[2])
end = parse_timedelta(sys.argv[3])
step = None

if len(sys.argv) > 4:
  step = parse_timedelta(sys.argv[4])

dump_frames(input_file=input, start=start, end=end, step=step)
