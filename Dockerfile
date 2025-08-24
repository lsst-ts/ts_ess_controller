FROM almalinux:9

RUN dnf install -y epel-release && \
    dnf update -y && \
    dnf install -y git vim bash-completion wget libftdi libftdi-devel iproute minicom && \
    dnf clean all

COPY minirc.dfl /etc/minirc.dfl

ENV HOME=/home/saluser
RUN groupadd -g 70014 docker
RUN adduser -G wheel,docker saluser
COPY setup.sh ${HOME}/.setup.sh

RUN chown saluser:saluser ${HOME}/.setup.sh && \
    chmod +x ${HOME}/.setup.sh

RUN dnf install -y gcc make && dnf clean all

USER saluser
WORKDIR ${HOME}
ARG ARCH=aarch64
ENV ARCH=${ARCH}

ARG common
ARG controller

ARG PYTHON_VERSION

RUN wget -q https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-${ARCH}.sh -O miniforge.sh && \
    chmod +x miniforge.sh && \
    ./miniforge.sh -b -p ${HOME}/miniconda3 && \
    source ${HOME}/miniconda3/bin/activate && \
    conda config --set solver libmamba && \
    conda install -y python=${PYTHON_VERSION} && \
    conda config --add channels conda-forge && \
    conda config --add channels lsstts && \
    conda install -y conda-build anaconda-client setuptools_scm && \
    conda install -y numpy astropy && \
    conda install -y ts-ess-common=${common} ts-ess-controller=${controller} && \
    pip install asyncio pyserial pylibftdi pyftdi jsonschema pyyaml

RUN echo source ${HOME}/miniconda3/bin/activate >> ${HOME}/.bashrc
COPY python/lsst/ts/ess/controller/device /opt/ts_ess_controller/python/lsst/ts/ess/controller/device
COPY python/lsst/ts/ess/controller/device/test_sps30.py /opt/ts_ess_controller/python/lsst/ts/ess/controller/device/

LABEL ts-ess-controller=${controller} \
      ts-ess-common=${common}

ENTRYPOINT ["/bin/bash", "--"]
CMD ["/home/saluser/.setup.sh"]

COPY sps30_driver /opt/sps30_driver
WORKDIR /opt/sps30_driver
RUN make

COPY sps30-uart-3.1.0 /opt/sps30/sps30-uart-3.1.0
WORKDIR /opt/sps30/sps30-uart-3.1.0
RUN make

ENTRYPOINT ["bash", "-c", "python3 sps30_uart.py & exec run_ess_controller"]
