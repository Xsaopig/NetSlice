'''
传输720P30帧时延需求一般的音视频渲染流,tcp版本。
'''
import math
import platform
from tkinter.tix import Tree
import cv2, imutils, socket
import numpy as np
import time, os
import base64
import threading, wave, pickle, struct, sys
import json

timelist = []
allspeedlist = [] # 仅做测试显示 带宽总变化情况
speedlist = []
delaylist = []
jitlist = []
pllist = []

is_slice = 0

serviceip = ''
sliip = "192.168.123.149"

recvcount = 0.0 # 统计速率
DEBUG = 1
g_th_flag = True
print('等待渲染服务器发送文件:')
BUFF_SIZE = 65536

# 建立socket通信。第三个参数为1时是UDP(和渲染服务器通信)
def socket_bulid(ipaddr, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipaddr, port))
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    return s

# 两个list转换的工具类函数
def iListTStr(l):
    lstr = [str(x) for x in l]
    return ', '.join(lstr)
def strListTf(l):
    li = [float(x) for x in l]
    return li

# 按需分类模块：
# 返回整型表示的用户需求
def getreq(resol, fps, gametype):
    if resol == 720 and fps == 30: # 低带宽
        if gametype: # 低时延
            return 2
        else:
            return 0
    elif resol == 1080 and fps == 60:
        if gametype:
            return 3
        else:
            return 1
    return -1

# 网络测量模块：
# 函数1：测量带宽(kbps)
def getspeed():
    global recvcount, speedlist # 存的是float形式
    time.sleep(1) # 先让渲染通信进入正常状态
    while g_th_flag:
        recvcount = 0.0
        time.sleep(1)
        recvcount = recvcount / 1000 * 8 #速率领域的kbps似乎是1000进制！
        speedlist.append(recvcount)
        allspeedlist.append(recvcount)
        if(len(speedlist) > 120):
            speedlist.pop(0)
        print(f'speed:{recvcount} kbps')
# 网络测量函数2：测量时延丢包率
def getother():
    global pllist, delaylist, serviceip
    time.sleep(1) # 与speed同步
    while g_th_flag:
        time.sleep(1)
        param = '-n' if platform.system().lower()=='windows' else '-c'
        result = os.popen('ping {} 1 {}'.format(param, serviceip)).read()
        # result = os.popen('ping {} 1 {}'.format(param, 'www.baidu.com')).read()
        # print(f'res:{result}')
        plstart = '丢失 = '
        pls = result.find(plstart)
        ple = result.find(' (', pls, pls + 10)
        los = result[pls + len(plstart):ple]
        pllist.append(los)
        if(len(pllist) > 120):
            pllist.pop(0)
        # print(f'los:{los}') 
        # 读取时延
        dlstart = '平均 = '
        dls = result.find(dlstart)
        dle = result.find('ms', dls, dls + 10)
        dl = result[dls + len(dlstart):dle]
        delaylist.append(dl)
        if(len(delaylist) > 120):
            delaylist.pop(0)
        # print(f'delay:{dl}') 
# 网络测量函数3：计算抖动
def caljit(): # 存的是str形式
    global jitlist, delaylist
    i = 1
    t = []
    while i < len(delaylist):
        t.append(math.fabs(int(delaylist[i - 1]) - int(delaylist[i])))
        i += 1
    jitlist = [str(x) for x in t]


