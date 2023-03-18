# 和客户端保持长连接的切片策略服务器
# 基于已训练好的模型进行决策、和贪心的、单纯降级的对比
# 策略：细粒度切片，需求决定QoE运算带宽区间，需求+预测+资源切片情况作为LSTM等算法输入，输出为实际分配带宽和优先级
# 8个用户接入的场景，5个720p（1-5Mbit），3个1080p（25-33Mbit），在100Mbit的环境下运行。
# 设定分配带宽上限在35Mbit这样。
from ipaddress import ip_address
import math
import os
import socket
import ARMA_forecast
from threading import Thread
import QoEcal
import pltres
import time
import json
import numpy as np
import sliceUtil as sutil
import struct

# 默认优先级为2和6两种，尊贵的客户为1和5（越小越优先）
# tc工具的flowid分配，从3开始

# # 由于tc工具的class没法删除，因此当新的用户需求符合该切片时，可将该flowid对于的切片复用。
# g_sliceRemain = {} # key是prio，value是[band, flowid]的list

hostip = '192.168.123.149'
g_port = 5050
server_port = 5051
DEBUG = 1
Serverlist={}  #服务器列表
sliceid = 0


#初始化5051端口
def init_serverport():
    try:
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print('server_port初始化失败')
        exit()
    socketServer.bind((hostip, server_port))
    socketServer.listen(10)
    print('server_port初始化成功')
    return socketServer

# 服务器管理
def ServerManagement():
    global Serverlist
    registerSoc = init_serverport()
    while True:
        try:
            conn, addr = registerSoc.accept()
        except:
            print('接收终端通信失败。')
            break
        datalen = struct.unpack('i', conn.recv(4))[0]
        data = b''
        while len(data) < datalen:
            if datalen-len(data) >= 1024:
                data += conn.recv(1024)
            else:
                data += conn.recv(datalen-len(data))
        content = json.loads(data.decode('UTF-8'))
        if content['tp']==0:#服务器注册/修改配置
            Serverlist[content['hostname']]=content
            updateAllServerCap()
        elif content['tp']==1:#服务器注销
            Serverlist.pop(content['hostname'])
        print(Serverlist)
    
#计算资源容量
def calCapacity(Server, w1, w2):
    Server['Capacity'] = w1 * Server['BandWidth'] + w2 * Server['Connections']
    # if Server['BandWidth']<=0 or Server['Connections']<=0:
    #     Server['Capacity'] = 0
    # else:
    #     Server['Capacity'] = w1 * Server['BandWidth'] + w2 * Server['Connections']

#找资源容量最大的服务器
def getmaxCapip():
    updateAllServerCap()
    maxCap = -2147483648
    resip,resport,resname = '','',''
    for _,Server in Serverlist.items():
        if maxCap < Server['Capacity']:
            maxCap = Server['Capacity']
            resip = Server['serverip']
            resport = Server['serverport']
            resname = Server['hostname']
    return resip,resport,resname

#更新所有服务器资源容量
def updateAllServerCap():
    for servername in Serverlist:
        calCapacity(Serverlist[servername],0.5,500)

