FROM python:3.7-slim

WORKDIR /bot

COPY Pipfile .
RUN pip install pipenv && \
    pipenv install --pre && \ 
    pipenv install --deploy --system && \
    rm -r /root/.cache/* && \
    rm -r /root/.local/*

COPY bot.py *.json *.pickle /bot/
COPY modules modules

CMD [ "python", "-u", "./bot.py" ]
