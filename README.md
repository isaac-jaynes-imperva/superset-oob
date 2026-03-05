# Superset OOB Assets Service

This service provides a mechanism for importing "Out-of-the-Box" (OOB) asset bundles into a running Superset instance.

## Exporting Superset Assets

Assets can be exported from Superset in a variety of locations. In the Dashboard list, there is an `export` action button, which will download a zip folder containing the dashboard and all associated assets, such as charts, datasets, and databases. This can be unzipped and added to a folder in the `/resources` directory of the `superset-oob` repo. This can similarly be done for Charts, Datasets, and Databases. Finally, `{{ tenant_id }}` can be added anywhere in the yaml files that need to have the tenant_id replaced. Add `template: true` to the yaml file if you would like `{{ tenant_id }}` NOT to be replaced, and wish to have the unaltered file uploaded to Superset. This is for Superset-side tenant provisioning.


## Asset Bundle Structure

Each subdirectory within the `/resources` directory is treated as a self-contained asset bundle. The service processes and imports each bundle individually. The directory structure inside a bundle must conform to the format expected by Superset's import functionality. In order to import correctly, all supporting assets will need to be in the folder. Not all asset types need to be present, you can for example only insert databases and datasets with no charts or dashboards.

A typical bundle layout looks like this:

```
resources/
└── oob_report_example/
    ├── metadata.yaml
    ├── charts/
    │   └── test_chart.yaml
    ├── dashboards/
    │   └── test_dashboard.yaml
    ├── databases/
    │   └── test_database.yaml
    ├── datasets/
    │   └── test_dataset.yaml
    └── reports/
        └── test_report.yaml
```

- **`metadata.yaml`**: Contains metadata about the exported assets.
- **`charts/`, `dashboards/`, `databases/`, `datasets/`, `reports/`**: These directories contain the YAML definitions for each asset type. The directory structure, including any subdirectories like `datasets/examples/`, is preserved in the final import package.

## How It Works

The import process is triggered by a POST request to the `/import` endpoint. For each asset bundle found in the `resources/` directory, the service performs the following steps:

1.  **UUID Management**: The service scans all `.yaml` files within the bundle to build a map of all existing UUIDs. It then generates a new, unique UUID for each old one. This ensures that re-importing a bundle creates new assets rather than overwriting existing ones.

2.  **Templating**: The service replaces all occurrences of the placeholder `{{ tenant_id }}` in the `.yaml` files with the `tenant_id` value provided in the API request.

3.  **Packaging**: The service creates a `.zip` archive containing all the files and folders from the bundle directory. The content of the YAML files includes the replaced UUIDs and `tenant_id`. This zip file is stored in memory.

4.  **Importing**: The final `.zip` file is sent in a single request to the `/api/v1/assets/import/` Superset API endpoint, which handles the import of all assets in the bundle.

## Running the service

This service is designed to be run as a Docker container.

### Prerequisites

*   Docker
*   A running Superset instance accessible from this service.

### Building the image

To build the Docker image, run the following command from the project root directory:

```bash
docker build -t superset-oob-assets .
```

### Running the container

To run the container, you can use the provided `docker-compose.yml` file:

```bash
docker-compose up --build
```

This will start the `oob-assets` service on port 8082. The service will attempt to connect to Superset at the address defined by the `SUPERSET_HOST` environment variable.

### Configuration

The service can be configured using the following environment variables:

*   `SUPERSET_HOST`: The URL of the Superset instance (default: `http://host.docker.internal:8088`)
*   `SUPERSET_USERNAME`: The username to use for authentication (default: `admin`)
*   `SUPERSET_PASSWORD`: The password to use for authentication (default: `admin`)

## Handling Secrets

To connect to certain databases, you may need to provide secrets like passwords or private keys. To handle these securely without checking them into the git repository, the import script can be configured with environment variables.

The script looks for environment variables with names based on the asset bundle's directory name. For a bundle located in a directory named `my_bundle`, the script will look for the following environment variables:

-   `MY_BUNDLE_PASSWORD`: For the database password.
-   `MY_BUNDLE_SSH_TUNNEL_PASSWORD`: For the SSH tunnel password.
-   `MY_BUNDLE_SSH_TUNNEL_PRIVATE_KEY_PASSWORD`: For the SSH tunnel's private key password.
-   `MY_BUNDLE_SSH_TUNNEL_PRIVATE_KEY`: For the SSH tunnel's private key.

### Formatting Secret Values

The value of these environment variables should be the raw secret content.

-   For a simple password, the value is the password itself.
-   For secrets that are JSON key files (like for Google BigQuery), the value should be the full content of the JSON file.

### Example

To provide a database password for a bundle named `oob_asset_secret`, you would set an environment variable like this before running the service:

```bash
export OOB_ASSET_SECRET_PASSWORD='your_database_password_here'
```

If your secret is a multi-line private key, you can set it like this:

```bash
export OOB_ASSET_SECRET_SSH_TUNNEL_PRIVATE_KEY='-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----'
```

Or for a JSON key file:

```bash
export OOB_ASSET_SECRET_PASSWORD='{"type": "service_account", "project_id": "...", ...}'
```

## Usage

To trigger the import of all OOB asset bundles, send a POST request to the `/import` endpoint with a `tenant_id`:

```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "tenant_id": "my_tenant"
}' http://localhost:8082/import
```

This single command will trigger the full import process described above for all bundles located in the `resources` directory.

