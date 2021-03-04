# Project Structure

Below is a breakdown of the significant files/directories found at the root of the project:

## [azure-templates](/pipelines/azure-templates)
This directory contains Azure DevOps re-usable templates

## [config](/config)
This directory contains YAML files for application configuration

## [database](/infrastructure/database)
This directory contains the Serverless deployment for the database

## [docs](/docs)
This directory contains the documentation that you are currently reading!

## [.devcontainer](/.devcontainer)
This directory contains Dockerfiles that tell Docker how to build the images for your application. This also contains docker-compose.yml and devcontainer.json

## [environment](/infrastructure/environment)
This directory contains the Serverless deployment for the shared infrastructure

## [application](/infrastructure/application)
This directory contains the Serverless configuration and resources used for the primary deployment

## [scripts](/scripts)
This directory contains various scripts used locally (such as setting up DynamoDB Local)

## [src](/src)
This directory contains the Python application source code

## [tests](/tests)
This directory contains the tests for the Python application

## [.artifactignore](/.artifactignore)
This file contains information that tells Azure DevOps Pipelines which files to ignore when creating a build artifact.
The syntax for this file is identical to a `.gitignore` file.

## [.coveragerc](/.coveragerc)
This file contains configuration for the Python module [coverage](https://pypi.org/project/coverage/).  This module is
invoked indirectly via the [pytest-cov](https://pypi.org/project/pytest-cov/) plugin.

## [.gitignore](/.gitignore)
This file tells git which files to not include in source control.

## [.npmrc](/.npmrc)
This file tells provides configuration for NPM.  This is used to point NPM to Agero's private NPM feed in Azure Devops.

## [.pre-commit-config.yaml](/.pre-commit-config.yaml)
This file provides configuration to `pre-commit`, to tell it which steps to perform before allowing a git commit.

## [postmancollections](/postmancollections)
This folder contains API automation tests collections along with environment files which we later execute in CI/CD pipeline after API deployment.

## [azure-pipelines.yml](/pipelines/azure-pipelines.yml)
This file contains Build and Release configuration for Azure Devops.

## [docker-compose.yml](/.devcontainers/docker-compose.yml)
This file contains information on the cluster of Docker containers used for this application.

## [Makefile](/Makefile)
This file contains abstractions on how to perform commonly executed tasks, such as running the application locally,
testing the application, and deploying the application.

## [package.json](/package.json)
This file contains dependencies for the root Serverless deployment.

## [package-lock.json](/package-lock.json)
This file contains the resolved dependencies from the `package.json`, including security hashes.  This is used when
running the command `npm ci`.

## [Pipfile](/Pipfile)
This file contains the dependencies for the Python application, as well as some scripts.  This file is used and read
by `pipenv`.

## [Pipfile.lock](/Pipfile.lock)
This file contains the resolved dependencies from the `Pipfile`, including security hashes.  This is used when running
the command `pipenv sync`.

## [README.md](/README.md)
This file is the root of the documentation for the repo.

## [serverless.yml](/serverless.yml)
This file contains defines the root Serverless deployment for application.

## [sonar-project.properties](/sonar-project.properties)
This file contains configuration information for SonarCloud.
