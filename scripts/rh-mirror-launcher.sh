#!/bin/bash

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

# Check that all of the required environment variables are there
check_vars() {
    if [ -z $baseurl ]; then
        echo "Need to set baseurl."
        exit 1
    fi
    if [ -z $fspath ]; then
        echo "Need to set fspath."
        exit 1
    fi
    if [ -z $version ]; then
        echo "Need to set version."
        exit 1
    fi
}
check_vars

# Base command to run
command="python scripts/rh-mirror.py"

# Check if we should do repodata only
if ! [ -z $repoonly ]; then
    command="$command --repoonly"
fi

# Run it!
eval "$command -p $fspath -v $version -b $baseurl"
