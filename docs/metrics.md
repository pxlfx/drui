# Metrics

This section describes how to enable and configure metrics collection in DRUI.

## Metrics Collected

- Total registry size
- Total number of images
- Number of tags for each image
- Total number of layers
- Size of the latest tag and its creation time for each image
- List of the newest tags
- List of the oldest tags
- Duplicate images

## Enabling metrics collection

To enable metrics collection set the configuration parameter:

```ini
[metrics]
enable = true
```

> Full information about the configuration parameters see in [docs/configuration](docs/configuration.md)

An example command to run DRUI with metrics collection using Docker:

```bash
docker run --detach \
           --name drui \
           --publish 8000:8000 \
           --restart always \
           --env DRUI_REGISTRY_ENDPOINT="http://127.0.0.1:5000" \
           --env DRUI_METRICS_ENABLE="true" \
           ghcr.io/pxlfx/drui:latest
```

## Accessing Metrics

Once metrics are enabled, DRUI exposes metrics at the `/metrics` endpoint.

**Example**: `http://127.0.0.1:8000/metrics`
