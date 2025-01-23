FROM ubuntu:20.04

LABEL maintainer="Wang Wei<wangwei@cmgos.com>" \
    description="UICR Service"

ENV python=python3 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /cmit
RUN mkdir -p /cmit/logs \
    # && echo "Asia/Shanghai" > /etc/timezone \
    && touch /etc/apt/sources.list \
    && sed -i "s@http://.*archive.ubuntu.com@http://mirrors.tuna.tsinghua.edu.cn@g" /etc/apt/sources.list \
    && sed -i "s@http://.*security.ubuntu.com@http://mirrors.tuna.tsinghua.edu.cn@g" /etc/apt/sources.list \
    # && sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list \
    # && sed -i 's|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list \
    # && apt-get clean \
    && apt-get update \
	&& apt-get install -y --no-install-recommends $python-pip libopencv-dev
    # && dpkg-reconfigure tzdata

COPY requirements.txt ./
RUN $python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY config/ ./config/
COPY data/ ./data/
COPY services/ ./services/
COPY yolov7/ ./yolov7/

COPY api_utils.py detect_models.py detect_api.py main.py entrypoint.sh ./


ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

EXPOSE 39060