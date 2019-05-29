FROM alpine:latest
MAINTAINER Matthew Gall <me@matthewgall.com>

RUN apk add --update \
	build-base \
	python3 \
	python3-dev \
	py-pip \
	openssl-dev \
	libffi-dev \
	whois \
	wget \
	curl \
	shadow \
	&& rm -rf /var/cache/apk/* \
	&& useradd --create-home whoisjs

USER whoisjs
WORKDIR /home/whoisjs
COPY . /home/whoisjs

RUN pip3 install --user --upgrade pip && \
    pip3 install --user -r /home/whoisjs/requirements.txt

EXPOSE 5000
CMD ["python3", "/home/whoisjs/app.py"]