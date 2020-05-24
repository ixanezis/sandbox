FROM ubuntu:18.04 as base

ARG USER=
ARG UID=
ARG GID=

RUN addgroup --gid $GID $USER
RUN adduser --disabled-password --gecos '' --uid $UID --gid $GID $USER
RUN usermod -aG sudo $USER

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update && apt-get install -y --no-install-recommends locales

RUN locale-gen en_US.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      sudo \
      ack-grep \
      vim \
      curl \
      wget \
      gnupg \
      ca-certificates

RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN curl -fsSL https://bazel.build/bazel-release.pub.gpg | apt-key add - >/dev/null
RUN echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list

RUN apt-get update && apt-get install -y --no-install-recommends \
      bazel

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip

RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

RUN pip install apscheduler pymongo

USER ${UID}:${GID}
WORKDIR /home/$USER

RUN git clone --recursive https://github.com/ixanezis/configs.git
RUN ./configs/setup.sh
