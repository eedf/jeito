FROM python:3.5
RUN apt-get update && apt-get install -y postgresql-client
RUN useradd -ms /bin/bash django
WORKDIR /home/django
ADD requirements.txt .
RUN pip install -r requirements.txt
USER django
CMD ./manage.py runserver 0.0.0.0:8000
