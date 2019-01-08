#! /usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import bullkit

def publics3 (commandargs):
	bad_buckets = {}
	bullkit.debug('Getting the list of S3 buckets...', commandargs)
	s3 = boto3.resource('s3')
	for bucket in s3.buckets.all():
		bullkit.debug('Checking the ACL of: ' + bucket.name, commandargs)
		for grant in s3.BucketAcl(bucket.name).grants:
			if grant['Grantee']['Type'] == 'Group' and 'URI' in grant['Grantee'].keys():
				if grant['Grantee']['URI'] in ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']:
					if not bad_buckets.get(bucket.name):
						bullkit.debug('Oh no, it\'s public!', commandargs)
						bad_buckets[bucket.name] = []
					bad_buckets[bucket.name].append(grant['Permission'])

	# If we didn't find any public buckets...
	if not bad_buckets:
		bullkit.debug('Found no public buckets.', commandargs)
		slackmsg = 'No S3 buckets have public permissions. Yay!'
	
	# If we found public buckets...
	else:
		# Format the list into a string for a Slack message.
		bullkit.debug('Found these public buckets: ' + str(bad_buckets), commandargs)
		bullkit.debug('Formatting the list of bad buckets...', commandargs)
		bad_buckets_formatted = []
		for bucket, privs in bad_buckets.items():
			bad_buckets_formatted.append(bucket + ': ' + str(privs))
		slackmsg = 'The following S3 buckets are public:\n```' + '\n'.join(bad_buckets_formatted) + '```\nYou should adjust their permissions immediately.'

	# If we've been told to post to Slack...
	if not commandargs.parse_args().no_slack:
		# Post the list to the relevant Slack channel.
		bullkit.debug('Posting our findings to Slack...', commandargs)
		bullkit.send_slack_message(commandargs.parse_args().public_s3_channel, 'AWS Security Bot', ':robot_face:', slackmsg, commandargs)

	# If we've been told to *not* post to Slack...
	else:
		# Print the list to standard output.
		print(slackmsg)
