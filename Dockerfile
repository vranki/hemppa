FROM python:3.7-slim

WORKDIR /bot

COPY Pipfile .
RUN pip install pipenv && \
    pip install pipfile-requirements
RUN pipfile2req Pipfile > requirements.txt
RUN pip install -r requirements.txt

COPY bot.py *.json *.pickle /bot/
COPY config config
COPY modules modules

VOLUME /bot/config

CMD [ "python", "-u", "./bot.py" ]
