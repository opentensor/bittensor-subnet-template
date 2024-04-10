ARG BASE_IMAGE=python:3.11-slim
FROM $BASE_IMAGE AS builder

# Set a non-interactive frontend to avoid any interactive prompts during the build
ARG DEBIAN_FRONTEND=noninteractive

# Create directory to copy files to
RUN mkdir -p /source/ /opt/template/
WORKDIR /source

ENV NODE_TYPE=$NODE_TYPE
ENV BITTENSOR_VERSION=$BITTENSOR_VERSION
RUN python -m pip install --prefix=/opt/template bittensor==$BITTENSOR_VERSION


COPY ./README.md ./setup.py /source/
COPY ./neurons /source/neurons
COPY ./template /source/template
RUN python -m pip install --prefix=/opt/template --no-deps .

# symlink lib/pythonVERSION to lib/python so path doesn't need to be hardcoded
RUN ln -rs /opt/template/lib/python* /opt/template/lib/python
COPY ./scripts /opt/template/scripts

FROM $BASE_IMAGE AS template

RUN mkdir -p ~/.bittensor/wallets

COPY --from=builder /opt/template /opt/template

ENV PATH="/opt/template/bin:${PATH}"
ENV LD_LIBRARY_PATH="/opt/template/lib:${LD_LIBRARY_PATH}"
ENV PYTHONPATH="/opt/template/lib/python/site-packages/:${PYTHONPATH}"


CMD ["python", "neurons/${NODE_TYPE}.py", \
     "--wallet.name", "${WALLET_NAME}", \
     "--wallet.hotkey", "${WALLET_HOTKEY}", \
    "--netuid", "${NETUID:-1}", "--axon.port", "${AXON_PORT}", \
    "--axon.external_port", "${AXON_EXTERNAL_PORT}", \
    "--subtensor.network", "${SUBTENSOR_NETWORK}", \
    "${TEMPLATE_EXTRA_OPTIONS}"]