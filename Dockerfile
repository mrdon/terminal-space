FROM python:3.7

RUN mkdir -p /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip
#RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
WORKDIR /usr/src/app

COPY . /usr/src/app

EXPOSE 8080
WORKDIR /usr/src/app
CMD python server.py
