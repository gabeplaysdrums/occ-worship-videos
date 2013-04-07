from ConfigParser import ConfigParser
from datetime import datetime
from datetime import timedelta
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from occ_stream_common import *
from time import sleep
import os
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
max_duration = parse_timedelta(config.get('recording', 'max_duration'))
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

  # log stream.js for diagnositc reasons
  #TODO: we might be able to compose the video URL from this scxript, rather
  # than hard-coding it
  logger.info('Requesting http://www.occ.org/_js/stream.js?_=1365360362926 for diagnostics')
  run_and_log('curl "http://www.occ.org/_js/stream.js?_=1365360362926" -H "Cookie: PHPSESSID=jvcsi4a8if39p9ub453lffor16; X-Mapping-elbhlnpj=598EF51A72E8FDF5A8CF6181180E5797; __utma=133793040.247792973.1360562815.1360562815.1365359500.2; __utmb=133793040.3.10.1365359500; __utmc=133793040; __utmz=133793040.1360562815.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)" -H "Accept-Encoding: gzip,deflate,sdch" -H "Host: www.occ.org" -H "Accept-Language: en-US,en;q=0.8" -H "User-Agent: Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36" -H "Accept: text/javascript, application/javascript, */*" -H "Referer: http://www.occ.org/" -H "X-Requested-With: XMLHttpRequest" -H "Connection: keep-alive"')

  short_video_count = 0

  for tries_remaining in range(poll_tries, 0, -1):
    try:
      # record the stream
      start_time = datetime.now()
      command = (
        'rtmpdump -v -y broadcast1 -r "rtmp://fss28.streamhoster.com/lv_occvideof1" -o %s -s "http://public.streamhoster.com/Resources/Flash/JWFLVMediaPlayer/mediaplayer.swf" -w 8ac08c568ab193b9e6d82ee9c0f6430a773f372a6afe6ef1ae735d58278430cd -x 50076' % (
          output_file_path
        )
      )
      result = run_and_log(command, max_duration.total_seconds())
      # timeout result (None) implies success (it usually means the stream was not taken down after the service ended)
      if (result != None and result != 0):
        raise Exception('unexpected exit code: %d' % result)
      end_time = datetime.now()
      
      # ensure the duration matches the expected value
      duration = (end_time - start_time)
      logger.info('finished recording, duration: %s' % duration)
      if (duration < min_duration):
        # rename the (valid) video file, so we don't overwrite it
        os.rename(
          output_file_path, 
          '%s.%d' % (output_file_path, short_video_count)
        )
        short_video_count += 1
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
