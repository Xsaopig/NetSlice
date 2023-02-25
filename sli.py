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

# addr指的是(ip, port)这一socket
g_addr_reSlQo = {} # value是该addr的[需求类型，优先级，分配带宽]
g_addr_qoe = {} # value是该addr的[qoelist]
g_addr_qoemean = {} # value是该addr的最近一次qoe均值
g_addr_qoemeanlist = {} # value是该addr的qoe均值的list
g_addr_lastconnect = {} # 通过给每个addr标记上传数据最近时间的方式来处理未知的客户端脱离连接情况，以回收资源
g_addr_netcond = {} # value是该addr的[bandwidth, delay, jitter, pl], 用于QoE展示
g_addr_slicetime = {} # ip:slicetime
# 记录网络分配情况。要用到的是：某个优先级分配的总带宽，剩余带宽。其中分配的带宽都是下限！
# ip分配给了什么类型，ip分配的带宽和优先级
# 默认优先级为2和6两种，尊贵的客户为1和5（越小越优先）
g_bandsum = 100 # 总带宽100Mbit
g_sliaddr = {} # 以优先级类型为key，该优先级下的addrlist为value，存分配给切片类型的的用户ip们
g_slires = {} # 以优先级类型为key，该优先级下分配的带宽为value，记录网络分配情况。用于算法决策
g_bandinuse = 0 # 目前分配的总bandwidth
# 是否要记录每个优先级目前的平均时延和抖动？暂时不用吧

# tc工具的flowid分配，从3开始
g_tcflowid = 3
g_addr_flowid = {} # 某个socket对应的flowid

# 由于tc工具的class没法删除，因此当新的用户需求符合该切片时，可将该flowid对于的切片复用。
g_sliceRemain = {} # key是prio，value是[band, flowid]的list

hostip = '192.168.123.149'
g_port = 5050
server_port = 5051
DEBUG = 1
Serverlist={}  #服务器列表



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


# 等待服务器注册
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
        if content['tp']==0:
            Serverlist[content['serverip']]=content
            calCapacity(Serverlist[content['serverip']],0.5,500)
        elif content['tp']==1:
            Serverlist.pop(content['serverip'])
        print(Serverlist)
    
#计算资源容量
def calCapacity(Server, w1, w2):
    Server['Capacity'] = w1 * Server['BandWidth'] + w2 * Server['Connections']

#找资源容量最小的服务器
def getminCapip():
    minCap = -1
    res = ''
    for ip,Server in Serverlist.items():
        if minCap > Server['Capacity'] or minCap == -1:
            minCap = Server['Capacity']
            res = ip
    return res

