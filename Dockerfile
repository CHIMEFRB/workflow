# syntax=docker/dockerfile:1

# Build Command
# export DOCKER_BUILDKIT=1; docker buildx build -t chimefrb/workflow:latest .

ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}-slim as base

# Setup Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=true \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/workflow" \
    VENV_PATH="/opt/workflow/.venv" \
    DEBIAN_FRONTEND=noninteractive \
    OPENMP_ENABLED=1

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Setup Shell for the Docker Image
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

FROM base as builder
# Install system dependencies
RUN set -ex \
    && apt-get update -yqq \
    && apt-get install --no-install-recommends -yqq \
       curl \
       ssh \
       gnupg \
       lsb-release \
    # Cleanup
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/* \
    && rm -rf /usr/share/man \
    && rm -rf /usr/share/doc \
    && rm -rf /usr/share/doc-base \
    # Setup SSH for Github Access
    && mkdir -p ~/.ssh \
    && touch ~/.ssh/known_hosts \
    && chmod 0600 ~/.ssh/known_hosts ~/.ssh \
    && ssh-keyscan github.com >> ~/.ssh/known_hosts

# Install Poetry
RUN set -ex \
    && pip install --upgrade pip poetry --no-cache-dir

# Copy Project Files
COPY . $PYSETUP_PATH
WORKDIR $PYSETUP_PATH
# Install Project Dependencies
RUN set -ex \
    && poetry install --without dev --no-interaction --no-ansi --no-cache -v

# Final Image
FROM base as production
COPY --from=builder $VENV_PATH $VENV_PATH
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH
ENTRYPOINT [ "/opt/workflow/entrypoint.sh" ]
CMD ["workflow"]
