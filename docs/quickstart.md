# Getting Started

This section will help you quickly set up and run the Docker Registry UI (DRUI)
locally using Docker.

---

## Running DRUI with Environment Variables

You can run DRUI with a simple configuration using environment variables.
Below is an example command to start the container:

```bash
docker run --detach \
           --name drui \
           --publish 8000:8000 \
           --restart always \
           --env DRUI_REGISTRY_ENDPOINT="http://127.0.0.1:5000" \
           pxlfx/drui:latest
```

**Explanation**:

- `--detach`: runs the container in the background
- `--name drui`: assigns a name to the container
- `--publish 8000:8000`: maps port 8000 on your host to port 8000 in the
  container
- `--restart always`: ensures the container restarts automatically if it stops
- `--env DRUI_REGISTRY_ENDPOINT="http://127.0.0.1:5000"`: sets the Docker
  Registry endpoint that DRUI will connect to
- `pxlfx/drui:latest`: specifies the DRUI Docker image to use

## Custom Configuration File

If you need more advanced configuration, you can provide your own configuration
file. Here’s how to do it:

```bash
docker run --detach \
           --name drui \
           --publish 8000:8000 \
           --restart always \
           --volume ${PWD}/config.cfg:/etc/drui/config.cfg \
           pxlfx/drui:latest
```

**Explanation**:

- `--volume ${PWD}/config.cfg:/etc/drui/config.cfg`: bind your configuration
  file from host machine to the container. Replace `${PWD}/config.cfg` with the
  path to your configuration file

> [!NOTE]
> For detailed information about configuration parameters, refer to the
> [configuration](configuration.md) section.

### Running with Docker Compose

You can use Docker Compose to run DRUI alongside other services, such as a
Docker Registry. Below is an example `docker-compose.yml` file that runs DRUI
and a Docker Registry:

```yaml
version: '3.4'

services:
  drui:
    image: pxlfx/drui:0.1.0
    container_name: drui
    restart: always
    environment:
      DRUI_REGISTRY_ENDPOINT: http://distribuition:5000
    ports:
      - 8000:8000
    depends_on:
      - distribution

  distribution:
    image: distribution:2.8.2
    container_name: distribution
    restart: always
    ports:
      - 5000:5000
    volumes:
      - data:/var/lib/registry

volumes:
  data:
    name: distribution_data
```

To start the services, run the following command:

```bash
docker-compose up -d
```

This will start both DRUI and the Docker Registry in detached mode. You can
access DRUI at http://127.0.0.1:8000.

## Additional Tips:

- **Reverse Proxy**: if you are running DRUI behind a
  [reverse proxy](reverse_proxy.md), make sure to configure the proxy to forward
  the correct headers

## Next Steps

- Explore the [configuration](configuration.md) section to customize DRUI
  further.
- Visit the [GitHub repository](https://github.com/pxlfx/drui) for more
  information, issues, and contributions.
