FROM python:3

WORKDIR /bot
RUN pip install pipenv && rm -rf /root/.cache
COPY Pipfile .
RUN pipenv install --pre && rm -rf /root/.cache

COPY bot.py *.json *.pickle /bot/
COPY modules modules

CMD [ "pipenv", "run", "python", "-u", "./bot.py" ]
