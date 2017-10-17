#! /usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import bullkit
import yaml
from slackclient import SlackClient

def mfa(commandargs):
	# Iterate through each IAM user.
	bullkit.debug('Getting the list of IAM users...', commandargs)
	bad_users = []
	iam = boto3.resource('iam')
	for user in iam.users.all():
		# Iterate through each of the IAM user's MFA devices and note if none exist.
		bullkit.debug('Checking the MFA devices of: ' + user.name, commandargs)
		if not list(user.mfa_devices.all()):
			bullkit.debug('No MFA devices found for: ' + user.name, commandargs)
			bad_users.append(user.name)
	bullkit.debug('List of AWS users without MFA assembled: ' + str(bad_users), commandargs)

	# Format the list of users for Slack.
	if bad_users:
		slackmsg = 'The following AWS users have not enabled multi factor authentication:\n```' + '\n'.join(bad_users) + '```\nThey should each visit http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html and perform the steps in the section titled: `Enable a Virtual MFA Device for an IAM User (AWS Management Console)`'
	else:
		slackmsg = 'All AWS users have enabled multi factor authentication. Yay!'

	# If we've been told to post to Slack...
	if not commandargs.parse_args().noslack:
		# Post the list to the relevant Slack channel.
		slack = SlackClient(commandargs.parse_args().slacktoken)
		slackresult = slack.api_call('chat.postMessage', channel=commandargs.parse_args().mfachannel, username='AWS Security Bot', icon_emoji=':robot_face:', text=slackmsg)

		# Make sure the post was successful.
		if slackresult['ok'] is not True:
			bullkit.abort('Posting to Slack was unsuccessful. Slack said:\n' + str(slackresult))

		# If there are users who need to enable MFA and we've been told to nag them...
		if bad_users and commandargs.parse_args().mfanagusers:
			# Load the map of AWS users to Slack users.
			bullkit.debug('Trying to load the map of AWS users to Slack users...', commandargs)
			try:
				with open('users.yml', 'r') as stream:
					try:
						slack_users = yaml.safe_load(stream)
					except yaml.YAMLError as exc:
						print(exc)
			except IOError:
				bullkit.debug('users.yml can\'t be read, so we\'ll skip messaging Slack users directly.', commandargs)
			bullkit.debug('Loaded:\n' + str(slack_users), commandargs)

			# Try to message each user directly via Slack.
			if slack_users:
				bullkit.debug('Iterating through bad AWS users to see if we can Slack them directly...', commandargs)
				for bad_user in bad_users:
					if bad_user in slack_users.keys():
						bullkit.debug('Trying to message @' + slack_users[bad_user], commandargs)
						slackmsg = 'Hi, it\'s me, your friendly AWS Security Bot! It looks like your AWS user (' + bad_user + ') doesn\'t have MFA (i.e. two-factor authentication) enabled. This is an important security feature that you should enable, so please visit http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html and perform the steps in the section titled: `Enable a Virtual MFA Device for an IAM User (AWS Management Console)`'
						slackresult = slack.api_call('chat.postMessage', channel='@' + slack_users[bad_user], username='AWS Security Bot', icon_emoji=':robot_face:', text=slackmsg)

						# Make sure the post was successful.
						if slackresult['ok'] is not True:
							bullkit.abort('Posting to Slack was unsuccessful. Slack said:\n' + str(slackresult))

	# If we've been told to *not* post to Slack...
	else:
		# Print the list to standard output.
		print slackmsg
