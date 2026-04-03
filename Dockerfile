# 1. Install Python Image
ARG PYTHON_VERSION=3.11.9
FROM python:${PYTHON_VERSION}-slim

# 2. Install UV

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# 3. Move over app
# Copy the source code into the container.
COPY . /app
WORKDIR /app

# Disable development dependencies
ENV UV_NO_DEV=1

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
# 4. Network
EXPOSE 5000

# 5. Run the application.
CMD uv run python -m src.app
