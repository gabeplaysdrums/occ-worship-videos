from ConfigParser import ConfigParser
from datetime import datetime
from datetime import timedelta
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from occ_stream_common import *
from time import sleep
import os.path
import smtplib

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
output_directory_name = compute_datetime_path_string()
output_directory = '%s/%s' % (
  config.get('general', 'root_directory'), output_directory_name
)
if not os.path.exists(output_directory):
  os.makedirs(output_directory)

# get the logger
logfile_path = '%s/%s' % (output_directory, config.get('log', 'filename'))
logger = setup_logger(logfile_path)
logging_context.register(logger, logfile_path)

def send_mail(subject, body):
  if config.has_section('mail'):
    from_addr = config.get('mail', 'from')
    to_addr = config.get('mail', 'to')
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP(
      config.get('mail', 'host'), config.getint('mail', 'port')
    )
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(from_addr, config.get('mail', 'password'))
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.close()

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
mail_subject = 'OCC stream download %s' % output_directory_name

send_mail(
  subject=mail_subject,
  body="""
<p>
Started downloading the OCC live video stream.  You will receive a follow-up email when the download completes.
</p>
"""
)

try:

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

  send_mail(
    subject=mail_subject,
    body="""
<p>
Downloaded the OCC live video stream successfully!
</p>
<p>
  <table border="1" cellpadding="5">
    <tr>
      <td><b>Output file:</b></td>
      <td>%s</td>
    </tr>
    <tr>
      <td><b>Duration:</b></td>
      <td>%s</td>
    </tr>
    <tr>
      <td><b>Log file:</b></td>
      <td>%s</td>
    </tr>
  </table>
</p>
""" % (
      output_file_path,
      duration,
      logfile_path
    )
  )
  
  logger.info('success!')

except Exception as error:

  logger.error('Failed to download the stream: %s' % error)
  logfile = open(logfile_path, 'r')
  send_mail(
    subject=mail_subject,
    body="""
<p>
Failed to download the OCC live video stream with the following error message:
</p>
<blockquote style="font-weight: bold; color: red;">%s</blockquote>
<p>
Here is the log:
<pre style="border-style: solid; border-width: 2px; border-color: gray; padding: 10px;">
%s
</pre>
</p>
""" % (
      error, logfile.read()
    )
  )
  logfile.close()
  raise error
