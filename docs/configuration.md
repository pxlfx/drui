# Configuration

This section describes the configuration parameters for DRUI.
You can configure DRUI using a configuration file or environment variables.
Below is a detailed explanation of each parameter.

---

### DEFAULT

#### `host`

- **Description**: the host address on which DRUI will listen for incoming
  connections
- **Type**: `string`
- **Example**: `192.168.0.13`
- **Default**: `0.0.0.0` (listens on all available interfaces)
- **Environment Variable**: `DRUI_HOST`

#### `port`

- **Description**: the port on which DRUI will listen for incoming connections
- **Type**: `int`
- **Example**: `80`
- **Default**: `8000`
- **Environment Variable**: `DRUI_PORT`

#### `secret_key`

- **Description**: a secret key used for session cryptography.
  It is recommended to generate a secure key using the following command:
  ```bash
  openssl rand -base64 16
  ```
- **Type**: `string`
- **Example**: `HL4MwifdGYXfdoZ4pHygbA==`
- **Default**: `<none>`
- **Environment Variable**: `DRUI_SECRET_KEY`

#### `disable_delete`

- **Description**: disables the "delete Docker image" feature in the UI
- **Type**: `bool`
- **Example**: `true`
- **Default**: `false` (delete feature is enabled by default)
- **Environment Variable**: `DRUI_DISABLE_DELETE`

#### `images_per_page`

- **Description**: limits the number of Docker images displayed per page on the
  projects page
- **Type**: `int`
- **Example**: `15`
- **Default**: `<none>` (no limit by default)
- **Environment Variable**: `DRUI_IMAGES_PER_PAGE`

---

### registry

#### `endpoint`

- **Description**: the endpoint of the Docker Registry that DRUI will connect
  to
- **Type**: `string`
- **Example**: `http://127.0.0.1:5000`
- **Default**: `<none>` (must be provided)
- **Environment Variable**: `DRUI_REGISTRY_ENDPOINT`

#### `pull_endpoint`

- **Description**: the endpoint showed in pull-string
  (`docker pull <pull_endpoint>/<image>`)
- **Type**: `string`
- **Example**: `http://public.registry.io/`
- **Default**: `<none>` (if not provided, the `endpoint` value is used)
- **Environment Variable**: `DRUI_REGISTRY_PULL_ENDPOINT`

---

### broadcast

#### `path`

- **Description**: the path to a file containing a broadcast message
  (in Markdown). This message will be displayed in the DRUI interface
- **Type**: `string`
- **Example**: `/tmp/broadcast.md`
- **Default**: `<none>` (no broadcast message by default)
- **Environment Variable**: `DRUI_BROADCAST_PATH`

---

### mark

#### `official_prefix`

- **Description**: a list of prefixes used to identify official Docker images.
  Images with these prefixes will be marked as "Official Image" in the UI
- **Type**: `list`
- **Example**: `library`
- **Default**: `<none>` (no official prefixes by default)
- **Environment Variable**: `DRUI_MARK_OFFICIAL_PREFIX`

#### `verified_prefix`

- **Description**: a list of prefixes used to identify verified Docker images.
  Images with these prefixes will be marked as "Verified Publisher" in the UI
- **Type**: `list`
- **Example**: `main, cloud`
- **Default**: `<none>` (no verified prefixes by default)
- **Environment Variable**: `DRUI_MARK_VERIFIED_PREFIX`

---

### logging

#### `format`

- **Description**: the format for log messages. You can use the following
  placeholders:
    - `url`: the requested URL
    - `remote_addr`: the user's network address
    - `method`: the HTTP method (e.g., GET, POST)
    - `status_code`: the HTTP response code
    - `user_agent`: the User-Agent header
    - `referer`: the Referer header
    - `x_forwarded_for`: the X-Forwarded-For header
    - `content_length`: the response length in bytes
- **Type**: `string`
- **Example**: `%(remote_addr)s %(method)s`
- **Default**:
  `[%(asctime)s] %(levelname)s %(method)s %(status_code)s %(url)s %(message)s`
- **Environment Variable**: `DRUI_LOGGING_FORMAT`

#### `date_format`

- **Description**: the format for the date and time in log messages
- **Type**: `string`
- **Example**: `%Y-%m-%d`
- **Default**: `%Y-%m-%d %H:%M:%S`
- **Environment Variable**: `DRUI_LOGGING_DATE_FORMAT`

---

## Additional Tips

- **Configuration File**: you can provide a configuration file
  when running DRUI. For example:
  ```bash
  docker run --volume /path/to/config.cfg:/etc/drui/config.cfg pxlfx/drui:latest
  ```
- **Environment Variables**: all configuration parameters can be set using
  environment variables
- **Security**: ensure that sensitive information (e.g., `secret_key`) is kept
  secure and not exposed in version control

## Next Steps

- Visit the [GitHub repository](https://github.com/pxlfx/drui) for more
  information, issue tracking, and contribution guidelines.
