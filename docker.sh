#!/bin/bash
set -eu

IMAGE_NAME=bots-sandbox
CONTAINER_NAME=sandbox
REBUILD=

while [[ $# -gt 0 ]]
do
	key="$1"

	case $key in
		-r|--rebuild)
		REBUILD=true
		shift # past argument
		;;
		*)    # unknown option
		echo "Unknown option $key"
		exit 1
		;;
	esac
done

if ! [ -x "$(command -v docker)" ]; then
    echo "Installing docker"
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
	sudo add-apt-repository \
	   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
	   $(lsb_release -cs) \
	   stable"
	sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $(whoami)
    docker run hello-world
fi

if ! $(docker image list | grep -q $IMAGE_NAME) || [ $REBUILD ]; then
    echo "Building image $IMAGE_NAME"
    docker build --network=host --build-arg USER=$(whoami) --build-arg UID=$(id -u) --build-arg GID=$(id -g) -f Dockerfile -t $IMAGE_NAME .
fi

if [ ! "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    docker container rm $CONTAINER_NAME >/dev/null 2>/dev/null && echo "Removed previous container $CONTAINER_NAME" || true
    echo "Starting container $CONTAINER_NAME"
    docker run --name $CONTAINER_NAME --network host -u $(id -u):$(id -g) -v $(pwd):/home/$(whoami)/$(basename $(pwd)) -it $IMAGE_NAME
else
    docker exec -it $CONTAINER_NAME bash
fi
