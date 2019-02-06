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

import boto3

def publics3 (bullkit):
	bad_buckets = {}
	bullkit.debug('Getting the list of S3 buckets...')
	s3 = boto3.resource('s3')
	for bucket in s3.buckets.all():
		bullkit.debug('Checking the ACL of: {}'.format(bucket.name))
		for grant in s3.BucketAcl(bucket.name).grants:
			if grant['Grantee']['Type'] == 'Group' and 'URI' in grant['Grantee'].keys():
				if grant['Grantee']['URI'] in ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']:
					if not bad_buckets.get(bucket.name):
						bullkit.debug('Oh no, it\'s public!')
						bad_buckets[bucket.name] = []
					bad_buckets[bucket.name].append(grant['Permission'])

	# If we didn't find any public buckets...
	if not bad_buckets:
		bullkit.debug('Found no public buckets.')
		slackmsg = 'No S3 buckets have public permissions. Yay!'
	
	# If we found public buckets...
	else:
		# Format the list into a string for a Slack message.
		bullkit.debug('Found these public buckets: {}'.format(bad_buckets))
		bullkit.debug('Formatting the list of bad buckets...')
		bad_buckets_list = []
		for bucket, privs in bad_buckets.items():
			bad_bucket = '{}: {}'.format(bucket, privs)
			bad_buckets_list.append(bad_bucket)
		bad_buckets_str = '\n'.join(bad_buckets_list)
		slackmsg = 'The following S3 buckets are public:\n```{}```\nYou should adjust their permissions immediately.'.format(bad_buckets_str)

	# If we've been told to post to Slack...
	if not bullkit.commandargs.parse_args().no_slack:
		# Post the list to the relevant Slack channel.
		bullkit.debug('Posting our findings to Slack...')
		bullkit.send_slack_message(bullkit.commandargs.parse_args().public_s3_channel, 'AWS Security Bot', ':robot_face:', slackmsg)

	# If we've been told to *not* post to Slack...
	else:
		# Print the list to standard output.
		print(slackmsg)