# 处理用户请求的函数（做出决策）
def dealReq(conn, addr): # 通过conn操作该socket，addr是(ip, port)
    global g_addr_reSlQo, g_addr_qoe, g_addr_lastconnect, g_addr_qoemean, g_addr_qoemeanlist
    global g_bandsum, g_bandinuse, g_sliaddr, g_slires, g_tcflowid, g_addr_flowid
    print('Connected by', addr)
    ipfrom = addr[0]
    serviceip = ''

    while 1 :
        try:
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
                req, band, pack, delay, jitter, serviceip = \
                    content['req'], content['BandWidth'], content['PacketLoss'], content['Delay'], content['Jitter'], content['serviceip']
                jitter = list(map(float,jitter))
                delay = list(map(float,delay))

                bandfor = band # 暂存一下拿来预测
                band = sutil.average(band, 5) # 5s合一
                delay = sutil.average(delay, 5)
                jitter = sutil.average(jitter, 5)
                pack = sutil.average(pack, 5)
                print(f'band:{band}')
                # if ipfrom in g_addr_qoe: # 之前的切片没有释放
                #     resolveSlice(ipfrom)
                qoelist = QoEcal.get_QoE(band, delay, jitter, pack, req)
                g_addr_netcond[ipfrom] = [band, delay, jitter, pack]
                g_addr_qoe[ipfrom] = qoelist
                qoemean = np.mean(qoelist)
                print(f'QoE:{qoelist}')
                g_addr_qoemean[ipfrom] = qoemean
                g_addr_qoemeanlist[ipfrom] = [qoemean]
                # 将网络质量等输入策略，输出带宽和优先级
                # max_abs_scaler = preprocessing.MaxAbsScaler()
                # poss = g_model1.predict(max_abs_scaler.fit_transform(nnc))
                # # 得到策略输出，执行切片
                # if poss > 2.1:
                #     poss = 3
                # elif poss > 1.5 and poss <= 2.1:
                #     poss = 2
                # elif poss <= 1.5 and poss > 0.9:
                #     poss = 1
                # else:
                #     poss = 0 

                # 现在是带宽预测结和按需匹配优先级的策略：
                poss = 6
                forecastRes = ARMA_forecast.forecast(bandfor, len(bandfor) - 1) # 得到预测的20s带宽
                min_f_band = np.min(forecastRes)
                max_f_band = np.max(forecastRes)
                forecastRes.remove(min_f_band)
                forecastRes.remove(max_f_band)

                max_f_band = np.max(forecastRes)
                mean_f_band = np.mean(forecastRes)
                sliceband = round((mean_f_band/3 + max_f_band*2/3), 1)
                if req == 2 or req == 3:
                    poss = 2
                if req == 1 or req == 3:
                    if sliceband < 28: # 切片之前的可能和实际需求差距较大，后面调整。
                        sliceband = 33
                elif req == 0 or req == 2:
                    if sliceband > 6:
                        sliceband = 4 

                # os.system('./show.sh')
                # print('执行命令：'+'./fine_slice.sh' + ' ' + str(g_tcflowid) + ' ' + str(poss) + ' ' + str(sliceband) + ' ' + str(ipfrom))
                # os.system('./fine_slice.sh' + ' ' + str(g_tcflowid) + ' ' + str(poss) + ' ' + str(sliceband) + ' ' + str(ipfrom))
                print(f'为 {ipfrom} 设置优先级{poss}带宽{sliceband}的切片,id为{g_tcflowid}')
                # os.system('./show.sh')
                print('-'*40)

                agent_msg='./fine_slice.sh' + ' ' + str(g_tcflowid) + ' ' + str(poss) + ' ' + str(sliceband) + ' ' + str(ipfrom)
                sentmsgtoagent(serviceip,agent_msg)



                g_addr_slicetime[ipfrom] = len(band)

                # 更新结果
                g_addr_flowid[ipfrom] = g_tcflowid # 更新全局flowid
                g_tcflowid += 1

                g_sliaddr[poss].append(ipfrom) # 在该优先级的addrlist中加入该addr
                g_slires[poss] = g_slires[poss] + sliceband # 更新该优先级使用带宽的结果
                g_bandinuse += sliceband # 加上新占用的带宽
                g_addr_reSlQo[ipfrom]= [req, poss, sliceband]
                g_addr_lastconnect[ipfrom] = {}
                g_addr_lastconnect[ipfrom][serviceip] = 0

            elif tp == 0: # 已建立切片后终端传的内容 主要是更新QoE
                req, band, pack, delay, jitter, serviceip = \
                    content['req'], content['BandWidth'], content['PacketLoss'], content['Delay'], content['Jitter'], content['serviceip']
                jitter = list(map(float,jitter))
                delay = list(map(float,delay))

                band = sutil.average(band, 5) # 5s合一
                delay = sutil.average(delay, 5)
                delay = sutil.average(jitter, 5)
                pack = sutil.average(pack, 5)
                # print(f'band:{band}')
                blast = g_addr_netcond[ipfrom][0]
                dlast = g_addr_netcond[ipfrom][1]
                jlast = g_addr_netcond[ipfrom][2]
                plast = g_addr_netcond[ipfrom][3]

                qoelist = QoEcal.get_QoE(band, delay, jitter, pack, g_addr_reSlQo[ipfrom][0]) # 最后一项是通过该用户预先的req计算
                # print(f'qoelist:{qoelist}')
                # print(f'before:{g_addr_qoe[ipfrom]}')
                g_addr_qoe[ipfrom] = sutil.updatelist(g_addr_qoe[ipfrom], qoelist, 30000) # qoe list 往后续上
                # print(f'after:{g_addr_qoe[ipfrom]}\n')

                qoemean = np.mean(qoelist)
                print(f'当前QoE均值:{qoemean}')
                g_addr_qoemean[ipfrom] = qoemean
                g_addr_qoemeanlist[ipfrom].append(qoemean)

                blast = sutil.updatelist(blast, band, 30000)
                dlast = sutil.updatelist(dlast, delay, 30000)
                jlast = sutil.updatelist(jlast, jitter, 30000)
                plast = sutil.updatelist(plast, pack, 30000)
                g_addr_netcond[ipfrom] = [blast, dlast, jlast, plast]
                g_addr_lastconnect[ipfrom] = {}
                g_addr_lastconnect[ipfrom][serviceip] = 0
            
            elif tp == 2: # 释放切片的操作
                # 将该用户的qoe和网络变化情况都记录下来
                print(f'释放用户{ipfrom}： 需求类型:{g_addr_reSlQo[ipfrom][0]}，切片优先级:{g_addr_reSlQo[ipfrom][1]}, 切片带宽:{g_addr_reSlQo[ipfrom][2]}')
                print("QoE变化情况：")
                printUserQoe(ipfrom)
                print('')
                saveResfig(ipfrom)
                resolveSlice(serviceip,ipfrom)
                break
            
            elif tp == 3: #用户请求接入
                mincapip = getminCapip()
                msg = json.dumps({'serverip':mincapip})
                conn.send(struct.pack('i', len(msg)))
                conn.sendall(msg.encode('UTF-8'))


        except ConnectionResetError:
