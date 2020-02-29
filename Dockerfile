FROM python:3.8.0

COPY ./src /src

RUN pip install -r /src/requirements.txt

CMD python -u /src/main.py
