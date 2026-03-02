# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
import requests

logger = logging.getLogger(__name__)

class SupersetClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None

    def login(self):
        """
        Login to Superset and get a CSRF token.
        """
        auth_data = {
            "username": self.username,
            "password": self.password,
            "provider": "db",
        }
        resp = self.session.post(f"{self.host}/api/v1/security/login", json=auth_data)
        resp.raise_for_status()
        access_token = resp.json()["access_token"]
        self.session.headers["Authorization"] = f"Bearer {access_token}"

        # get csrf token
        resp = self.session.get(f"{self.host}/api/v1/security/csrf_token/")
        resp.raise_for_status()
        self.csrf_token = resp.json()["result"]
        self.session.headers["X-CSRFToken"] = self.csrf_token



    def import_asset(self, bundle_name: str, bundle_data: bytes) -> None:
        """
        Import a full asset bundle from in-memory data.
        """
        logger.info("Importing asset bundle for: %s", bundle_name)
        files = {'bundle': (bundle_name, bundle_data, 'application/zip')}
        resp = self.session.post(f"{self.host}/api/v1/assets/import/", files=files)
        try:
            resp.raise_for_status()
            logger.info("Successfully imported asset bundle for %s", bundle_name)
        except requests.exceptions.HTTPError as e:
            logger.error("Error importing asset bundle: %s", e.response.text)
            raise e
