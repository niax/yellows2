#!/bin/bash -ex

(
	cd infra
	docker build . -t yellows2-infra
)

docker run -e AWS_DEFAULT_REGION -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -e AWS_ACCESS_KEY_ID -it -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):/src yellows2-infra sh -xec '
	cd infra
	cdk bootstrap
'
