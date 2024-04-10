FROM python:3.11-slim

ARG NODE_TYPE
ARG BITTENSOR_VERSION
ARG WALLET_NAME
ARG WALLET_HOTKEY
ARG NETUID
ARG AXON_PORT
ARG AXON_EXTERNAL_PORT
ARG SUBTENSOR_NETWORK


# # Set a non-interactive frontend to avoid any interactive prompts during the build
# ARG DEBIAN_FRONTEND=noninteractive

# Create directory to copy files to
RUN mkdir -p /source/ /opt/template/
WORKDIR /source

ENV NODE_TYPE=$NODE_TYPE
ENV BITTENSOR_VERSION=$BITTENSOR_VERSION
ENV WALLET_NAME=$WALLET_NAME
ENV WALLET_HOTKEY=$WALLET_HOTKEY
ENV NETUID=$NETUID
ENV AXON_PORT=$AXON_PORT
ENV AXON_EXTERNAL_PORT=$AXON_EXTERNAL_PORT
ENV SUBTENSOR_NETWORK=$SUBTENSOR_NETWORK

RUN echo "Building $NODE_TYPE with bittensor version $BITTENSOR_VERSION"
RUN echo "Command: python -m pip install --prefix=/opt/template bittensor==$BITTENSOR_VERSION"
RUN python -m pip install bittensor==$BITTENSOR_VERSION
ENV PYTHONPATH=/source/

COPY ./README.md ./setup.py /source/
COPY ./neurons /source/neurons
COPY ./template /source/template

# symlink lib/pythonVERSION to lib/python so path doesn't need to be hardcoded
# RUN ln -rs /opt/template/lib/python* /opt/template/lib/python
COPY ./scripts /opt/template/scripts

RUN mkdir -p ~/.bittensor/wallets

# CMD ["tail", "-f", "/dev/null"]

CMD python neurons/${NODE_TYPE}.py \
     --wallet.name ${WALLET_NAME} \
     --wallet.hotkey ${WALLET_HOTKEY} \
     --netuid ${NETUID:-1} --axon.port ${AXON_PORT} \
     --axon.external_port ${AXON_EXTERNAL_PORT} \
     --subtensor.network ${SUBTENSOR_NETWORK} \
     ${TEMPLATE_EXTRA_OPTIONS}