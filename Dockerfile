FROM python:3.8.0

ENV TZ America/Denver
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./src /src

RUN pip install -r /src/requirements.txt

RUN git clone https://github.com/WillNess210/frcpy /usr/local/lib/python3.8/site-packages/frcpy

CMD python -u /src/main2.py
