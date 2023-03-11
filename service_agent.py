from ipaddress import ip_address
import math
import os
import socket
from threading import Thread
import time
import json
import numpy as np

# 初始化服务器代理
def init(hostip,agent_port,MaxBandWidth):
    print('hostip:', hostip)
    try:
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print('服务器创建失败')
        exit()
    socketServer.bind((hostip, agent_port))
    socketServer.listen(10)
    print('服务器代理开始运行 port '+str(agent_port))
    os.system(f'./fine_init_tc.sh {MaxBandWidth}')
    print('Traffic control 初始化成功')
    return socketServer

def getmsg(conn,addr):
    rcvmsg = ""
    while 1:
        t = conn.recv(9192)
        msg = t.decode()
        rcvmsg += msg
        idx=rcvmsg.find('END')
        if idx != -1: # 消息结尾
            rcvmsg=rcvmsg[:idx]
            break
    return rcvmsg

def agent_start(hostip,agent_port,MaxBandWidth):
    print(f'MaxBandWidth={MaxBandWidth}')
    # 初始化切片策略服务器
    socketSer = init(hostip,agent_port,MaxBandWidth)
    while True:
        try:
            conn, addr = socketSer.accept()
        except:
            print('接收终端通信失败。')
            break
        msg=getmsg(conn,addr)
        print('接收到来自'+addr[0]+'的数据:'+msg)
        os.system(msg)
    socketSer.close()

if __name__ == '__main__':
    agent_start()
