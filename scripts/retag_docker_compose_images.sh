#!/bin/bash
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Run this to retag the images created by the `docker compose build`, specifically
# the images with that has a prefix `superset-`. E.g. `superset-superset`.

declare -a arr=("superset-oob")

# e.g. VERSION=6.0.0-alpha.15
if [ -z "$1" ]; then
  echo "Usage: $0 <VERSION>"
  exit 1
fi
VERSION=$1

# TODO: Handle gcloud auth login

REPO="us-central1-docker.pkg.dev/cpl-dspm-l-sandbox-02/sky-dev-joey-andres"

for i in "${arr[@]}"
do
    FINAL_IMAGE="${REPO}/${i}:${VERSION}"
    #docker tag superset-$i $i # Only relevant if image is from docker-compose build
    docker tag $i $FINAL_IMAGE
    docker push $FINAL_IMAGE
done