# 和策略服务器定时通信（目前实验全需要切片）。req是需求类型，tp表示是建立切片的发送还是已建立切片只上传qoe的
def sendToSli(ssl):
    # req = getreq(720, 30, 0) # 需求低带宽低延迟类型2
    req =3
    global speedlist, delaylist, jitlist, pllist
    tp = 1
    while g_th_flag:
        time.sleep(15)
        caljit()
        if len(pllist):
            pl = sum(strListTf(pllist)) / len(pllist)
        else:
            pl = 0.0
        # print(f'{len(speedlist)}, {len(delaylist)}, {len(jitlist)}, {len(pllist)}')
        print(speedlist)

        Content = {'type':tp, 'BandWidth':speedlist, 'Delay': delaylist,'Jitter':jitlist, 'PacketLoss':[pl], 'req':req, 'serviceip':serviceip}
        msg = json.dumps(Content)
        ssl.send(struct.pack('i', len(msg)))
        ssl.sendall(msg.encode('UTF-8'))

        # 清空原网络质量情况    
        speedlist.clear()
        delaylist.clear()
        jitlist.clear()
        pllist.clear()
        if tp == 1: # 只发送一次
            tp = 0

# 和渲染服务器通信的函数
def video_stream(video_socket): # 接收视频流 UDP
    global recvcount, g_th_flag # 统计带宽
    cv2.namedWindow('RECEIVING VIDEO')        
    cv2.moveWindow('RECEIVING VIDEO', 10,360) 
    fps,st,frames_to_count,cnt = (0,0,10,0)
    payload_size = struct.calcsize("Q")
    data = b""
    while g_th_flag:
        while len(data) < payload_size:
            packet = video_socket.recv(4*1024) # 4K
            if not packet: break
            data += packet
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q",packed_msg_size)[0] # 读取长度
        recvcount += msg_size
        while len(data) < msg_size:
            data += video_socket.recv(4 * 1024)
        frame_data = data[:msg_size]
        data  = data[msg_size:]
        viddata = base64.b64decode(frame_data,' /')
        npdata = np.fromstring(viddata, dtype=np.uint8)

        frame = cv2.imdecode(npdata,1)
        frame = cv2.putText(frame,'FPS: '+str(fps),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
        cv2.imshow("RECEIVING VIDEO",frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            ss_soc.sendall('type=2'.encode())
            time.sleep(0.1)
            g_th_flag = False   
            video_socket.close()
            print('客户端结束运行')
            print('历史速率', allspeedlist)
            os._exit(1)
            break
        if cnt == frames_to_count:
            try:
                fps = round(frames_to_count/(time.time()-st))
                st = time.time()
                cnt=0
            except:
                pass
        cnt+=1
		
    video_socket.close()
    cv2.destroyAllWindows() 

#返回渲染服务器ip
def getserviceip(soc):
    Content = {'type':3}
    msg = json.dumps(Content)
    soc.send(struct.pack('i', len(msg)))
    soc.sendall(msg.encode('UTF-8'))
    
    datalen = struct.unpack('i', soc.recv(4))[0]
    data = b''
    while len(data) < datalen:
        if datalen-len(data) >= 1024:
            data += soc.recv(1024)
        else:
            data += soc.recv(datalen-len(data))
    content = json.loads(data.decode('UTF-8'))
    return content['serverip'],content['serverport']

if __name__ == '__main__':
    # 初始化
    ss_soc = socket_bulid(sliip, 5050) # 策略服务器
    serviceip,serviceport = getserviceip(ss_soc)
    print('server = '+serviceip+":"+serviceport)
    vid_soc = socket_bulid(serviceip, serviceport) # 渲染服务器
    # 预先感知文件长度
    # 开启网络质量监测
    t1 = threading.Thread(target = getspeed)
    # t1.setDaemon(True) # 能随着control-c一起退出
    t1.start()
    t2 = threading.Thread(target = getother)
    # t2.setDaemon(True)
    t2.start()

    # 进入通信
    try:
        t3 = threading.Thread(target = video_stream, args=(vid_soc, ))
        t4 = threading.Thread(target = sendToSli, args=(ss_soc, ))
        # t3.setDaemon(True)
        # t4.setDaemon(True)
        t3.start()
        t4.start()
        t1.join()
        t2.join()
        t3.join()
        t4.join()
    except KeyboardInterrupt as e:
        g_th_flag = False
        ss_soc.sendall('type=2'.encode())
        print('客户端结束运行')
        os._exit(0)
