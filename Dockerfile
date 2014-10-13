FROM python:2-onbuild

RUN tinker -b && mkdir -p /srv/www && mv blog/html /srv/www/psftw.com

VOLUME /srv/www/psftw.com
