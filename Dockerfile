FROM python:3-slim-buster
ADD . /code
WORKDIR /code
RUN groupadd -g 124 postfix && \
        groupadd -g 125 postdrop && \
    useradd -u 116 -g 124 postfix

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    postfix \
    bsd-mailx

RUN pip install -r requirements.txt
RUN mkfifo /var/spool/postfix/public/pickup
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