# 处理用户请求的函数（做出决策）
def dealReq(conn, addr): # 通过conn操作该socket，addr是(ip, port)
    # global g_addr_reSlQo, g_addr_qoe, g_addr_lastconnect, g_addr_qoemean, g_addr_qoemeanlist
    # global g_bandsum, g_bandinuse, g_sliaddr, g_slires, g_tcflowid, g_addr_flowid
    print('Connected by', addr)
    ipfrom = addr[0]
    while 1 :
        try:
            # 读取传输数据
            datalen = struct.unpack('i', conn.recv(4))[0]
            data = b''
            while len(data) < datalen:
                if datalen-len(data) >= 1024:
                    data += conn.recv(1024)
                else:
                    data += conn.recv(datalen-len(data))
            content = json.loads(data.decode('UTF-8'))
            tp = content['type']
            if tp == 1:#建立切片
                # 读取用户切片请求
                req, band, pack, delay, jitter, serviceip,servicename,serviceport,usersliceid = \
                    content['req'], content['BandWidth'], content['PacketLoss'], content['Delay'], content['Jitter'], content['serviceip'], content['servicename'], content['serviceport'],content['sliceid']
                jitter,delay = list(map(float,jitter)),list(map(float,delay))
                userip,userport = content['userip'],content['userport']

                # 预处理,计算Qoe
                bandfor = band # 暂存一下拿来预测
                band = sutil.average(band, 5) # 5s合一
                delay = sutil.average(delay, 5)
                jitter = sutil.average(jitter, 5)
                pack = sutil.average(pack, 5)
                qoelist = QoEcal.get_QoE(band, delay, jitter, pack, req)
                # 现在是带宽预测结和按需匹配优先级的策略：
                poss = 6
                forecastRes = ARMA_forecast.forecast(bandfor, len(bandfor) - 1) # 得到预测的20s带宽
                min_f_band,max_f_band = np.min(forecastRes),np.max(forecastRes)
                forecastRes.remove(min_f_band)
                forecastRes.remove(max_f_band)
                max_f_band,mean_f_band = np.max(forecastRes),np.mean(forecastRes)
                sliceband = round((mean_f_band/3 + max_f_band*2/3), 1)
                if req == 2 or req == 3:
                    poss = 2
                if req == 1 or req == 3:
                    if sliceband < 28: # 切片之前的可能和实际需求差距较大，后面调整。
                        sliceband = 33
                elif req == 0 or req == 2:
                    if sliceband > 6:
                        sliceband = 4 
                #更新服务节点列表和切片列表
                Server = Serverlist[servicename]
                Server['Connections'] -= 1
                tc_flowid = Server['tc_flowid']
                Server['tc_flowid'] += 1
                sliceband *= 1024
                # if Server['BandWidth'] < sliceband :
                #     sliceband = Server['BandWidth']
                Server['BandWidth'] -= sliceband 
                sliceband /= 1024
                if userip in Server['userBandwidth'].keys():
                    Server['userBandwidth'][userip] += sliceband
                else:
                    Server['userBandwidth'][userip] = sliceband
                Slice = {'sliceid':usersliceid,'userip':userip,'userport':userport,'tc_flowid':tc_flowid,'sliceband':sliceband,'poss':poss,'lastConnectTime':0,'req':req}
                Server['Slices'].append(Slice)
                # 设置服务器tc切片
                agent_msg = f'./fine_slice.sh {tc_flowid} {poss} {sliceband} {userip} {userport}'
                sentmsgtoagent(hostname = servicename,msg = agent_msg)
                print(f'为节点{servicename}设置对ip:{userip}端口:{userport}优先级{poss}带宽{sliceband}的切片,flowid为{tc_flowid}')
            elif tp == 0: # 已建立切片后终端传的内容 主要是更新QoE
                # 读取用户发送的数据
                req, band, pack, delay, jitter, serviceip,servicename,serviceport,usersliceid = \
                    content['req'], content['BandWidth'], content['PacketLoss'], content['Delay'], content['Jitter'], content['serviceip'], content['servicename'], content['serviceport'],content['sliceid']
                jitter,delay = list(map(float,jitter)),list(map(float,delay))
                userip,userport = content['userip'],content['userport']
                # 预处理，计算Qoe
                band = sutil.average(band, 5) # 5s合一
                delay = sutil.average(delay, 5)
                delay = sutil.average(jitter, 5)
                pack = sutil.average(pack, 5)
                qoelist = QoEcal.get_QoE(band, delay, jitter, pack, req) # 最后一项是通过该用户预先的req计算
                qoemean = np.mean(qoelist)
                print(f'节点{servicename},切片id:{usersliceid},当前QoE均值:{qoemean}')
                # 更新当前切片时间
                for slice in Serverlist[servicename]['Slices']:
                    if slice['sliceid'] == usersliceid:
                        slice['lastConnectTime'] = 0
                        break
            elif tp == 2: # 释放切片
                serviceip,servicename,serviceport,usersliceid = content['serviceip'], content['servicename'], content['serviceport'],content['sliceid']
                for slice in Serverlist[servicename]['Slice']:
                    if slice['sliceid'] == usersliceid:
                        # 将该用户的qoe和网络变化情况都记录下来
                        req,poss,sliceband = slice['req'],slice['poss'],slice['sliceband']
                        userip,userport = slice['userip'],slice['userport']
                        print(f'释放节点{servicename}对用户{userip}:{userport}切片(id:{usersliceid})： 需求类型:{req}，切片优先级:{poss}, 切片带宽:{sliceband}')
                        resolveSlice(servicename,userip,userport,usersliceid)
                        break     
            elif tp == 3: #用户请求接入
                global sliceid
                maxCapip,maxCapport,maxCapServername = getmaxCapip()
                msg = json.dumps({'serverip':maxCapip,'serverport':maxCapport,'servername':maxCapServername,'sliceid':sliceid})
                conn.send(struct.pack('i', len(msg)))
                conn.sendall(msg.encode('UTF-8'))
                sliceid +=1
                print(Serverlist)
                print(f'为用户{ipfrom}分配服务节点{maxCapServername},切片id：{sliceid}')
        except ConnectionResetError:
