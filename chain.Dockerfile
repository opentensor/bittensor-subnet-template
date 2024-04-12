FROM rust:1.77-bullseye

RUN apt update && \
    apt install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler tmux



CMD tail -f /dev/null