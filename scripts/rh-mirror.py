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
import requests
import signal
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from datetime import datetime

LOCKFILE_NAME = "mirrorlock"


def parse_args():
    """
    Parse and establish the arguments we take in on the CLI
    """
    parser = ArgumentParser(description="Mirror a Red Hat mirror.")

    # Programmatic Things
    parser.add_argument("-b", "--base", dest="base",
                        help="The remote base URL of the OS you want to "
                        "mirror. (ex: http://mirror.rit.edu/centos)",
                        required=True)
    parser.add_argument("-v", "--version", dest="version",
                        help="The sub-version of the OS you want to mirror. "
                        "(ex: 6.7)",
                        required=True)
    parser.add_argument("-p", "--path", dest="path",
                        help="The local filesystem path to store your "
                        "mirror. (ex: /mnt/pub/centos/)",
                        required=True)
    parser.add_argument("--repoonly", dest="repoonly",
                        default=False, action='store_true',
                        help="repo metadata only (no packages).")

    return parser.parse_args()


def sanitize_base(base):
    """
    Ensure the base URL we got is legit.
    """
    if not base.startswith("http"):
        raise Exception("Base must be a valid HTTP(S) URL.")
    r = requests.get(base)
    if r.status_code != 200:
        raise Exception("Base URL is broken")

    return base


def sanitize_version(version, base):
    """
    Ensure the version number we got is legit.

    Sometimes the upstream repository will delete old versions unexpectedly
    since you theoretically should not be using them anyway. This doesnt
    work for us so if that happens, stop the job before its to late.
    """
    url = "%s/%s" % (base, version)
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("Verison URL %s is broken" % url)
    soup = BeautifulSoup(r.text, "html.parser")
    if len(soup.find_all('a')) < 5:
        raise Exception("This mirror has been deleted. You may need to "
                        "find a legacy source.")

    return version


def sanitize_path(path, version):
    """
    Ensure the local filesystem path we're supposed to write to is legit.
    """
    if "/" not in path:
        raise Exception("Path must be fully qualified.")

    if not os.path.isdir(path):
        os.mkdir(path)
    os.chdir(path)
    if not os.path.isdir(version):
        os.mkdir(version)
    os.chdir(version)

    return os.getcwd()


def test_write(path):
    """
    Try writing to the mirror target.
    """
    os.chdir(path)
    if os.path.isfile("%s/%s" % (path, LOCKFILE_NAME)):
        raise Exception("Lock file exists in %s" % path)

    with open(LOCKFILE_NAME, "w+") as fh:
        fh.write(datetime.now().isoformat())


def clone_mirror(path, base, version):
    """
    Clone a remote mirror to the local filesystem.
    """
    url = "%s/%s" % (base, version)
    lftp(path, url, True, True)


def find_repodirs(path):
    """
    Return a list of repodata directories.
    """
    repodirs = []
    for root, dirs, files in os.walk(path):
        for dir_ in dirs:
            if dir_ == "repodata":
                repodirs.append(os.path.join(root, dir_))

    return relativize_paths(path, repodirs)


def lftp(path, url, missing=True, delete=True):
    """
    Clone a directory from a remote HTTP endpoint to the local filesystem.
    """
    os.chdir(path)

    if missing is True:
        missing = "--only-missing"
    else:
        missing = ""

    if delete is True:
        delete = "--delete"
    else:
        delete = ""

    args = " ".join([missing, delete])
    command = "lftp -e 'open %s && mirror -v %s . && exit'" % (url, args)

    os.system(command)


def clone_repodata(path, base, version):
    """
    Clone the new repodata to the local filesystem.
    """
    os.chdir(path)

    repodirs = find_repodirs(path)

    for repodir in repodirs:
        url = "%s/%s/%s" % (base, version, repodir)
        lftp(os.path.join(path, repodir), url, False)

    os.chdir(path)


def relativize_paths(root, paths):
    """
    Take a list of fully-qualified paths and remove the root,
    thus making them relative to something.
    """
    clean_paths = []
    for path in paths:
        clean_paths.append(path.replace("%s/" % root, ''))

    return clean_paths


def remove_lockfile(path):
    """
    Remove a lockfile at the end of a repo.
    """
    lock = "%s/%s" % (path, LOCKFILE_NAME)
    if os.path.isfile(lock):
        os.remove(lock)


def main():
    """
    Main logic.
    """
    args = parse_args()
    base = sanitize_base(args.base)
    version = sanitize_version(args.version, base)
    # version = args.version
    path = sanitize_path(args.path, version)
    test_write(path)

    if args.repoonly is False:
        clone_mirror(path, base, version)

    clone_repodata(path, base, version)

    remove_lockfile(path)


def closeout(signal, frame):
    """
    Exit the program
    """
    print "\nClosing. You may need to delete the %s at "\
          "the mirror root." % LOCKFILE_NAME
    exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, closeout)
    main()