#            resolveSlice(userip)
            conn.close()
            break

# 释放切片资源，并记录该切片实例用不上了。
def resolveSlice(hostname,userip,userport,sliceid):
    Server = Serverlist[hostname]
    for i,slice in enumerate(Server['Slices']):
        if slice['sliceid']==sliceid:#找到对应切片
            Server['Connections'] += 1
            Server['BandWidth'] += slice['sliceband'] * 1000
            Server['userBandwidth'][userip] -= slice['sliceband']
            poss = slice['poss']
            tc_flowid = slice['tc_flowid']
            agent_msg='./fine_delFilter.sh' + ' ' + str(poss) + ' ' + str(userip) + ' ' + str(userport)
            sentmsgtoagent(hostname=hostname,msg=agent_msg)
            del Server['Slices'][i]
            break

# 定时器，超时时取消切片分配
def monitor_con():
    toresolve = []
    while 1:
        time.sleep(1)
        for hostname in Serverlist:
            for i,slice in enumerate(Serverlist[hostname]['Slices']):
                slice['lastConnectTime'] += 1
                if slice['lastConnectTime'] > 30: # 暂时认为150s+未发送信息的已经断开应用
                    toresolve.append([hostname,slice['userip'],slice['userport'],slice['sliceid']])
        for i in toresolve:
            print(f'超时删除，节点{i[0]}用户{i[1]}:{i[2]}切片id为{i[3]}')
            resolveSlice(i[0],i[1],i[2],i[3])
        toresolve.clear()
    

#向hostname服务器代理发送消息msg
def sentmsgtoagent(hostname,msg):
    Server = Serverlist[hostname]
    serverip,serveragentport = Server['serverip'],Server['serveragentport']
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((serverip,serveragentport))
    except socket.error as msg:
        print(msg)
        exit(1)
    msg+='END'
    s.sendall(msg.encode())
    print(f'向服务器{serverip}的代理端口{serveragentport}发送数据:{msg}')
    s.close()
    return 

# 初始化5050端口
def init_gport():
    # global g_sliaddr, g_slires, g_sliceRemain
    # g_sliaddr[2] = [] # 2和6两个优先级下的ip和分配带宽目前均为空。
    # g_sliaddr[6] = []
    # g_slires[2] = 0
    # g_slires[6] = 0
    # g_sliceRemain[2] = []
    # g_sliceRemain[6] = []
    try:
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print('gport初始化失败')
        exit()
    socketServer.bind((hostip, g_port))
    socketServer.listen(10)
    print('gport初始化成功')
    return socketServer

def UserAccess():
    socketSer = init_gport()
    while True:
        try:
            conn, addr = socketSer.accept()
        except:
            print('接收终端通信失败。')
            break
        Thread(target=dealReq, args=(conn, addr)).start()
    socketSer.close()

if __name__ == '__main__':
    print('hostip:', hostip)
    Thread(target=ServerManagement).start()
    Thread(target=UserAccess).start()
    Thread(target=monitor_con).start()
    