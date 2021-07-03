FROM python:3.6.10-slim-buster as builder

LABEL MAINTAINER "Khaerul Umam"
LABEL DESCRIPTION "Covid Vaccine Progress"

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y build-essential default-libmysqlclient-dev libssl-dev python-dev \
    python3-setuptools gfortran libblas-dev liblapack-dev liblapack3 nano supervisor locales \
    && python -m venv /opt/venv

RUN locale-gen en_US.UTF-8
ENV TZ=Asia/Jakarta
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN ln -s /usr/include/x86_64-linux-gnu/bits/types/__locale_t.h /usr/include/xlocale.h

ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.6.10-slim-buster as run

ARG APP_USER="Khaerul"
ARG WORK_DIRECTORY="/app"

COPY . /app
WORKDIR ${WORK_DIRECTORY}

RUN apt-get update -y && apt-get upgrade -y \ 
    && apt-get install -y --no-install-recommends libgomp1 locales dumb-init \ 
    && useradd -rm -d ${WORK_DIRECTORY} -s /bin/bash -U ${APP_USER} \ 
    && chown -R ${APP_USER}:${APP_USER} ${WORK_DIRECTORY} \ 
    && locale-gen en_US.UTF-8 \ 
    && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && echo ${TZ} >/etc/timezone \ 
    && apt-get clean

USER ${APP_USER}

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD python app.py
