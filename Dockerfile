FROM python:3-alpine
MAINTAINER Matthew Gall <docker@matthewgall.com>

WORKDIR /app
COPY . /app

RUN pip3 install -r /app/requirements.txt

EXPOSE 5000
CMD ["python3", "/app/app.py"]