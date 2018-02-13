#!/usr/bin/env python3
#
# willikins.py --- taking care of jobs and picking up the slack on Slack
#
# Willikins is a simple harness for posting information about running
# jobs to a Slack server. You supply Willikins with your username and
# the command that is to be run. Willikins executes it and sends some
# information about the command back to you.

import argparse
import os 
import shlex
import subprocess
import string
import time

from slackclient import SlackClient
from subprocess  import Popen, PIPE

def format_output(stdout, stderr, rc, time):
  """
  Formats the output that is used in sending the message to the client,
  depending on the return code of the command.
  """

  template = string.Template("""
${greeting}!\n
I have finished executing your job. Its return code is `$rc`, which
$comment.\n
Your command took `$time` to run. I am attaching its output to this
message. If the command created any files, you will have to inspect
them manually.
  """)

  return template.substitute( {
    "greeting" : "Hello",
    "rc"       : rc,
    "comment"  : "looks good to me" if rc == 0 else "may indicate an error",
    "time"     : time
  } )

if __name__ == "__main__":

  ######################################################################
  # Parse command-line arguments
  ######################################################################

  parser = argparse.ArgumentParser(description="Executes job with prejudice")
  parser.add_argument("-u", "--user",                    action="store", type=str, help="ID of user to report to")
  parser.add_argument("command"     , metavar="COMMAND", action="store", type=str, help="Command to run"         )

  arguments = parser.parse_args()

  ######################################################################
  # Setting up the client
  ######################################################################
  #
  # Look for a direct channel to communicate with the user. If no such
  # channel is found, the program exits.

  token   = os.getenv("SLACK_BOT_TOKEN")
  user_id = arguments.user
  command = arguments.command

  sc          = SlackClient(token)
  im_channels = sc.api_call("im.list")
  channel_id  = None

  for channel in im_channels['ims']:
    if channel['user'] == user_id:
      channel_id = channel['id']

  assert channel_id

  ######################################################################
  # Run the command
  ######################################################################

  time_start     = time.process_time()
  commands       = shlex.split(command)
  p              = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
  stdout, stderr = p.communicate()
  rc             = p.returncode
  time_stop      = time.process_time()
  duration       = "{:2f} s".format(time_stop - time_start)
  message        = format_output(stdout, stderr, rc, duration)

  sc.api_call(
    "chat.postMessage",
      channel = channel_id,
      text    = message,
      as_user = False
  )