#            resolveSlice(ipfrom)
            conn.close()
            break

'''
释放切片和定时判断是否要释放切片的函数
'''
# 释放切片资源，并记录该切片实例用不上了。
def resolveSlice(serviceip,ipfrom):
    global g_addr_reSlQo, g_addr_qoe, g_addr_netcond, g_addr_slicetime, g_addr_lastconnect, g_addr_flowid, g_addr_qoemean, g_addr_qoemeanlist
    global g_sliaddr, g_slires, g_bandinuse, g_sliceRemain
    if g_addr_reSlQo.get(ipfrom, 0) != 0: # 已经分配过切片的
        prio = g_addr_reSlQo[ipfrom][1] # 获取优先级类型
        bandresolve = g_addr_reSlQo[ipfrom][2]
        flowid = g_addr_flowid[ipfrom] # 获取切片资源的id
        print(f'为 {ipfrom} 删除优先级{prio}带宽{bandresolve}的切片,id为{flowid}') 
        # os.system('./show.sh')
        
        # 删除切片
        strdel = './fine_delFilter.sh' + ' ' + str(flowid) + ' ' + str(ipfrom) + ' ' + str(flowid)
        print('删除指令：' + strdel)
        # os.system('./fine_delFilter.sh' + ' ' + str(flowid) + ' ' + str(ipfrom))

        agent_msg='./fine_delFilter.sh' + ' ' + str(flowid) + ' ' + str(ipfrom)
        sentmsgtoagent(serviceip,agent_msg)

        # print("删除后")
        # os.system('./show.sh')
        print('-'*40)
        g_addr_flowid.pop(ipfrom)
        g_addr_reSlQo.pop(ipfrom)
        g_addr_lastconnect[ipfrom].pop(serviceip)
        g_addr_qoe.pop(ipfrom)
        g_addr_netcond.pop(ipfrom)
        g_addr_qoemean.pop(ipfrom)
        g_addr_qoemeanlist.pop(ipfrom)
        g_addr_slicetime.pop(ipfrom)
        # 更新剩余带宽
        g_bandinuse -= bandresolve
        g_slires[prio] -= bandresolve
        g_sliaddr[prio].remove(ipfrom)
        g_sliceRemain[prio].append([flowid, bandresolve]) # 记录空闲的切片，以后可以用上，本实验不考虑

