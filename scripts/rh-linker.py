#!/usr/bin/env python

# Copyright 2016 Grant Cohoe (grant.cohoe@rsa.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import signal
from argparse import ArgumentParser
from datetime import datetime

LOCKFILE_NAME = "mirrorlock"


def parse_args():
    """
    Parse and establish the arguments we take in on the CLI
    """
    parser = ArgumentParser(description="Mirror a Red Hat mirror.")

    # Programmatic Things
    parser.add_argument("-p", "--path", dest="path",
                        help="The local filesystem path to store your "
                        "mirror. (ex: /mnt/pub/centos/)",
                        required=True)
    parser.add_argument("-s", "--source", dest="source",
                        help="The source subdirectory (ex: 6.7)",
                        required=True)
    parser.add_argument("-d", "--destination", dest="destination",
                        help="The destination subdirectory (ex: 6)",
                        required=True)

    return parser.parse_args()


def sanitize_path(path):
    """
    Ensure the local filesystem path we're supposed to write to is legit.
    """
    if not path.startswith("/"):
        raise Exception("Path must be fully qualified.")

    os.chdir(path)
    return os.getcwd()


def test_write(path):
    """
    Try writing to the target.
    """
    os.chdir(path)

    with open(LOCKFILE_NAME, "w+") as fh:
        fh.write(datetime.now().isoformat())


def remove_lockfile(path):
    """
    Remove a lockfile at the end of a repo.
    """
    lock = "%s/%s" % (path, LOCKFILE_NAME)
    if os.path.isfile(lock):
        os.remove(lock)


def sanitize_source(path, source):
    """
    Ensure the source directory exists.
    """
    os.chdir(path)
    if not os.path.isdir(source):
        raise Exception("Source directory '%s' does not exist in "
                        "'%s'." % (source, path))

    return source


def sanitize_destination(path, destination):
    """
    Ensure the destination directory is either a symlink or doesnt exist.
    """
    os.chdir(path)
    if os.path.exists(destination):
        if not os.path.islink(destination):
            raise Exception("Destination directory '%s' is not a "
                            "symlink." % destination)

    return destination


def make_link(path, source, destination):
    """
    Create a symlink between the source and destination in a given path.
    """
    os.chdir(path)

    if source == destination:
        raise Exception("Source and Destination are the same ('%s')" % source)

    if os.path.islink(destination):
        os.remove(destination)

    os.symlink(source, destination)


def main():
    """
    Main logic.
    """
    args = parse_args()
    path = sanitize_path(args.path)
    test_write(path)
    source = sanitize_source(path, args.source)
    destination = sanitize_destination(path, args.destination)
    make_link(path, source, destination)
    remove_lockfile(path)


def closeout(signal, frame):
    """
    Exit the program
    """
    print "\nClosing."
    exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, closeout)
    main()
