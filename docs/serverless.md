# Serverless Framework
Serverless Framework is an abstraction layer that can deploy to multiple cloud providers (though only one per template).
We are using Serverless Framework as it greatly simplifies the deployment of AWS Lambda based applications, and also
because it supports the use of regular CloudFormation templates, while giving the benefit of variable substitution
and a plugin ecosystem.

## Serverless at Agero

### Serverless.yml
This file is the base of a Serverless deployment.  When compiled, it will generate a CloudFormation template that is
then used (by Serverless) to deploy a CloudFormation Stack for the application environment.

Serverless uses a pre-defined S3 bucket to maintain the state of an application's deployments, as well as to host any
Zip archives for Lambda code.  Within Agero, we have adopted the Serverless Deployment Bucket naming convention of
`agero-{accountId}-{region}-sls-deploy`.

Serverless provides the ability to create Stack Tags, which are applied to the CloudFormation stack.  Any resource then
created by the CloudFormation stack that supports tagging will have said tags applied.  This allows teams to stay in
compliance with Agero's Tagging requirements.

Serverless provides a `resources` key in which raw CloudFormation can be used.  This can be used to create new
resources, but can also be used to modify the resources that Serverless creates.  Follow the [documentation](https://serverless.com/framework/docs/providers/aws/guide/resources#aws-cloudformation-resource-reference)
for the override functionality.

Serverless provides a rich plugin ecosystem that we use extensively.  Plugins are declared in the `plugins` section of
the `serverless.yml`, but must also be installed at the root via `npm` (as Serverless is a Node.js application).

### Configuration
In order to keep the `serverless.yml` file clean, we have adopted the use of per-environment configuration files that
can be pulled in at the time of deployment.  The convention we have used for these is to create a `serverless/config`
directory at the root of the deployment, and have the naming of the config files as `{stage}.yml`, where stage is
provided with the `--stage dev` argument passed into `serverless deploy`.

### Resources
In addition to the, we will often use a `serverless/resources` section in order to store the CloudFormation for
individual resources.  This helps keep the `serverless.yml` file cleaner and easier to read.

### Plugins
If there are plugins that are created as part of a project that are only applicable to that project, we will include
those in a `serverless/plugins` directory.

### NPM Permissions and setup
https://agero-ops.visualstudio.com/Core%20Engineering/_packaging?_a=connect&feed=arch-feed

## Project Specific Deployments
Within this project, there are three separate (but related) Serverless deployments.

### Infrastructure Deployment
This [serverless.yml](/infrastructure/serverless.yml) provides the following functionality:
* Creates an API Gateway Custom Domain (shared per account)
* Creates a Route53 entry for the Custom Domain
* Exports the API Gateway Custom Domain Name for later import

### Database Deployment
This [serverless.yml](/databases/serverless.yml) provides the following functionality:
* Creates a DynamoDB Table without provisioned capacity.
* Exports the table name for later import.

### Lambda Deployment
This [serverless.yml](/serverless.yml) provides the following functionality:
* Imports secrets from AWS Secrets manager
* Packages the Lambda Function
* Imports the exported value of the DynamoDB table from the Database Deployment (creating a lock)
* Imports the exported value of the Custom Domain from the Infrastructure Deployment (creating a lock)
* Encrypts the value of specified environment variables
* Creates a Lambda function and version
* Creates a secured API Gateway and deployment
* Creates a Cloudwatch Log Group for the Lambda function to log to
* Creates an IAM Role to grant the Lambda Function CloudWatch, KMS Decrypt, and DynamoDB Permissions
* Creates an API Key to access the API Gateway
* Mounts API Gateway to custom domain.
* Implement canary deployments of Lambda functions, making use of the traffic shifting feature in combination with AWS CodeDeploy.
