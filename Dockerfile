# FROM ubuntu
FROM continuumio/anaconda3
# FROM python:3.12-rc-bullseye
COPY ./ /app
WORKDIR /app
EXPOSE 5051
EXPOSE 5050


# RUN apt-get update
# # # iproute2 包含了 tc 命令
# RUN apt-get -y install iproute2
# RUN apt-get -y install pip

# 配置pip镜像
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
# RUN pip install -r requirements.txt

CMD python ./sli.py

## 阿里云仓库https://cr.console.aliyun.com/repository/cn-hangzhou/network_sli/sli/details
## docker build -t sli ./sli/ -f ./Dockerfile.dockerfile
## docker run -i -t --name 123123 -p 5051:5051 -p 5050:5050 sli
## docker exec -it 123123 /bin/bash
## docker tag sli docker.io/xsaopig/sli:20230325
## docker push xsaopig/sli:20230325