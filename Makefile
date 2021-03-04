.PHONY: clean test build bandit package view-coverage destroy bash run stop setup serverless-deps debug serverless-cv-deps package-cv package-cv-infra deploy-cv-api deploy-cv-infra deploy-cv-database automation-test deploy-cv-database-supplement sonarcloud-ci apigee-automation-test smoke-test

clean:
	cd .devcontainer && docker-compose run app /bin/bash -c "find . -name '*.py[co]' -delete"
	cd .devcontainer && docker-compose run app /bin/bash -c "find . -name __pycache__ |xargs rm -rf"

test:
	cd .devcontainer && docker-compose run app pipenv run test

build:
	cd .devcontainer && docker-compose build $(container)

bandit:
	cd .devcontainer && docker-compose run app pipenv run bandit

package:
	cd .devcontainer && docker-compose run app bash -c "serverless package --conceal --verbose --stage $(stage) --region $(region)  && rm -rf ./.serverless"

view-coverage:
	open ./coverage-report/index.html

destroy:
	cd .devcontainer && docker-compose down -v

bash:
	cd .devcontainer && docker-compose run app env SHELL=/bin/bash /bin/bash -c "pipenv shell"

run: stop
	cd .devcontainer && docker-compose up

stop:
	cd .devcontainer && docker-compose down

setup:
	pipenv run pre-commit install

serverless-deps:
	cd .devcontainer && docker-compose run app npm ci

debug:
	cd .devcontainer && docker-compose run --service-ports app pipenv run app

serverless-cv-deps:
	cd .devcontainer && docker-compose run deploy npm ci

package-cv:
	cd .devcontainer && docker-compose run -w /workspace deploy bash -c "serverless package --stage $(stage) --region $(region) --conceal --verbose"

package-cv-infra:
	cd .devcontainer && docker-compose run -w /workspace/infrastructure/environment deploy bash -c "serverless package --stage $(stage) --region $(region) --conceal --verbose"

deploy-cv-api:
	cd .devcontainer && docker-compose run -w /workspace deploy bash -c "serverless deploy --stage $(stage) --region $(region) --conceal --verbose"

deploy-cv-infra:
	cd .devcontainer && docker-compose run -w /workspace/infrastructure/environment deploy serverless deploy --stage $(stage) --region $(region) --conceal --verbose

deploy-cv-database:
	cd .devcontainer && docker-compose run -w /workspace/infrastructure/database deploy serverless deploy --stage $(stage) --region $(region) --conceal --verbose

deploy-cv-database-supplement:
	cd .devcontainer && docker-compose run -w /workspace/infrastructure/supplementdatabase deploy serverless deploy --stage $(stage) --region $(region) --conceal --verbose

automation-test:
	cd .devcontainer && docker-compose -f docker-compose-testing.yml run automationtestsrunner run CVGatewayAPI.postman_collection.json -e environments/$(stage).postman_environment.json -r cli,junitfull --reporter-junitfull-export Results//apiTestResults.xml

apigee-automation-test:
	cd .devcontainer && docker-compose -f docker-compose-testing.yml run automationtestsrunner run CVGatewayAPIApigee.postman_collection.json -e environments/$(stage).postman_environment.json -r cli,junitfull --reporter-junitfull-export Results//apiTestResults.xml

smoke-test:
	cd .devcontainer && docker-compose -f docker-compose-testing.yml run automationtestsrunner run CVGatewaySmokeTests.postman_collection.json -e environments/$(stage).postman_environment.json -r cli,junitfull --reporter-junitfull-export Results//apiTestResults.xml

sonarcloud-ci:
	cd .devcontainer && docker-compose -f docker-compose-sonar.yml run sonar sonar-scanner -Dsonar.host.url=https://sonarcloud.io -Dsonar.projectVersion=${version} -Dsonar.branch.name=${branch}
