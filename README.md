# AWS Security Bot

## About

This tool performs various security checks on an Amazon Web Services account to ensure:

* All IAM users have multi-factor authentication enabled.
* No S3 buckets have any public permissions.
* All IAM users' access keys are below a certain age.

If a violation of those rules is found, it can either print its findings to standard output or send a message to Slack. It can even nag IAM users directly if you map their user names to Slack user names.

## Usage

Options may be provided either on the command line or in environment variables. Command line options are as follows, with their equivalent environment variable name noted at the end of each description:

```
  -v                    Print additional debugging output to stderr. [env var:
                        VERBOSE]
  --noslack             Print output to stdout rather than Slack. [env var:
                        NOSLACK]
  --slacktoken SLACKTOKEN
                        Your Slack API token. Required unless you use
                        --noslack. [env var: SLACKTOKEN]
  --mfa                 Check for IAM users that don't have MFA enabled. [env
                        var: MFA]
  --mfachannel MFACHANNEL
                        The Slack channel to which we should post the results
                        of the IAM user MFA check. [env var: MFACHANNEL]
  --mfanagusers         Send Slack messages directly to users who need to
                        enable MFA. Relies on a properly populated users.yml
                        file. [env var: MFANAGUSERS]
  --publics3            Check for public S3 buckets. [env var: PUBLICS3]
  --publics3channel PUBLICS3CHANNEL
                        The Slack channel to which we should post the results
                        of the public S3 bucket check. [env var:
                        PUBLICS3CHANNEL]
  --iamkeys             Check for expired IAM access keys. [env var: IAMKEYS]
  --iamkeyschannel IAMKEYSCHANNEL
                        The Slack channel to which we should post the results
                        of the expired IAM access key check. [env var:
                        IAMKEYSCHANNEL]
  --iamkeysnagusers     Send Slack messages directly to users who need to
                        disable expired IAM access keys. Relies on a properly
                        populated users.yml file. [env var: IAMKEYSNAGUSERS]
  --iamkeyswarnage IAMKEYSWARNAGE
                        The age (in days) of IAM access keys after which we
                        should start sending warnings. [env var:
                        IAMKEYSWARNAGE]
  --iamkeysexpireage IAMKEYSEXPIREAGE
                        The age (in days) that IAM access keys are not allowed
                        to exceed. [env var: IAMKEYSEXPIREAGE]
```

### Slack integration

To send messages on Slack, you must set up a bot in your Slack team. Specify your bot's API token using the `--slacktoken` option. More information can be found in Slack's documentation: https://api.slack.com/bot-users

### Mapping IAM users to Slack users

When the tool finds an IAM user that doesn't have MFA enabled, it adds them to the list of MFA-less users reported at the end of execution. Optionally, it can also send a message directly to the user on Slack, pointing them to AWS's documentation on how to enable MFA. To make these direct messages possible, you must specify the `--mfanagusers` option and also map IAM user names to Slack user names in a YAML file named `users.yml`. For example, to have messages about the IAM user `alex_on_aws` sent to the Slack user `alex_on_slack`, your `users.yml` should look like:

```
---
alex_on_aws: alex_on_slack
```

### Examples

Check for IAM users without MFA, but don't send any messages to Slack:

```
./aws-security-bot.py --mfa --noslack
```

Check for public S3 buckets and notify the Slack channel `#storage`, also check for IAM users without MFA and notify the Slack user `@alex`:

```
./aws-security-bot.py --publics3 --publics3channel '#storage' --mfa --mfachannel '@alex' --slacktoken E82i0ZaPDnWC
```
