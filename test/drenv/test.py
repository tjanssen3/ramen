# SPDX-FileCopyrightText: The RamenDR authors
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import os
import sys

import yaml

config = None
log = None
parser = None
log_format = "%(asctime)s %(levelname)-7s [%(name)s] %(message)s"


def start(name, file, config_file="config.yaml"):
    global config, parser, log

    # Setting up logging and sys.excepthook must be first so any failure will
    # be reported using the logger.
    log = logging.getLogger(name)
    sys.excepthook = _excepthook

    # We start with info level. After parsing the command line we may change
    # the level to debug.
    logging.basicConfig(level=logging.INFO, format=log_format)

    # Change directory so the test script can run from any directory.
    os.chdir(os.path.dirname(file))

    with open(config_file) as f:
        config = yaml.safe_load(f)

    parser = argparse.ArgumentParser(name)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Be more verbose.",
    )


def add_argument(*args, **kw):
    parser.add_argument(*args, **kw)


def parse_args():
    args = parser.parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)
    debug("Parsed arguments: %s", args)
    return args


def info(fmt, *args):
    log.info(fmt, *args)


def debug(fmt, *args):
    log.debug(fmt, *args)


def _excepthook(t, v, tb):
    log.exception("test failed", exc_info=(t, v, tb))