#! /bin/sh

image_name=$(docker load -i *.tar| awk '/Loaded image:/ {print $NF}')
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
docker push "$image_name"
