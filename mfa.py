#! /usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import bullkit
import time
import csv
import yaml
from slackclient import SlackClient

def mfa(commandargs):
	# Get the credential report from AWS.
	bullkit.debug('Generating IAM report...', commandargs)
	iam = boto3.client('iam')
	bullkit.debug('Checking for the IAM report...', commandargs)
	while iam.generate_credential_report()['State'] != 'COMPLETE':
		time.sleep(2)
		bullkit.debug('Checking for the IAM report...', commandargs)

	bullkit.debug('Got the IAM report.', commandargs)
	users = iam.get_credential_report()['Content']

	# Figure out which column is 'mfa_active'.
	bullkit.debug('Figuring out which column in the report is \'mfa_active\'...', commandargs)
	for i, column in enumerate(csv.reader(users.splitlines()).next()):
		if column == 'mfa_active':
			break
	mfa_column_number = i
	bullkit.debug('It\'s column ' + str(mfa_column_number) + '.', commandargs)

	# Figure out which column is 'password_enabled'.
	bullkit.debug('Figuring out which column in the report is \'password_enabled\'...', commandargs)
	for i, column in enumerate(csv.reader(users.splitlines()).next()):
		if column == 'password_enabled':
			break
	password_column_number = i
	bullkit.debug('It\'s column ' + str(password_column_number) + '.', commandargs)

	# Iterate through the report and make a list of users with passwords but no MFA.
	bullkit.debug('Iterating through IAM report.', commandargs)
	bad_users = []
	for user in csv.reader(users.splitlines()):
		if user[mfa_column_number] == 'false':
			if user[password_column_number] != 'false':
				bad_users.append(user[0])
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
					if slack_users[bad_user]:
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
