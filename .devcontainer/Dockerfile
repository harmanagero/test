#agero/lambda is a clone of lambci image which is very well known image when they are trying to duplicate lambda container run time. Only difference
# is that we have installed serverless framework in it so that we can do deployments with it.
FROM agero/lambda:build-python3.8 AS base

COPY Pipfile Pipfile.lock /workspace/

WORKDIR /workspace

#PIP_EXTRA_INDEX_URL- private Pip index that we have which is going to do pipenv install from azure devops artifacts repos.
ARG PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL:-""}
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}

# This is pre-building the virtual environment. VENV is not stored in the directory. it is outside of it.
RUN pipenv sync --dev

FROM base AS app

# Pre-setting the pre commit environment.
COPY .pre-commit-config.yaml /workspace/
RUN git init

RUN pipenv run pre-commit run --all-files
RUN rm -rf .git
