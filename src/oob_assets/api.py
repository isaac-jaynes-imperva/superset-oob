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
from flask import Flask, jsonify, request # pylint: disable=E0401
from src.oob_assets.commands import import_oob_assets # pylint: disable=E0401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/import", methods=["POST"])
def import_assets():
    """
    Import OOB assets.
    """
    data = request.get_json()
    tenant_id = data.get("tenant_id")

    if not tenant_id:
        return jsonify({"error": "tenant_id is required"}), 400

    try:
        import_oob_assets(
            tenant_id=tenant_id
        )
        return jsonify({"message": "Import started"}), 202
    except Exception as e:
        logger.exception("Failed to import OOB assets")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082, debug=True)
