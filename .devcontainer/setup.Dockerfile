FROM agero/lambda:build-python3.8

COPY Pipfile Pipfile.lock /workspace/

WORKDIR /workspace

ARG PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL:-""}
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}

RUN pipenv sync --dev
