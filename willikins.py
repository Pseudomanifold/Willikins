#!/usr/bin/env python3
#
# willikins.py --- taking care of jobs and picking up the slack on Slack
#
# Willikins is a simple harness for posting information about running
# jobs to a Slack server. You supply Willikins with your username and
# the command that is to be run. Willikins executes it and sends some
# information about the command back to you.

from slackclient import SlackClient

import argparse
import os 
import shlex
import subprocess

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

  sc.api_call(
    "chat.postMessage",
      channel = channel_id,
      text    = "This is a test!",
      as_user = False
  )