# 定时器，超时时取消切片分配
def monitor_con():
    global g_addr_lastconnect
    toresolve = []
    while 1:
        time.sleep(1)
        keys = g_addr_lastconnect.keys()
        for k in keys:
            for ip in g_addr_lastconnect[k]:
                g_addr_lastconnect[k][ip] = g_addr_lastconnect[k][ip] + 1
                # if(DEBUG):print(f"监视 count：{k}:{g_addr_lastconnect[k]}")
                if g_addr_lastconnect[k][ip] > 150: # 暂时认为150s+未发送信息的已经断开应用
                    toresolve.append([ip,k])
        for i in toresolve:
            resolveSlice(i[0],k)
'''
查看qoe及结果相关的函数
'''
# 输出某个用户的QoE情况。
def printUserQoe(ipfrom):
    global g_addr_qoemeanlist
    for i in g_addr_qoemeanlist[ipfrom]:
        print(i, end=' ')
    print('')

# 主线程接收终端输入，然后输出用户优先级和带宽，及QoE结果
def getinput():
    global g_addr_reSlQo
    print('输入1查看qoe变化情况')
    while 1:
        cmd = input()
        if cmd == '1':
            for k in g_addr_reSlQo.keys(): # 有接入用户
                print(f'用户{k[0]}： 需求类型:{g_addr_reSlQo[k][0]}，切片优先级:{g_addr_reSlQo[k][1]}, 切片带宽:{g_addr_reSlQo[k][2]}')
                print("QoE变化情况：")
                printUserQoe(k)
                print('')

# 将结果保存成图片可视化的函数
def saveResfig(ipfrom):
    global g_addr_qoe, g_addr_netcond
    # with open (ipfrom, 'w') as f:
    #     f.write('qoe:\n')
    #     f.write(sutil.iListTStr(g_addr_qoe[ipfrom]))
    #     f.write('\nband:\n')
    #     f.write(sutil.iListTStr(g_addr_netcond[ipfrom][0]))
    #     f.write('\n')
    #     f.write(str(g_addr_slicetime[ipfrom]))
    pltres.initfig()
    strname = str(ipfrom)
    pltres.pltlist(g_addr_qoe[ipfrom], 'Time(5s)', 'QoE', strname + 'QoE')
    pltres.pltylin(g_addr_slicetime[ipfrom], 'Start slice')
    pltres.finish(ipfrom + 'QoE')

    pltres.initfig()
    pltres.pltlist(g_addr_netcond[ipfrom][0], 'Time(5s)', 'Bandwidth', strname + 'Bandwidth')
    pltres.pltylin(g_addr_slicetime[ipfrom], 'Start slice')
    pltres.finish(ipfrom + 'Bandwidth')

#向aimip服务器代理发送消息msg
def sentmsgtoagent(aimip,msg,agent_port=8081):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((aimip,agent_port))
    except socket.error as msg:
        print(msg)
        exit(1)

    msg+='END'
    s.sendall(msg.encode())
    print('向服务器'+aimip+'的代理发送数据:'+msg)
    s.close()
    return 


# 初始化5050端口
def init_gport():
    global g_sliaddr, g_slires, g_sliceRemain
    g_sliaddr[2] = [] # 2和6两个优先级下的ip和分配带宽目前均为空。
    g_sliaddr[6] = []
    g_slires[2] = 0
    g_slires[6] = 0
    g_sliceRemain[2] = []
    g_sliceRemain[6] = []


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
    # Thread(target=getinput).start()
    