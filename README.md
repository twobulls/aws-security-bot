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
  --no-slack            Print output to stdout rather than Slack. [env var:
                        NO_SLACK]
  --slack-token SLACK_TOKEN
                        Your Slack API token. Required unless you use --no-
                        slack. [env var: SLACK_TOKEN]
  --mfa                 Check for IAM users that don't have MFA enabled. [env
                        var: MFA]
  --mfa-channel MFA_CHANNEL
                        The Slack channel to which we should post the results
                        of the IAM user MFA check. [env var: MFA_CHANNEL]
  --mfa-nag-users       Send Slack messages directly to users who need to
                        enable MFA. Relies on a properly populated users.yml
                        file. [env var: MFA_NAG_USERS]
  --public-s3           Check for public S3 buckets. [env var: PUBLIC_S3]
  --public-s3-channel PUBLIC_S3_CHANNEL
                        The Slack channel to which we should post the results
                        of the public S3 bucket check. [env var:
                        PUBLIC_S3_CHANNEL]
  --iam-keys            Check for expired IAM access keys. [env var: IAM_KEYS]
  --iam-keys-channel IAM_KEYS_CHANNEL
                        The Slack channel to which we should post the results
                        of the expired IAM access key check. [env var:
                        IAM_KEYS_CHANNEL]
  --iam-keys-nag-users  Send Slack messages directly to users who need to
                        disable expired IAM access keys. Relies on a properly
                        populated users.yml file. [env var:
                        IAM_KEYS_NAG_USERS]
  --iam-keys-warn-age IAM_KEYS_WARN_AGE
                        The age (in days) of IAM access keys after which we
                        should start sending warnings. [env var:
                        IAM_KEYS_WARN_AGE]
  --iam-keys-expire-age IAM_KEYS_EXPIRE_AGE
                        The age (in days) that IAM access keys are not allowed
                        to exceed. [env var: IAM_KEYS_EXPIRE_AGE]
```

### Slack integration

To send messages on Slack, you must set up a bot in your Slack team. Specify your bot's API token using the `--slack-token` option. More information can be found in Slack's documentation: https://api.slack.com/bot-users

### Mapping IAM users to Slack users

When the tool finds an IAM user that doesn't have MFA enabled, it adds them to the list of MFA-less users reported at the end of execution. Optionally, it can also send a message directly to the user on Slack, pointing them to AWS's documentation on how to enable MFA. To make these direct messages possible, you must specify the `--mfa-nag-users` option and also map IAM user names to Slack user names in a YAML file named `users.yml`. For example, to have messages about the IAM user `alex_on_aws` sent to the Slack user `alex_on_slack`, your `users.yml` should look like:

```
---
alex_on_aws: alex_on_slack
```

### Necessary IAM permissions

This tool requires several IAM permissions in order to examine your account. The following IAM policy grants them:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "aws-security-bot-policy",
            "Effect": "Allow",
            "Action": [
                "iam:GenerateCredentialReport",
                "iam:GetCredentialReport",
                "iam:ListUsers",
                "iam:ListAccessKeys",
                "iam:ListMFADevices",
                "iam:GetLoginProfile",
                "s3:ListAllMyBuckets",
                "s3:GetBucketAcl"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

### Deploying with Serverless Framework
You can optionally deploy this service using Serverless Framework. 
It will run at 10:55am every weekday using the server's timezone. 
This has been tested with Serverless Framework v1.26.1.

###### Install Serverless Framework
First, install `npm` using whatever method you prefer, e.g.,
`brew install npm`

Then: 

`npm install -g serverless` 

###### Install pip packages
`pip install -r requirements.txt -t .`

###### Deploy
Replace `<stage>` and `<region>` in the call below. 
`sls deploy -s <stage> --region <region>`

This will use your default credentials in the `~/.aws/credentials` file. In order
to use a different profile do the following:
`AWS_PROFILE=other_profile sls deploy -s somestage --region some_region`

### Examples

Check for IAM users without MFA, but don't send any messages to Slack:

```
./aws-security-bot.py --mfa --no-slack
```

Check for public S3 buckets and notify the Slack channel `#storage`, also check for IAM users without MFA and notify the Slack user `@alex`:

```
./aws-security-bot.py --public-s3 --public-s3-channel '#storage' --mfa --mfa-channel '@alex' --slack-token E82i0ZaPDnWC
```
