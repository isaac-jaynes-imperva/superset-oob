# Superset OOB Assets Service

This service provides a mechanism for importing "Out-of-the-Box" (OOB) asset bundles into a running Superset instance.

## Exporting Superset Assets

Assets can be exported from Superset in a variety of locations. In the Dashboard list, there is an `export` action button, which will download a zip folder containing the dashboard and all associated assets, such as charts, datasets, and databases. This can be unzipped and added to a folder in the `/resources` directory of the `superset-oob` repo. This can similarly be done for Charts, Datasets, and Databases.!

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

### Creating the shared network

To ensure the `superset-oob` service and the Superset service can communicate via Docker networking, you can create a shared network:

```bash
docker network create superset_oob_network
```
*(Ensure your Superset container also joins this network.)*

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

## Usage

To trigger the import of all OOB asset bundles, send a POST request to the `/import` endpoint with a `tenant_id`:

```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "tenant_id": "my_tenant"
}' http://localhost:8082/import
```

This single command will trigger the full import process described above for all bundles located in the `resources` directory.

Inside of the superset container

```bash
superset oob-cli oob-import --tenant-id my_tenant
```

