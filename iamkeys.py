#! /usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import bullkit
from datetime import datetime, timedelta
from pytz import timezone
from slackclient import SlackClient
import yaml

def iamkeys (commandargs):
	expired_keys = {}
	keys_to_warn = {}

	# Iterate through each IAM user.
	bullkit.debug('Getting the list of IAM users...', commandargs)
	iam = boto3.resource('iam')
	for user in iam.users.all():
		# Iterate through each of the IAM user's access keys.
		bullkit.debug('Checking the access keys of: ' + user.name, commandargs)
		for access_key in iam.User(user.name).access_keys.all():
			bullkit.debug('Checking access key: ' + access_key.access_key_id, commandargs)

			# Calculate the age of the keys (converting to UTC where necessary).
			utcnow = timezone('UTC').localize(datetime.utcnow())
			access_key_age = utcnow - access_key.create_date
			bullkit.debug('Access key\'s age: ' + str(access_key_age), commandargs)
			access_key_warn_age = timedelta(days = float(commandargs.parse_args().iam_keys_warn_age))
			access_key_expire_age = timedelta(days = float(commandargs.parse_args().iam_keys_expire_age))

			# If the key is approaching expiration...
			if access_key_age >= access_key_warn_age and access_key_age < access_key_expire_age and access_key.status == 'Active':
				bullkit.debug('Key ' + access_key.access_key_id + ' is approaching expiration.', commandargs)
				# Assemble the keys into lists with the user name as their key. Each item in the list is a dict containing the key's ID and time until expiration.
				if not keys_to_warn.get(user.name):
					keys_to_warn[user.name] = []
				key_approaching_expiration = {'id': access_key.access_key_id, 'time left': access_key_expire_age - access_key_age}
				keys_to_warn[user.name].append(key_approaching_expiration)

			# If the key is expired...
			if access_key_age >= access_key_expire_age and access_key.status == 'Active':
				bullkit.debug('Key ' + access_key.access_key_id + ' is expired.', commandargs)
				# Assemble the keys into lists with the user name as their key.
				if not expired_keys.get(user.name):
					expired_keys[user.name] = []
				expired_keys[user.name].append(access_key.access_key_id)

	# If we didn't find any access keys that are approaching expiration or have expired...
	if not keys_to_warn and not expired_keys:
		bullkit.debug('No issues found with access keys.', commandargs)
	
	# If we found access keys that are approaching expiration or have expired...
	else:
		# Since it's uncertain how many parts to this message there will be, store them in a list and collapse it into a string at the end.
		slackmsg_list = []

		if keys_to_warn:
			# Format the list into a string for a Slack message.
			bullkit.debug('Found these access keys that are approaching expiration: ' + str(keys_to_warn), commandargs)
			bullkit.debug('Formatting the list of keys that expire soon...', commandargs)
			keys_to_warn_formatted = []
			for user, access_key in keys_to_warn.iteritems():
				keys_to_warn_formatted.append(user + ': ' + str(access_key[0]['id'] + ' (expires in ' + str(access_key[0]['time left'].days) + ' days)'))
			slackmsg_list.append('The following IAM access keys expire soon:\n```' + '\n'.join(keys_to_warn_formatted) + '```\nThey should be deactivated and replaced ASAP.')

		if expired_keys:
			# Format the list into a string for a Slack message.
			bullkit.debug('Found these expired access keys: ' + str(expired_keys), commandargs)
			bullkit.debug('Formatting the list of expired access keys...', commandargs)
			expired_keys_formatted = []
			for user, access_key in expired_keys.iteritems():
				expired_keys_formatted.append(user + ': ' + str(access_key))
			slackmsg_list.append('The following IAM access keys are expired:\n```' + '\n'.join(expired_keys_formatted) + '```\nThey should be deactivated and replaced immediately.')

		# Collapse the list of message parts into one string.
		slackmsg = '\n\n'.join(slackmsg_list)

		# If we've been told to post to Slack...
		if not commandargs.parse_args().no_slack:
			bullkit.debug('Sending the list to Slack...', commandargs)
			# Post the list to the relevant Slack channel.
			slack = SlackClient(commandargs.parse_args().slack_token)
			slackresult = slack.api_call('chat.postMessage', channel=commandargs.parse_args().iam_keys_channel, username='AWS Security Bot', icon_emoji=':robot_face:', text=slackmsg)

			# Make sure the post was successful.
			if slackresult['ok'] is not True:
				bullkit.abort('Posting to Slack was unsuccessful. Slack said:\n' + str(slackresult))
			bullkit.debug('Sent successfully.', commandargs)

			# If there are users who need to deactivate their keys and we've been told to nag them...
			if commandargs.parse_args().iam_keys_nag_users:
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

				# If we were able to assemble a map of AWS users to Slack users...
				if slack_users:
					# Assemble a list of users that need notification.
					keys_to_warn_users = keys_to_warn.keys()
					expired_keys_users = expired_keys.keys()
					bad_users = keys_to_warn_users + expired_keys_users

					# Try to message each user directly via Slack.
					bullkit.debug('Iterating through bad AWS users to see if we can Slack them directly...', commandargs)
					for bad_user in bad_users:
						if bad_user in slack_users.keys():
							bullkit.debug('Trying to message @' + slack_users[bad_user], commandargs)

							# Assemble the Slack message.
							slackmsg_list = []
							slackmsg_list.append('Hi, it\'s me, your friendly AWS Security Bot!')
							if bad_user in expired_keys:
								slackmsg_list.append('You have the following IAM access key(s) that have expired. You must deactivate them immediately.\n```' + '\n'.join(expired_keys[bad_user]) + '```')
							if bad_user in keys_to_warn:
								keys_to_warn_formatted = []
								for access_key in keys_to_warn[bad_user]:
									keys_to_warn_formatted.append(str(access_key['id'] + ' (expires in ' + str(access_key['time left'].days) + ' days)'))
								slackmsg_list.append('You have the following IAM access key(s) that are expiring soon. You must deactivate them before their stated expiration date.\n```' + '\n'.join(keys_to_warn_formatted) + '```')
							slackmsg_list.append('For instructions on deactivating your access keys and replacing them with new ones, please visit http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_RotateAccessKey and perform the steps in the section titled: `To rotate access keys without interrupting your applications (console)`')
							slackmsg = '\n\n'.join(slackmsg_list)
							bullkit.debug('Message body: ' + slackmsg, commandargs)

							# Try to post the Slack message.
							slackresult = slack.api_call('chat.postMessage', channel='@' + slack_users[bad_user], username='AWS Security Bot', icon_emoji=':robot_face:', text=slackmsg)
							if slackresult['ok'] is not True:
								bullkit.abort('Posting to Slack was unsuccessful. Slack said:\n' + str(slackresult))
						else:
							bullkit.debug('Couldn\'t find AWS user ' + bad_user + ' in the user map.', commandargs)

		# If we've been told to *not* post to Slack...
		else:
			# Print the list to standard output.
			print slackmsg
