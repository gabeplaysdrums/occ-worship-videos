import os
import os.path
import re
import sys
from occ_stream_common import *
from time import sleep
import logging
from datetime import timedelta
from datetime import datetime

OUTPUT_ROOT = '/home/public/media/occ-stream'
OUTPUT_FILENAME = 'raw.flv'
RECORD_TRIES = 30
RECORD_INTERVAL = timedelta(minutes=2)
RTMPDUMP_PATH = '/home/gabe/occ-stream/rtmpdump-2.3/rtmpdump'
MIN_DURATION = timedelta(hours=1)

# get the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LoggerStream(object):
  """
  Fake file-like stream object that redirects writes to a logger instance.
  Reference: http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
  """
  def __init__(self, logger, log_level=logging.INFO):
    self.logger = logger
    self.log_level = log_level
    self.linebuf = ''
 
  def write(self, buf):
    for line in buf.rstrip().splitlines():
      self.logger.log(self.log_level, line.rstrip())

# create output directory
output_directory = '%s/%s' % (OUTPUT_ROOT, compute_datetime_path_string())
logger.info('creating output directory')
if not os.path.exists(output_directory):
  os.makedirs(output_directory)

# configure the logger
logfile_path = '%s/download.log' % output_directory
logger_handler = logging.FileHandler(logfile_path)
logger_handler.setFormatter(logging.Formatter(
  '%(asctime)s %(levelname)s %(message)s\r\n'
))
logger.addHandler(logger_handler)
 
sys.stdout = LoggerStream(logger, logging.INFO)
sys.stderr = LoggerStream(logger, logging.ERROR)

# compute output path
output_file_path = '%s/%s' % (output_directory, OUTPUT_FILENAME)
logger.info('saving output to %s' % output_file_path)

record_duration = None
record_succeeded = False

for tries_remaining in range(RECORD_TRIES, 0, -1):
  try:
    # record the stream
    start_time = datetime.now()
    command = (
      '%s -v -y broadcast1 -r "rtmp://fss24.streamhoster.com/lv_occvideof1" -o %s -s "http://public.streamhoster.com/Resources/Flash/JWFLVMediaPlayer/mediaplayer.swf" -w 8ac08c568ab193b9e6d82ee9c0f6430a773f372a6afe6ef1ae735d58278430cd -x 50076' % (
        RTMPDUMP_PATH, output_file_path
      )
    )
    result = run_and_log(command)
    if (result != 0):
      raise Exception('unexpected exit code: %d' % result)
    end_time = datetime.now()
    
    # ensure the duration matches the expected value
    record_duration = (end_time - start_time)
    logger.info('finished recording, duration: %s' % record_duration)
    if (record_duration < MIN_DURATION):
      raise Exception(
        'duration is less than the minimum value expected (%s)' % 
        MIN_DURATION
      )
  except Exception as error:
    logger.info('failed to record the stream: %s' % error)
    logger.info('trying again in %s (%d tries left) ...' % (
      RECORD_INTERVAL, tries_remaining
    ))
    sleep(RECORD_INTERVAL.seconds)
    continue
  record_succeeded = True
  break

if (not record_succeeded):
  raise Exception(
    'Failed to record stream after several attempts.  Giving up.'
  )

logger.info('Finished recording stream')

logger.info('Dumping frames to assist with editing')
dump_frames(input_file=output_file_path, end=record_duration)

logger.info('success!')
