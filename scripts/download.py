import os
import os.path
import re
from occ_stream_common import *
from time import sleep
from datetime import timedelta
from datetime import datetime

OUTPUT_ROOT = '/home/public/media/occ-stream'
OUTPUT_FILENAME = 'raw.flv'
LOG_FILENAME = 'download.log'
RECORD_TRIES = 30
RECORD_INTERVAL = timedelta(minutes=2)
RTMPDUMP_PATH = '/home/gabe/occ-stream/rtmpdump-2.3/rtmpdump'
MIN_DURATION = timedelta(hours=1)

# create output directory
output_directory = '%s/%s' % (OUTPUT_ROOT, compute_datetime_path_string())
if not os.path.exists(output_directory):
  os.makedirs(output_directory)

# get the logger
logfile_path = '%s/%s' % (output_directory, LOG_FILENAME)
logger = setup_logger(logfile_path)
logging_context.register(logger, logfile_path)

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
