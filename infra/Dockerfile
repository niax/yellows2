FROM node:18-alpine

RUN mkdir /src
WORKDIR /src

RUN npm install -g aws-cdk@2.35.0 \
 && apk add --update docker

COPY package.json package-lock.json /src/
RUN npm install

COPY * /src/
