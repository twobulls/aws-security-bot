#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import configargparse
import bullkit

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

	# If we're supposed to talk to Slack...
	if not commandargs.parse_args().no_slack:
		# ...fail if the API token hasn't been provided.
		if not commandargs.parse_args().slack_token:
			bullkit.abort('--slack-token must be specified if you\'re not suppressing Slack output with --no-slack')

		# ...fail if we've not been told what Slack channel to use for MFA results.
		if commandargs.parse_args().mfa:
			if not commandargs.parse_args().mfa_channel:
				bullkit.abort('--mfa-channel must be specified if you\'re using --mfa without --no-slack')

		# ...fail if we've not been told what Slack channel to use for public S3 results.
		if commandargs.parse_args().public_s3:
			if not commandargs.parse_args().public_s3_channel:
				bullkit.abort('--public-s3-channel must be specified if you\'re using --public-s3 without --no-slack')

		# ...fail if we've not been told what Slack channel to use for IAM access key results.
		if commandargs.parse_args().iam_keys:
			if not commandargs.parse_args().iam_keys_channel:
				bullkit.abort('--iam-keys-channel must be specified if you\'re using --iam-keys without --no-slack')

	# If we're supposed to check IAM keys...
	if commandargs.parse_args().iam_keys:
		# ...fail if a key warning age hasn't been provided.
		if not commandargs.parse_args().iam_keys_warn_age:
			bullkit.abort('--iam-keys-warn-age must be specified if you\'re checking for expired IAM access keys with --iam-keys')

		# ...fail if a maximum key age hasn't been provided.
		if not commandargs.parse_args().iam_keys_expire_age:
			bullkit.abort('--iam-keys-expire-age must be specified if you\'re checking for expired IAM access keys with --iam-keys')

		# ...fail if the maximum key age isn't greater than the key warning age.
		if commandargs.parse_args().iam_keys_warn_age >= commandargs.parse_args().iam_keys_expire_age:
			bullkit.abort('--iam-keys-expire-age must be greater than --iam-keys-warn-age')

	if commandargs.parse_args().mfa:
		import mfa
		mfa.mfa(commandargs)

	if commandargs.parse_args().public_s3:
		import publics3
		publics3.publics3(commandargs)

	if commandargs.parse_args().iam_keys:
		import iamkeys
		iamkeys.iamkeys(commandargs)

	return "AWS Security Bot ran succesfully."


# Only execute main() if we're being executed, not if we're being imported.
if __name__ == "__main__":
	main()
