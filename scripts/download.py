import os.path
from occ_stream_common import *
from time import sleep
from datetime import timedelta
from datetime import datetime
from ConfigParser import ConfigParser

def print_usage():
  print 'usage: python download.py config_file\n'

def print_usage_and_exit():
  print_usage()
  exit(1)

if len(sys.argv) <= 1:
  print_usage_and_exit()

# read configuration file
config = ConfigParser()
config.read(sys.argv[1])

# create output directory
output_directory = '%s/%s' % (
  config.get('general', 'root_directory'), compute_datetime_path_string()
)
if not os.path.exists(output_directory):
  os.makedirs(output_directory)

# get the logger
logfile_path = '%s/%s' % (output_directory, config.get('log', 'filename'))
logger = setup_logger(logfile_path)
logging_context.register(logger, logfile_path)

# compute output path
output_file_path = '%s/%s' % (
  output_directory, config.get('recording', 'filename')
)
logger.info('saving output to %s' % output_file_path)

poll_tries = config.getint('recording', 'poll_tries')
poll_interval = parse_timedelta(config.get('recording', 'poll_interval'))
min_duration = parse_timedelta(config.get('recording', 'min_duration'))
duration = None
record_succeeded = False

for tries_remaining in range(poll_tries, 0, -1):
  try:
    # record the stream
    start_time = datetime.now()
    command = (
      'rtmpdump -v -y broadcast1 -r "rtmp://fss24.streamhoster.com/lv_occvideof1" -o %s -s "http://public.streamhoster.com/Resources/Flash/JWFLVMediaPlayer/mediaplayer.swf" -w 8ac08c568ab193b9e6d82ee9c0f6430a773f372a6afe6ef1ae735d58278430cd -x 50076' % (
        output_file_path
      )
    )
    result = run_and_log(command)
    if (result != 0):
      raise Exception('unexpected exit code: %d' % result)
    end_time = datetime.now()
    
    # ensure the duration matches the expected value
    duration = (end_time - start_time)
    logger.info('finished recording, duration: %s' % duration)
    if (duration < min_duration):
      raise Exception(
        'duration is less than the minimum value expected (%s)' % 
        min_duration
      )
  except Exception as error:
    logger.info('failed to record the stream: %s' % error)
    logger.info('trying again in %s (%d tries left) ...' % (
      poll_interval, tries_remaining
    ))
    sleep(poll_interval.seconds)
    continue
  record_succeeded = True
  break

if (not record_succeeded):
  raise Exception(
    'Failed to record stream after several attempts.  Giving up.'
  )

logger.info('Finished recording stream')

logger.info('Dumping frames to assist with editing')
dump_frames(input_file=output_file_path, end=duration)

logger.info('success!')
