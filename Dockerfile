FROM python:3

WORKDIR /bot
RUN pip install pipenv
COPY Pipfile .
RUN pipenv install --pre

COPY bot.py *.json *.pickle /bot/
COPY modules modules

CMD [ "pipenv", "run", "python", "-u", "./bot.py" ]
