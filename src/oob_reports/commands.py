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
import ossaudiodev
import zipfile
import uuid
import io
from pathlib import Path

import yaml

from oob_reports.client import SupersetClient

logger = logging.getLogger(__name__)


def import_oob_reports(
    tenant_id: str
) -> None:
    """
    Imports OOB reports from a git repository or a local directory.
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
                        
                        # Replace tenant_id
                        content = content.replace('{{ tenant_id }}', tenant_id)

                        # Replace UUIDs
                        for old, new in uuid_map.items():
                            content = content.replace(old, new)
                        
                        zipf.writestr(str(rel_path), content.encode('utf-8'))
                    else:
                        zipf.write(abs_path, arcname=str(rel_path))
        
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
        client.import_report(f"{bundle_name}.zip", zip_data)
