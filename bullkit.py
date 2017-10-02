#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

# Function for outputting text to stderr.
def stderr(message):
	sys.stderr.write(message + '\n')

# Function for outputting debug messages only if the "verbose" option is enabled.
def debug(message, commandargs):
	if commandargs.parse_args().v:
		stderr(message)

# Function for outputting fatal error messages.
def abort(message):
	stderr(message)
	quit()