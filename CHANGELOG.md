# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog].
This project adheres to [Semantic Versioning].

## [0.2.2] - 2026-07-18

### Fixed

- fixed hanging Promise in RequestQueue executor
- fixed hardcoded "localhost" address used for URL matching
- fixed incorrect column type for `digest` in `tags` table
- fixed timeout not being set for registry requests
- fixed detailed error message for broadcast message processing being displayed to the user
- fixed missing "sha256:" prefix when obtaining Docker-Content-Digest not from the response header
- fixed incorrect HTTP return code (505) when a service error occurs
- fixed `error_count` not being reset on successful request execution
- fixed incorrect function called in `test_test_getint_default`
- fixed simple hardcoded default `secret_key`
- fixed spelling error in the word "duplicates" (was "dublicates")
- fixed potentially dangerous Jinja2 safe filters for HTML templates
- fixed `Vault.get` returning the internal dict instead of the value
- fixed wrong key used to retrieve the token TTL
- fixed inefficient tag lookup in the tags list
- fixed setting some paths that are not available on Windows
- fixed missing existence check for logger handler before adding
- fixed Flask session not being encrypted, allowing it to be decoded and the password to be read
- fixed `error_count` being incremented on every iteration, which leads to a worker crash after 3 cycles

### Changed

- refactored: replaced duplicated code with `get_conf` call

## [0.2.1] - 2026-02-20

### Fixed

- fixed incompatibility with Windows by replacing Gunicorn with Waitress as the WSGI server
- fixed database lock errors for metrics on Windows
- fixed XSS vulnerabilities caused by unsafe `innerHTML` usage
- fixed argument type mismatches in function calls
- fixed potential mass deletion of metrics database
- fixed incorrect display of the list of tags being deleted (updated `table.js` to version 0.1.3)
- fixed security issues in Docker Compose configuration
- fixed Docker container startup failure when `read_only: true` is set (added `DRUI_METRICS_PATH` variable)

## [0.2.0] - 2025-12-25

### Added

- added download Docker image as tar file (#1)
- added metrics collection system (#2)
- added token authentication support (#3)
- added copying tag details to clipboard on mobile devices
- added Python-3.14 support

### Changed

- updated JavaScript libraries (fontawesome, bootstrap, table.js)

### Fixed

- fixed image page rendering error when repository list is empty
- fixed implement for registry catalog to bypass 100 items limit

## [0.1.0] - 2025-08-01

### Added

- added Docker files for building an image and running a container
- added "dark/light" design theme
- added the ability to specify the file path for a public message
- added the ability to pass parameters via environment variables
- added Basic Auth support in the web interface
- added the ability to identify official and verified publisher images
- added the ability to filter images by name
- added the option to disable image deletion
- added support for deleting specific tags from images
- added a "Summary" section for the image
- added a "History" section for the image
- added a "Tags" section for the image
- added an "OS/Arch" section for the image
- added an "Inspect" section for the image
- added the ability to view essential information about an image (Tag, OS/Arch)
- added support for the `vnd.oci.image.manifest.v1` manifest
- added support for the `vnd.docker.distribution.manifest.v2` manifest
- added the display of image repositories
- added the ability to browse all available images

<!-- Links -->
[keep a changelog]: https://keepachangelog.com/en/1.0.0/
[semantic versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[0.2.2]: https://github.com/pxlfx/drui/releases/tag/0.2.2
[0.2.1]: https://github.com/pxlfx/drui/releases/tag/0.2.1
[0.2.0]: https://github.com/pxlfx/drui/releases/tag/0.2.0
[0.1.0]: https://github.com/pxlfx/drui/releases/tag/0.1.0
