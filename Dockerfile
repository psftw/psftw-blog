FROM python:2-onbuild

MAINTAINER Peter Salvatore <peter@psftw.com>

RUN tinker -b && mkdir -p /srv/www && mv blog/html /srv/www/psftw.com

VOLUME /srv/www/psftw.com

CMD ["/usr/local/bin/tinker", "-b"]
