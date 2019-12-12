FROM python:3.7

ENV PYTHONUNBUFFERED 1

MAINTAINER Salman Qasim

ADD . /code
WORKDIR /code

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /code/requirements.txt

#ENV FLASK_APP main.py

ENV PORT 8080
CMD ["gunicorn", "main:app"]

#CMD gunicorn -w 4 -b 0.0.0.0:5000 main:app
