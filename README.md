# cvgatewayapi-serverless-framework

Connected Vehicle Gateway API persist and Return Connected Vehicle Data. The primary responsibility of this service is to service Telematics calls originated from a car that has a telematics device installed for making roadside assistance calls.


## Organization
The documentation is organized into separate files, each covering their own area.  Each of these files is linked below:


## Setup and Prerequisites 
* [Setup and Prerequisites Installations](/docs/setup&installations.md)

Once all of the prerequisites are in place, running `make setup` is all that is needed.  This will perform 3 steps:

1. Pre-build all of the docker containers referenced in the `docker-compose.yml`
1. Run `pip install pre-commit` to install `pre-commit` locally.
1. Run `pre-commit install` to register `pre-commit` with the local git hooks.

If you are using an IDE that supports attaching the a remote interpreter, it is running on the `app` container, at
`/root/.local/share/virtualenvs/workspace-dqq3IVyd/bin/python`

## Primary Technologies

* [Primary Technologies](/docs/technologies.md)

## Project Structure

* [Project Structure](/docs/structure.md)

* [Serverless Framework](/docs/serverless.md)

## CI/CD Pipeline

* [Azure DevOps Pipeline](/docs/azure-cicd.md)

## Rest API designj Considerations

* [Rest API Design Considerations](/docs/restapidesignconsiderations.md)


## Run Locally

Create a .env file at the root of the project (this should NOT be checked into git) with the following:
    fca__api_key=****
    AWS_ACCESS_KEY_ID=VALID_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY=VALID_SECRET_ACCESS
    AWS_SESSION_TOKEN=VALID_SESSION_TOKEN

* Run in VS Code - Locally
    * Go to Run icon on left side of VS Code
    * Select Python: Fast API App from the dropdown
    * Click on Run icon.

* Run in VS Code - Remote Containers
    * Follow all the guidelines to Install remote container extension in VS Code [Remote Containers](/docs/remotecontainers.md)
    * Open command pallet by selecting Ctrl + Shift + P keys 
    * Select Remote-Containers: Rebuild and Reopen in Container
        
* Run in container
    * `make run`
    * This will use docker-compose to:
    * Start DynamoDB Local
    * Setup table in DynamoDB Local
    * Start Python: Fast API App and expose via port 5000
* Rebuild
    * `make build`  will rebuild the Api container
    * This should only be needed if there are dependency changes in Pipfile
      * Dependency installation is performed as part of the build to ensure make run starts quickly


* [Configurations](/docs/configuration.md)
