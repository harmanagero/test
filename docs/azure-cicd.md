# Azure DevOps
Azure DevOps is a holistic DevOps tool that provides Build and Release pipelines, build artifact storage, and package
manager feeds for various languages.  We are using it extensively for the Pipeline functionality, as well as for hosting
private Agero feeds for Pip, NPM, and NuGet.

Build Pipelines are defined in YAML, and are stored in source control.

## Triggering Pipelines
Once a Pipeline is created in Azure DevOps (which can connect to a repository in Azure DevOps, Bitbucket, and GitHub),
the pipeline will be triggered via conditions defined in the [YAML](/azure-pipelines.yml).  In addition to triggering
based on specific branches and/or PRs, there can also be triggers based on specific paths, allowing builds to be
skipped if there was only a documentation change, or other conditions.

## Schema
Please refer to the [documentation](https://docs.microsoft.com/en-us/azure/devops/pipelines/yaml-schema?view=azure-devops&tabs=schema)
for the schema definition.

## Agents
Microsoft has build agents that they host, which can be utilized.  In addition to Windows Agents (which are currently
the only agents available for Windows-based build requirements), there are also Ubuntu and macOS X agents.  Agero
currently pays for unlimited build minutes on two concurrent build agents hosted by Microsoft.  Generally, we are
recommending these agents be used only for builds (not deployments), and only if Agero agents are not suitable (such as
if it is a Windows-based build).

Agero also has build agents that we have deployed in various AWS accounts that have permissions to perform deployments
within those accounts.  This eliminates the need for managing AWS credentials.  These build agents are Amazon Linux
based, and are not suitable for Windows-based builds.  Once a Windows build is completed, however, these agents would be
capable of taking the build artifact and deploying it to AWS.  Agero is licensed for a much larger number of these build
agents, as it is based on the number of Visual Studio licenses within the organization.

## Environments
Azure DevOps has the concept of a deployment environment.  These environments are used via a specific `deployment` job
within the Pipeline.  These environments can have approvals attached to them, providing a level of gating for
deployments to protected environments, such as Production.

## Stages, Jobs, and Steps
The actual work of a Pipeline is split into Stages, Jobs, and Steps.  In order to work with multi-stage pipelines, a
user must turn on the feature for themselves.  It is available to the organization, but must be enabled per user, as it
changes the User Interface.  Please follow [these instructions](https://docs.microsoft.com/en-us/azure/devops/project/navigation/preview-features?view=azure-devops&tabs=new-account-enabled)
to enable Preview Features.

Each stage can consist of multiple Jobs, though most are a single job.  Each job can (and generally do) consist of
multiple steps, typically of type `task`, `script`, `publish`, and `checkout`.
* `checkout`: is used to check out the code.  If the pipeline will be pushing tags back to the repo,
`persistCredentials: true` is needed.
* `publish`: is used to publish a Pipeline artifact.  The use of [/.artifactignore](/.artifactignore) simplifies this
* `task`: is used to perform a pre-defined piece of work.
    * These should be used sparingly (as they are vendor specific tasks)
    * Typically used for authentication
* `script`: is used to run a shell script
    * These are typically going to be `make` commands that invoke a process inside a Docker container
    * Dockerizing the build processes makes them more stable and involves less vendor lock-in.

## Key Steps

* Linting
    * Pre-commit linting checks only what is staged for a commit by default
    * Within the build pipeline, should verify all-files
    * Linting failures should block the build from continuing
    * Correctly installing `pre-commit` will prevent this from being an issue
* Tests
    * This should go without saying
    * Failing tests should block the build from continuing
    * Test coverage reports should be produced (in Cobertura format)
    * Test results should be produced in JUnit format
* SonarCloud
    * SonarCloud performs static code analysis
    * SonarCloud will provide reports of code smells
    * SonarCloud will read the Test Coverage report and include that within its analysis
    * Once SonarCloud project is stable, highly recommend adding SonarCloud gate check to fail the build if analysis is
      poor.
* Automation Tests (postmancollections)
    * Execute automation tests suite after deployment to QA/Stage completes. Roll back deployment if tests fail

## Best practices

* Team specific accounts use custom build agents instead of Service Connections which may not include all features of Azure agents.
* A pipeline will automatically fail if the code quality is below A. This can be due to test coverage lack or vulnerabilities and bad coding practices.
* For test coverage, SonarCloud requires 80% or above to pass by default
* Use Bandit as an additional vulnerability scanner if possible
* Python Bandit is a library that creates a SonarCloud compatible report and can catch issues that SonarCloud may miss
* Enable Build step of the pipeline to validate the build, run unit tests and code quality.
* Use environments to prevent unintentional deployments to stages. Please do not create environment for each project.
* You can add approver requirements per environment which requires explicit acceptance before a pipeline is executed
