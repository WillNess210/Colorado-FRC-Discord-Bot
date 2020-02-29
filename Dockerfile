FROM python:3.8.0

ENV TZ America/Denver
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./src /src

RUN pip install -r /src/requirements.txt

CMD python -u /src/main.py
