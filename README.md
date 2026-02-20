# DRUI

Docker Registry UI

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Release](https://img.shields.io/github/release/pxlfx/drui.svg)](https://github.com/pxlfx/drui/releases/latest)

<div align="center">
  <img src="docs/images/logo.png" alt="drui-logo"/>
</div>

---

`DRUI` is an open-source Python-based web application that provides a user-friendly interface for interacting with Docker Registry ([Docker Distribution](https://github.com/distribution/distribution)).

This tool simplifies the management and exploration of container images stored in your private or public Docker registry.

## Demo

<https://drui.pxlfx.dev>

## Features

<div align="center">
  <a href="docs/screenshots.md">
    <img src="docs/images/preview.png" alt="screenshot" />
        <br />
        (click to view all screenshots)
  </a>
  <br />
  <br />
</div>

- **Auth**: basic auth / bearer token auth support
- **Image Catalog Overview**: browse through all available images in the
  registry
- **Filtering**: search and filter images by name
- **Repository Browsing**: explore images within a specific repository
- **Image Details**:
  - **summary**: view essential information about an image
  - **tags**: list all tags associated with the image
  - **inspect**: inspect detailed metadata of the image
  - **history**: show image history (build steps)
  - **os/arch**: display os/arch for multi-architecture images
- **Tag Management**:
  - download a specific image tag as a Docker Archive (`tar` file)
  - delete specific tags from images
- **Registry Analytics & Metrics**:
  - view statistics on image count, disk usage, etc
  - integrated system for data analysis and registry metrics collection
- **Image Marking**: identify official and verified publisher images
- **Theme**: dark/light theme in web interface
- **Mobile View**: support mobile view
- **Cross-Platform**: run on both Linux and Windows systems

## Quickstart

You can run DRUI with a simple configuration using environment variables:

```bash
docker run --detach \
           --name drui \
           --publish 8000:8000 \
           --restart always \
           --env DRUI_REGISTRY_ENDPOINT="http://127.0.0.1:5000" \
           ghcr.io/pxlfx/drui:latest
```

**Explanation**:

- `--env DRUI_REGISTRY_ENDPOINT="http://127.0.0.1:5000"`: sets the Docker Registry endpoint that DRUI will connect to

> For more information about quickly set up and run DRUI using Docker, see the [docs/quickstart](docs/quickstart.md).

## Configuration

Full information about the configuration parameters see in [docs/configuration](docs/configuration.md) or check [config.example.cfg](config.example.cfg).

## Documentation

Complete documentation is available at the following link: [documentation](docs/index.md).

## License

Source code distributed by [MIT License](LICENSE).

---

If you find this project useful, please consider starring it! Your support helps us continue development and improvement.
