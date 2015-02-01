FROM python:2-onbuild

MAINTAINER Peter Salvatore <peter@psftw.com>

RUN tinker -b

VOLUME ["/usr/src/app/blog/html"]
