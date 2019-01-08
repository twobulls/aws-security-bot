#! /usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import bullkit
from datetime import datetime, timedelta
from pytz import timezone
import yaml

def iamkeys (commandargs):
	expired_keys = {}
	keys_to_warn = {}

	# Iterate through each IAM user.
	bullkit.debug('Getting the list of IAM users...', commandargs)
	iam = boto3.resource('iam')
	for iam_user in iam.users.all():
		# Iterate through each of the IAM user's access keys.
		iam_user_name = iam_user.name
		bullkit.debug('Checking the access keys of: {}'.format(iam_user_name), commandargs)
		for access_key in iam.User(iam_user_name).access_keys.all():
			access_key_id = access_key.access_key_id
			bullkit.debug('Checking access key: {}'.format(access_key_id), commandargs)

			# Calculate the age of the keys (converting to UTC where necessary).
			utcnow = timezone('UTC').localize(datetime.utcnow())
			access_key_age = utcnow - access_key.create_date
			bullkit.debug('Access key\'s age: {}'.format(access_key_age), commandargs)
			access_key_warn_age = timedelta(days = float(commandargs.parse_args().iam_keys_warn_age))
			access_key_expire_age = timedelta(days = float(commandargs.parse_args().iam_keys_expire_age))

			# If the key is approaching expiration...
			if access_key_age >= access_key_warn_age and access_key_age < access_key_expire_age and access_key.status == 'Active':
				bullkit.debug('Key {} is approaching expiration.'.format(access_key_id), commandargs)
				# Assemble the keys into lists with the user name as their key. Each item in the list is a dict containing the key's ID and time until expiration.
				if not keys_to_warn.get(iam_user_name):
					keys_to_warn[iam_user_name] = []
				key_approaching_expiration = {'id': access_key_id, 'time left': access_key_expire_age - access_key_age}
				keys_to_warn[iam_user_name].append(key_approaching_expiration)

			# If the key is expired...
			if access_key_age >= access_key_expire_age and access_key.status == 'Active':
				bullkit.debug('Key {} is expired.'.format(access_key_id), commandargs)
				# Assemble the keys into lists with the user name as their key.
				if not expired_keys.get(iam_user_name):
					expired_keys[iam_user_name] = []
				expired_keys[iam_user_name].append(access_key_id)

	# If we didn't find any access keys that are approaching expiration or have expired...
	if not keys_to_warn and not expired_keys:
		bullkit.debug('No issues found with access keys.', commandargs)
	
	# If we found access keys that are approaching expiration or have expired...
	else:
		# Since it's uncertain how many parts to this message there will be, store them in a list and collapse it into a string at the end.
		slackmsg_list = []

		if keys_to_warn:
			# Format the list into a string for a Slack message.
			bullkit.debug('Found these access keys that are approaching expiration: {}'.format(keys_to_warn), commandargs)
			bullkit.debug('Formatting the list of keys that expire soon...', commandargs)
			keys_to_warn_list = []
			for iam_user_name, access_key in keys_to_warn.items():
				access_key_id = access_key[0]['id']
				access_key_days_left = access_key[0]['time left'].days
				keys_to_warn_list.append('{}: {} (expires in {} days)'.format(iam_user_name, access_key_id, access_key_days_left))
			keys_to_warn_str = '\n'.join(keys_to_warn_list)
			slackmsg_list.append('The following IAM access keys expire soon:\n```{}```\nThey should be deactivated and replaced ASAP.'.format(keys_to_warn_str))

		if expired_keys:
			# Format the list into a string for a Slack message.
			bullkit.debug('Found these expired access keys: {}'.format(expired_keys), commandargs)
			bullkit.debug('Formatting the list of expired access keys...', commandargs)
			expired_keys_list = []
			for iam_user_name, access_key in expired_keys.items():
				expired_key = '{}: {}'.format(iam_user_name, access_key)
				expired_keys_list.append(expired_key)
			expired_keys_str = '\n'.join(expired_keys_list)
			slackmsg_list.append('The following IAM access keys are expired:\n```{}```\nThey should be deactivated and replaced immediately.'.format(expired_keys_str))

		# Collapse the list of message parts into one string.
		slackmsg = '\n\n'.join(slackmsg_list)

		# If we've been told to post to Slack...
		if not commandargs.parse_args().no_slack:
			# Post the list to the relevant Slack channel.
			bullkit.debug('Sending the list to Slack...', commandargs)
			bullkit.send_slack_message(commandargs.parse_args().iam_keys_channel, 'AWS Security Bot', ':robot_face:', slackmsg, commandargs)

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
				bullkit.debug('Loaded:\n{}'.format(slack_users), commandargs)

				# If we were able to assemble a map of AWS users to Slack users...
				if slack_users:
					# Assemble a list of users that need notification.
					bad_iam_users = [*keys_to_warn, *expired_keys]

					# Try to message each user directly via Slack.
					bullkit.debug('Iterating through bad AWS users to see if we can Slack them directly...', commandargs)
					for bad_iam_user in bad_iam_users:
						if bad_iam_user in slack_users.keys():
							bad_slack_user = slack_users[bad_iam_user]
							if bad_slack_user is not False:
								bullkit.debug('Trying to message @{}'.format(bad_slack_user), commandargs)

								# Assemble the Slack message.
								slackmsg_list = []
								slackmsg_list.append('Hi, it\'s me, your friendly AWS Security Bot!')
								if bad_iam_user in expired_keys:
									bad_iam_users_str = '\n'.join(expired_keys[bad_iam_user])
									slackmsg_list.append('You have the following IAM access key(s) that have expired. You must deactivate them immediately.\n```{}```'.format(bad_iam_users_str))
								if bad_iam_user in keys_to_warn:
									keys_to_warn_list = []
									for access_key in keys_to_warn[bad_iam_user]:
										access_key_id = access_key['id']
										access_key_days_left = access_key['time left'].days
										keys_to_warn_list.append('{} (expires in {} days)'.format(access_key_id, access_key_days_left))
										keys_to_warn_str = '\n'.join(keys_to_warn_list)
									slackmsg_list.append('You have the following IAM access key(s) that are expiring soon. You must deactivate them before their stated expiration date.\n```{}```'.format(keys_to_warn_str))
								slackmsg_list.append('For instructions on deactivating your access keys and replacing them with new ones, please visit http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_RotateAccessKey and perform the steps in the section titled: `To rotate access keys without interrupting your applications (console)`')
								slackmsg = '\n\n'.join(slackmsg_list)
								bullkit.debug('Message body: {}'.format(slackmsg), commandargs)

								# Send the Slack message.
								bad_slack_user = slack_users[bad_iam_user]
								bullkit.send_slack_message('@{}'.format(bad_slack_user), 'AWS Security Bot', ':robot_face:', slackmsg, commandargs)
							else:
								bullkit.debug('Ignoring {} because it\'s set to False in users.yml.'.format(bad_iam_user), commandargs)
						else:
							bullkit.debug('Couldn\'t find AWS user {} in the user map.'.format(bad_iam_user), commandargs)
							slackmsg='I don\'t know the Slack name of the AWS user `{}` so I could not send them a message directly. Please update my `users.yml` file so I can message them in the future.'.format(bad_iam_user)
							bullkit.send_slack_message(commandargs.parse_args().iam_keys_channel, 'AWS Security Bot', ':robot_face:', slackmsg, commandargs)

		# If we've been told to *not* post to Slack...
		else:
			# Print the list to standard output.
			print(slackmsg)
