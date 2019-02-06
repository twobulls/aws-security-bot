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

import os
import configargparse
from bullkit import Bullkit

def main(*arg):
	# Parse command line options.
	commandargs = configargparse.ArgumentParser(description='This script performs various security checks on an Amazon Web Services account.')
	commandargs.add_argument('-v', env_var='VERBOSE', action="store_true", default=False, help='Print additional debugging output to stderr.')
	commandargs.add_argument('--no-slack', env_var='NO_SLACK', action="store_true", default=False, help='Print output to stdout rather than Slack.')
	commandargs.add_argument('--slack-token', env_var='SLACK_TOKEN', help='Your Slack API token. Required unless you use --no-slack.')
	commandargs.add_argument('--mfa', env_var='MFA', action="store_true", default=False, help='Check for IAM users that don\'t have MFA enabled.')
	commandargs.add_argument('--mfa-channel', env_var='MFA_CHANNEL', help='The Slack channel to which we should post the results of the IAM user MFA check.')
	commandargs.add_argument('--mfa-nag-users', env_var='MFA_NAG_USERS', action="store_true", default=False, help='Send Slack messages directly to users who need to enable MFA. Relies on a properly populated users.yml file.')
	commandargs.add_argument('--public-s3', env_var='PUBLIC_S3', action="store_true", default=False, help='Check for public S3 buckets.')
	commandargs.add_argument('--public-s3-channel', env_var='PUBLIC_S3_CHANNEL', help='The Slack channel to which we should post the results of the public S3 bucket check.')
	commandargs.add_argument('--iam-keys', env_var='IAM_KEYS', action="store_true", default=False, help='Check for expired IAM access keys.')
	commandargs.add_argument('--iam-keys-channel', env_var='IAM_KEYS_CHANNEL', help='The Slack channel to which we should post the results of the expired IAM access key check.')
	commandargs.add_argument('--iam-keys-nag-users', env_var='IAM_KEYS_NAG_USERS', action="store_true", default=False, help='Send Slack messages directly to users who need to disable expired IAM access keys. Relies on a properly populated users.yml file.')
	commandargs.add_argument('--iam-keys-warn-age', env_var='IAM_KEYS_WARN_AGE', help='The age (in days) of IAM access keys after which we should start sending warnings.')
	commandargs.add_argument('--iam-keys-expire-age', env_var='IAM_KEYS_EXPIRE_AGE', help='The age (in days) that IAM access keys are not allowed to exceed.')

	bk = Bullkit(commandargs)

	if commandargs.parse_args().mfa:
		import mfa
		mfa.mfa(bk)

	if commandargs.parse_args().public_s3:
		import publics3
		publics3.publics3(bk)

	if commandargs.parse_args().iam_keys:
		import iamkeys
		iamkeys.iamkeys(bk)

	return "AWS Security Bot ran succesfully."

# Only execute main() if we're being executed, not if we're being imported.
if __name__ == "__main__":
	main()
