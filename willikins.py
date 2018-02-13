#!/usr/bin/env python3
#
# willikins.py --- taking care of jobs and picking up the slack on Slack
#
# Willikins is a simple harness for posting information about running
# jobs to a Slack server. You supply Willikins with your username and
# the command that is to be run. Willikins executes it and sends some
# information about the command back to you.

import argparse
import json
import os 
import shlex
import string
import subprocess
import time

from cgi         import escape
from slackclient import SlackClient
from subprocess  import Popen, PIPE

def format_output(rc, time):
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

def format_attachments(stdout, stderr):
  """
  Formats the attachments of both `stdout` and `stderr` for a new
  message to the client.
  """

  attachments = []

  for text, description in zip( [stdout, stderr], ["`stdout`", "`stderr`"]):
    if not text:
      continue

    properties = {
      "title"   : description,
      "fallback": description,
      "text"    : escape(text),
      "mrkdwn"  : "false",
    }

    attachments.append(properties)

  return json.dumps(attachments)

if __name__ == "__main__":

  ######################################################################
  # Parse command-line arguments
  ######################################################################

  parser = argparse.ArgumentParser(description="Executes job with prejudice")
  parser.add_argument("-a", "--attach",                  action="store_true",           help="Attach command output instead of using a snippet")
  parser.add_argument("-u", "--user",                    action="store"     , type=str, help="ID of user to report to")
  parser.add_argument("command"     , metavar="COMMAND", action="store"     , type=str, help="Command to run"         )

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
  attach  = arguments.attach

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

  time_start     = time.perf_counter()
  commands       = shlex.split(command)
  p              = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
  stdout, stderr = p.communicate()
  rc             = p.returncode
  duration       = "{:2f} s".format(time.perf_counter() - time_start)
  message        = format_output(rc, duration)

  # TODO: make encoding configurable
  stdout = stdout.decode("utf-8")
  stderr = stderr.decode("utf-8")

  if attach:
    attachments = format_attachments(stdout, stderr)
  else:
    attachments = None

  sc.api_call(
    "chat.postMessage",
      channel     = channel_id,
      text        = message,
      attachments = attachments
  )

  # User wants us to *upload* the output of the command instead of
  # attaching it directly to the message.
  if not attach:
    for data, description in zip([stdout, stderr], ["stdout", "stderr"]):
      if not data:
        continue

      sc.api_call(
        "files.upload",
          channels = channel_id,
          content  = data,
          title    = description
      )
