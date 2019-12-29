FROM python:3

WORKDIR /bot
RUN pip install pipenv
COPY Pipfile .
RUN pipenv install --pre

COPY bot.py .
COPY modules modules

# googlecal: copy credentials.json and token.pickle if they exist
COPY *.json .
COPY *.pickle .

CMD [ "pipenv", "run", "python", "-u", "./bot.py" ]
