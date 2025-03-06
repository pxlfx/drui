# Build

This section will walk you through the steps to build and install **DRUI** from
source code.

---

1. Clone the repository:

   ```bash
   git clone https://github.com/pxlfx/drui
   cd drui
   ```
   > [!NOTE]
   > This will download the source code and navigate you into the project
   > directory.

2. Create a Virtual Environment (to isolate the project dependencies):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install DRUI:

   ```bash
   pip install .
   ```

4. Verify the Installation:

   ```bash
   drui --version
   ```
   > [!NOTE]
   > This command should output the current version of DRUI, confirming that
   > the installation was successful.

## Additional Tips

- **Development Mode**: after install, you can run DRUI in "development" mode
  (an interactive debugger will be shown for unhandled exceptions, and the
  server will be reloaded when code changes):

  ```bash
  drui --dev --config "/path/to/config.cfg"
  ```

- **Deactivating the Virtual Environment**: when you're done working, you can
  deactivate the virtual environment by simply running:

  ```bash
  deactivate
  ```

## Next Steps

- Explore the [configuration](configuration.md) section to customize DRUI for
  your needs.
- Visit the [GitHub repository](https://github.com/pxlfx/drui) for more
  information, issue tracking, and contribution guidelines.
