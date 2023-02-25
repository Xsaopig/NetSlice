# FROM ubuntu
FROM continuumio/anaconda3
#FROM python:3.12-rc-bullseye
COPY . /app
WORKDIR /app
EXPOSE 8080
EXPOSE 5050

RUN apt-get update
# # iproute2 包含了 tc 命令
RUN apt-get -y install iproute2
# RUN apt-get -y install pip

# 配置pip镜像
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
# RUN pip install -r requirements.txt

# CMD python ./service_tcp.py
# CMD python ./sli_fine.py

## docker build -t netslice ./
## docker run -i -t --name 123123 --cap-add=NET_ADMIN --privileged=true --network=bridge -p 8080:8080 -p 5050:5050 netslice
## docker exec -it 123123 /bin/bash