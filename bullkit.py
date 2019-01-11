#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from slackclient import SlackClient

# Function for outputting text to stderr.
def stderr(message):
	sys.stderr.write('{}\n'.format(message))

# Function for outputting debug messages only if the "verbose" option is enabled.
def debug(message, commandargs):
	if commandargs.parse_args().v:
		stderr(message)

# Function for outputting fatal error messages.
def abort(message):
	stderr(message)
	quit()

def send_slack_message(channel, my_name, my_emoji, message, commandargs):
	global slack

	# Connect to Slack if we haven't already.
	try:
		slack
	except NameError:
		debug('Initializing Slack object...', commandargs)
		slack = SlackClient(commandargs.parse_args().slack_token)

	# Send the message.
	slackresult = slack.api_call('chat.postMessage', channel=channel, username=my_name, icon_emoji=my_emoji, text=message)

	# Make sure the post was successful.
	if slackresult['ok'] is not True:
		abort('Posting to Slack was unsuccessful. Slack said:\n{}'.format(slackresult))
	debug('Posting to Slack was successfull.', commandargs)
