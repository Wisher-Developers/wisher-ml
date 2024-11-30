FROM python:3.12.7-bookworm

RUN apt-get update && \
    apt-get install python3-pip python3-setuptools python3-psycopg2 python3-dev postgresql-server-dev-all librdkafka-dev -y && \
    pip3 install --upgrade pip==24.3.1 && \
    pip3 install pipenv

WORKDIR /project

ADD ./Pipfile ./Pipfile.lock ./

RUN pipenv install --system --deploy --clear

COPY ./ ./

CMD [ "./start.sh" ]
