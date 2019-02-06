#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Two Bulls Holdings Pty Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from slackclient import SlackClient

class Bullkit:
	def __init__(self, commandargs):
		self.commandargs = commandargs

		# If we're supposed to talk to Slack...
		if not self.commandargs.parse_args().no_slack:
			# ...fail if the API token hasn't been provided.
			if not self.commandargs.parse_args().slack_token:
				self.abort('--slack-token must be specified if you\'re not suppressing Slack output with --no-slack')

			# ...fail if we've not been told what Slack channel to use for MFA results.
			if self.commandargs.parse_args().mfa:
				if not self.commandargs.parse_args().mfa_channel:
					self.abort('--mfa-channel must be specified if you\'re using --mfa without --no-slack')

			# ...fail if we've not been told what Slack channel to use for public S3 results.
			if self.commandargs.parse_args().public_s3:
				if not self.commandargs.parse_args().public_s3_channel:
					self.abort('--public-s3-channel must be specified if you\'re using --public-s3 without --no-slack')

			# ...fail if we've not been told what Slack channel to use for IAM access key results.
			if self.commandargs.parse_args().iam_keys:
				if not self.commandargs.parse_args().iam_keys_channel:
					self.abort('--iam-keys-channel must be specified if you\'re using --iam-keys without --no-slack')

		# If we're supposed to check IAM keys...
		if self.commandargs.parse_args().iam_keys:
			# ...fail if a key warning age hasn't been provided.
			if not self.commandargs.parse_args().iam_keys_warn_age:
				self.abort('--iam-keys-warn-age must be specified if you\'re checking for expired IAM access keys with --iam-keys')

			# ...fail if a maximum key age hasn't been provided.
			if not self.commandargs.parse_args().iam_keys_expire_age:
				self.abort('--iam-keys-expire-age must be specified if you\'re checking for expired IAM access keys with --iam-keys')

			# ...fail if the maximum key age isn't greater than the key warning age.
			if int(self.commandargs.parse_args().iam_keys_warn_age) >= int(self.commandargs.parse_args().iam_keys_expire_age):
				self.abort('--iam-keys-expire-age must be greater than --iam-keys-warn-age')

	# Function for outputting text to stderr.
	def stderr(self, message):
		sys.stderr.write('{}\n'.format(message))

	# Function for outputting debug messages only if the "verbose" option is enabled.
	def debug(self, message):
		if self.commandargs.parse_args().v:
			self.stderr(message)

	# Function for outputting fatal error messages.
	def abort(self, message):
		self.stderr(message)
		quit()

	def send_slack_message(self, channel, my_name, my_emoji, message):
		# Connect to Slack if we haven't already.
		try:
			self.slack
		except AttributeError:
			self.debug('Initializing Slack object...')
			self.slack = SlackClient(self.commandargs.parse_args().slack_token)

		# Send the message.
		slackresult = self.slack.api_call('chat.postMessage', channel=channel, username=my_name, icon_emoji=my_emoji, text=message)

		# Make sure the post was successful.
		if slackresult['ok'] is not True:
			self.abort('Posting to Slack was unsuccessful. Slack said:\n{}'.format(slackresult))
		self.debug('Posting to Slack was successfull.')
