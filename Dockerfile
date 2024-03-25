# syntax=docker/dockerfile:1

# `python-base` sets up all our shared environment variables
FROM python:3.10-slim as base

# Setup Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=true \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \
    DEBIAN_FRONTEND=noninteractive \
    OPENMP_ENABLED=1

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Setup Shell for the Docker Image
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

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
    # Setup SSH
    && mkdir -p ~/.ssh \
    && touch ~/.ssh/known_hosts \
    && chmod 0600 ~/.ssh/known_hosts ~/.ssh \
    && ssh-keyscan github.com >> ~/.ssh/known_hosts \
    # Install Poetry
    && pip install "poetry==$POETRY_VERSION"

CMD ["/bin/bash"]

FROM base as production_pipelines
COPY . $PYSETUP_PATH
WORKDIR $PYSETUP_PATH
RUN poetry install --without=dev
# Run the project
CMD ["workflow", "workspace", "set", "development"]
