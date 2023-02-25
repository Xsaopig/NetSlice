# 和客户端保持长连接的切片策略服务器
# 基于已训练好的模型进行决策、和贪心的、单纯降级的对比
# 策略：细粒度切片，需求决定QoE运算带宽区间，需求+预测+资源切片情况作为LSTM等算法输入，输出为实际分配带宽和优先级
# 8个用户接入的场景，5个720p（1-5Mbit），3个1080p（25-33Mbit），在100Mbit的环境下运行。
# 设定分配带宽上限在35Mbit这样。
from ipaddress import ip_address
import math
import os
import socket
from threading import Thread
import time
import json
import numpy as np
g_port = 8081

# 初始化服务器代理
def init():
    hostip = '192.168.133.100'
    print('hostip:', hostip)
    try:
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print('服务器创建失败')
        exit()
    socketServer.bind((hostip, g_port))
    socketServer.listen(10)
    print('服务器代理开始运行 port '+str(g_port))
    os.system('./fine_init_tc.sh')
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

if __name__ == '__main__':
    # 初始化切片策略服务器
    socketSer = init()
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
