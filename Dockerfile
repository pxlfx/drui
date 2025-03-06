# use the official Python slim image as the base image
FROM python:3-slim

# expose port 8000 for the Flask application
EXPOSE 8000

# set environment variables to optimize Python execution
# - PYTHONDONTWRITEBYTECODE: keeps Python from generating .pyc files
# - PYTHONUNBUFFERED: turns off buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# set the working directory
WORKDIR /app

# copy DRUI source code and install it
COPY . /app
RUN python -m pip install .

# create default configuration file
COPY config.example.cfg /etc/drui/config.cfg

# creates a non-root user with an explicit UID and
# adds permission to access the /app folder
RUN adduser -u 5678 appuser && chown -R appuser /app
USER appuser

# set the command to run the application
CMD ["drui", "--config", "/etc/drui/config.cfg"]
