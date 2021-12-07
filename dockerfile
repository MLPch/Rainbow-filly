FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3-pip python3-dev build-essential locales locales-all tree
ENV LC_ALL ru_RU.UTF-8
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU.UTF-8
WORKDIR /data
COPY requirements.txt /data/requirements.txt
RUN cat requirements.txt | sed -e '/^\s*#.*$/d' -e '/^\s*$/d' | xargs -n 1 pip install --no-cache-dir
RUN rm requirements.txt