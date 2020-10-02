FROM python:3-slim-buster
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "tucan_grade_notifier.py", "-l debug.log", "-u uniquetuid", "-p strongpassword!", "-m me@webmail.com", "-i 30"]
