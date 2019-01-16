#! /usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import yaml

def mfa(bullkit):
	# Iterate through each IAM user.
	bullkit.debug('Getting the list of IAM users...')
	bad_iam_users = []
	iam = boto3.resource('iam')
	for iam_user in iam.users.all():
		# If the user doesn't have an MFA device...
		user_name = iam_user.name
		bullkit.debug('Checking IAM user: {}'.format(user_name))
		if not list(iam_user.mfa_devices.all()):
			bullkit.debug('No MFA devices found for: {}'.format(user_name))

			# Try to get the user's login profile. If we can, that means they have a password.
			try:
				# Note that the user is "bad" because they have a password but no MFA.
				null = iam.LoginProfile(user_name).create_date
				bullkit.debug('Password found for: {}'.format(user_name))
				bad_iam_users.append(user_name)
			except iam.meta.client.exceptions.NoSuchEntityException:
				bullkit.debug('No password found for: {}'.format(user_name))
	bullkit.debug('List of AWS users without MFA assembled: {}'.format(bad_iam_users))

	# Format the list of users for Slack.
	if bad_iam_users:
		bad_iam_users_str = '\n'.join(bad_iam_users)
		slackmsg = 'The following AWS users have not enabled multi factor authentication:\n```{}```\nThey should each visit http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html and perform the steps in the section titled: `Enable a Virtual MFA Device for an IAM User (AWS Management Console)`'.format(bad_iam_users_str)
	else:
		slackmsg = 'All AWS users have enabled multi factor authentication. Yay!'

	# If we've been told to post to Slack...
	if not bullkit.commandargs.parse_args().no_slack:
		# Post the list to the relevant Slack channel.
		bullkit.send_slack_message(bullkit.commandargs.parse_args().mfa_channel, 'AWS Security Bot', ':robot_face:', slackmsg)

		# If there are users who need to enable MFA and we've been told to nag them...
		if bad_iam_users and bullkit.commandargs.parse_args().mfa_nag_users:
			# Load the map of AWS users to Slack users.
			bullkit.debug('Trying to load the map of AWS users to Slack users...')
			try:
				with open('users.yml', 'r') as stream:
					try:
						slack_users = yaml.safe_load(stream)
					except yaml.YAMLError as exc:
						print(exc)
			except IOError:
				bullkit.debug('users.yml can\'t be read, so we\'ll skip messaging Slack users directly.')
			bullkit.debug('Loaded:\n{}'.format(slack_users))

			# Try to message each user directly via Slack.
			if slack_users:
				bullkit.debug('Iterating through bad AWS users to see if we can Slack them directly...')
				for bad_iam_user in bad_iam_users:
					if bad_iam_user in slack_users.keys():
						if slack_users[bad_iam_user] is not False:
							bad_slack_user = slack_users[bad_iam_user]
							bullkit.debug('Trying to message @{}'.format())
							slackmsg = 'Hi, it\'s me, your friendly AWS Security Bot! It looks like your AWS user (`{}`) doesn\'t have MFA (i.e. two-factor authentication) enabled. This is an important security feature that you should enable, so please visit http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html and perform the steps in the section titled: `Enable a Virtual MFA Device for an IAM User (AWS Management Console)`'.format(bad_iam_user)
							bullkit.send_slack_message('@{}'.format(bad_slack_user), 'AWS Security Bot', ':robot_face:', slackmsg)
						else:
							bullkit.debug('Ignoring {} because it\'s set to False in users.yml.'.format(bad_iam_user))
					else:
						bullkit.debug('Couldn\'t find AWS user {} in the user map.'.format(bad_iam_user))
						slackmsg='I don\'t know the Slack name of the AWS user `{}` so I could not send them a message directly. Please update my `users.yml` file so I can message them in the future.'.format(bad_iam_user)
						bullkit.send_slack_message(bullkit.commandargs.parse_args().iam_keys_channel, 'AWS Security Bot', ':robot_face:', slackmsg)

	# If we've been told to *not* post to Slack...
	else:
		# Print the list to standard output.
		print(slackmsg)
