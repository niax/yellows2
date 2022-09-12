#!/bin/bash -ex

docker run --rm -e AWS_DEFAULT_REGION -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -e AWS_ACCESS_KEY_ID -it -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):/src -w /src/infra yellows2-infra cdk deploy "$@"
