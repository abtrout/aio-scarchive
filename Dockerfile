FROM python:3.6-alpine

COPY . /archive

RUN pip install -r /archive/requirements.txt

CMD [ "/archive/run.sh" ]
