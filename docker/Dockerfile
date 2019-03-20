FROM ubuntu:18.04
MAINTAINER "Rodrigo Favarini <rodrigofavarini@gmail.com>"

RUN apt-get update && \
    apt-get install -y python2.7 python2.7-dev python-pip python-docutils git perl nmap sslscan nikto && \
    cd /opt && \
    git clone https://github.com/golismero/golismero.git && \
    cd golismero && \
    pip install -r requirements.txt && \
    pip install -r requirements_unix.txt && \
    ln -s /opt/golismero/golismero.py /usr/bin/golismero 

ENTRYPOINT ["golismero"]