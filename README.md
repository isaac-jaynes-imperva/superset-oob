# Out-of-the-Box (OOB) Reports

This serves as an example for how to structure the repository for Superset's "Out-of-the-Box" (OOB) reports import feature. This feature allows you to import reports, dashboards, charts, and datasets from a Git repository into your Superset instance.

## Repository Structure

The repository must be structured with the following directories. Each directory holds YAML files corresponding to a specific Superset asset type.

```
.
├── databases/
├── datasets/
├── charts/
├── dashboards/
└── reports/
```

-   `databases/`: Holds YAML definitions for databases.
-   `datasets/`: Holds YAML definitions for datasets.
-   `charts/`: Holds YAML definitions for charts.
-   `dashboards/`: Holds YAML definitions for dashboards.
-   `reports/`: Holds YAML definitions for reports (email schedules).

## Asset Format

All asset files must be in YAML format (`.yaml` or `.yml`). You can generate these files by exporting assets from the Superset UI.

For example, to export a dashboard, navigate to the dashboard list, select the dashboards you want to export, and choose **"Export dashboard(s) to YAML"** from the **Actions** menu. The exported YAML files should then be placed in the corresponding directories in your repository.

## Templating

The import command supports basic templating using the `{{ tenant_id }}` placeholder. You can use this placeholder in your YAML files to create assets that are specific to a tenant. This is particularly useful for multi-tenant deployments where assets might point to tenant-specific tables or schemas.

For example, you can use the `{{ tenant_id }}` placeholder in a dataset's `table_name`:

```yaml
table_name: my_table_{{ tenant_id }}
schema: my_schema_{{ tenant_id }}
```

When you run the import command with a `tenant_id` of `my_tenant`, the `table_name` will be set to `my_table_my_tenant` and the `schema` to `my_schema_my_tenant`.

## Usage

Once your repository is structured correctly and contains your YAML assets, you can import them into Superset using the `superset import-oob-reports` CLI command.

```bash
superset import-oob-reports -t my_tenant -u https://my-repo.com/reports.git -b main
```

This command will clone the specified repository, apply the `tenant_id` templating, and import all the assets into your Superset instance.
