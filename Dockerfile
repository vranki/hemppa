FROM python:3

WORKDIR /bot
RUN pip install pipenv
COPY Pipfile .
RUN pipenv install --pre

COPY bot.py .
COPY modules modules

# Make sure these exist
RUN touch credentials.json
RUN touch token.pickle

COPY credentials.json .
COPY token.pickle .

CMD [ "pipenv", "run", "python", "-u", "./bot.py" ]
