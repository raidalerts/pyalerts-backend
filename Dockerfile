FROM python:3.11-alpine3.17
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r ./requirements.txt --src=/root/pip
COPY ./src ./src
