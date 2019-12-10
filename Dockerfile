FROM python:3

WORKDIR /bot
RUN pip install pipenv
COPY Pipfile .
RUN pipenv install --skip-lock --system

COPY bot.py .
COPY modules modules

# Uncomment for google calendar:

#COPY credentials.json .
#COPY token.pickle .

CMD [ "python", "-u", "./bot.py" ]
