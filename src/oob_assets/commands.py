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
import os
from typing import Optional
import zipfile
import uuid
import io
from pathlib import Path

import yaml

from oob_assets.client import SupersetClient

logger = logging.getLogger(__name__)


def import_oob_assets(
    tenant_id: Optional[str] = None
) -> None:
    """
    Imports OOB assets from a git repository or a local directory.
    """

    superset_host = os.environ.get("SUPERSET_HOST", "http://superset:8088")
    superset_username = os.environ.get("SUPERSET_USERNAME", "admin")
    superset_password = os.environ.get("SUPERSET_PASSWORD", "admin")

    client = SupersetClient(superset_host, superset_username, superset_password)
    client.login()

    bundles_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../resources'))

    for bundle_name in os.listdir(bundles_dir):
        bundle_path = Path(os.path.join(bundles_dir, bundle_name))
        if not bundle_path.is_dir():
            continue

        database_file = None
        db_dir = bundle_path / "databases"
        if db_dir.is_dir():
            for file in os.listdir(db_dir):
                if file.endswith((".yaml", ".yml")):
                    database_file = f"databases/{file}"
                    break
        
        secrets = {}
        secret_types = {
            "passwords": "PASSWORD",
            "ssh_tunnel_passwords": "SSH_TUNNEL_PASSWORD",
            "ssh_tunnel_private_key_passwords": "SSH_TUNNEL_PRIVATE_KEY_PASSWORD",
            "ssh_tunnel_private_keys": "SSH_TUNNEL_PRIVATE_KEY",
        }

        if database_file:
            for secret_key, env_var_suffix in secret_types.items():
                env_var_name = f"{bundle_name.upper()}_{env_var_suffix}"
                secret_content = os.environ.get(env_var_name)
                if secret_content:
                    logger.info("Found %s for %s in environment variable", secret_key, bundle_name)
                    secrets[secret_key] = {database_file: secret_content}

        uuid_map = {}
        all_yaml_files = []
        for root, _, files in os.walk(bundle_path):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    all_yaml_files.append(os.path.join(root, file))

        # First pass: build UUID map
        for file_path in all_yaml_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if isinstance(config, dict) and 'uuid' in config:
                        old_uuid = config['uuid']
                        if old_uuid not in uuid_map:
                            uuid_map[old_uuid] = str(uuid.uuid4())
            except (yaml.YAMLError, IOError) as ex:
                logger.warning("Could not process YAML file %s: %s", file_path, ex)
                continue

        # Second pass: create zip with modified contents in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zipf:
            for root, _, files in os.walk(bundle_path):
                for file in files:
                    if file == '.DS_Store':
                        continue
                    
                    abs_path = Path(root) / file
                    rel_path = abs_path.relative_to(bundle_path)

                    if file.endswith((".yaml", ".yml")):
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        content_yaml = yaml.safe_load(content)
                        template = content_yaml.get('template', False) if isinstance(content_yaml, dict) else False
                        
                        # Replace tenant_id if it's not a template
                        if tenant_id and not template:
                            content = content.replace('{{ tenant_id }}', tenant_id)

                        # Replace UUIDs
                        for old, new in uuid_map.items():
                            content = content.replace(old, new)
                        
                        zipf.writestr(str(Path(bundle_name) / rel_path), content.encode('utf-8'))
                    else:
                        zipf.write(abs_path, arcname=str(Path(bundle_name) / rel_path))
        
        # Get the zip data from the buffer
        zip_data = zip_buffer.getvalue()

        # For debugging: write the zip file to the .tmp folder
        # tmp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', '.tmp'))
        # os.makedirs(tmp_dir, exist_ok=True)
        # debug_zip_path = os.path.join(tmp_dir, f'debug_{bundle_name}.zip')
        # with open(debug_zip_path, 'wb') as f:
        #     f.write(zip_data)
        # logger.info("Saved debug zip file to: %s", debug_zip_path)
        
        # Call the single import endpoint for the whole bundle
        client.import_asset(f"{bundle_name}.zip", zip_data, **secrets)
