# use the official Python slim image as the base image
FROM python:3.13-slim

# set build arguments
ARG SOURCE_PATH=.source
ARG WORKDIR_PATH=/app

# expose port 8000 for the Flask application
EXPOSE 8000

# set workdir
WORKDIR ${WORKDIR_PATH}

# set environment variables to optimize Python execution
# - PYTHONDONTWRITEBYTECODE: keeps Python from generating .pyc files
# - PYTHONUNBUFFERED: turns off buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# copy DRUI source code and install it
COPY . ${SOURCE_PATH}
RUN python -m pip install --no-cache-dir ${SOURCE_PATH} && \
    rm -rf ${SOURCE_PATH} /root/.cache/pip

# create default configuration file
COPY config.example.cfg ${WORKDIR_PATH}/config.cfg

# creates a non-root user with an explicit UID and
# adds permission to access the workdir folder
RUN addgroup appuser && \
    adduser --no-create-home --system appuser && \
    chown -R appuser:appuser ${WORKDIR_PATH}
USER appuser

# set the command to run the application
CMD ["drui", "--config", "${WORKDIR_PATH}/config.cfg"]
