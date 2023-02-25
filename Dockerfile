FROM continuumio/anaconda3
RUN mkdir ./app
COPY ./ ./app
WORKDIR ./app
