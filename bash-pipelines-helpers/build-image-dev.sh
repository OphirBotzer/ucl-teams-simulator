#! /bin/sh

/bin/sh -c ./bash-pipelines-helpers/configure-git.sh
latest_commit_hash=$(git rev-parse HEAD)
image_id=$(docker build -t ucl-team-simulator:tmp .)
docker_sha=$(docker images --no-trunc --quiet ucl-team-simulator:tmp | sed 's/sha256://')

docker tag ucl-team-simulator:tmp ophirbotzer/ucl-team-simulator:dev-$latest_commit_hash-$docker_sha
git tag -a dev-$latest_commit_hash-$docker_sha -m "Tag for commit $latest_commit_hash with Docker image $docker_sha"
git push --tags

docker save ophirbotzer/ucl-team-simulator:dev-$latest_commit_hash-$docker_sha -o ucl-team-simulator-dev-$latest_commit_hash-$docker_sha.tar