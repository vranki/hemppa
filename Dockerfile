FROM python:3

WORKDIR /bot
RUN pip install pipenv
COPY Pipfile .
RUN pipenv install --skip-lock --system

COPY bot.py .

CMD [ "python", "-u", "./bot.py" ]
