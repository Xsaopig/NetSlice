# '''
# 模拟云渲染服务器 TCP传输视频版本
# 端口：8080
# '''
from logging import exception
import cv2, imutils, socket
import numpy as np
import time
import base64
import threading, wave, pickle, struct
import sys
from threading import Thread
import queue
import os
import json
from service_agent import agent_start

hostip = '192.168.133.100'
lisvidport,agent_port = 8080,8081
filename = './video/vedio.mp4'
sli_ip = '192.168.123.149'
sli_port = 5051
MaxBandWidth = 60*1024 #kbps
MaxConnections = 3 #最大连接数
Content = {'serverip':'192.168.123.149', 'BandWidth':MaxBandWidth, 'Connections':MaxConnections, 'tp': 0, 'serverport':50000, 'hostname':'master','serveragentport':50010,
        'tc_flowid':3,'userBandwidth':{},'Slices':[]}

# 建立socket通信
def socket_bulid(ipaddr, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipaddr, port))
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    return s


def registerOrlogout(content,Sli_ip,Sli_port):
    sli_soc=socket_bulid(Sli_ip,Sli_port)
    msg = json.dumps(content)
    sli_soc.send(struct.pack('i', len(msg)))
    sli_soc.sendall(msg.encode('UTF-8'))
    sli_soc.close()
    return True


def init():  # 初始化视频的监听socket
    print('hostip:', hostip, 'port', lisvidport)
    try:
        socketvid = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print('渲染服务器创建失败')
        exit()

    socketvid.bind((hostip, lisvidport))
    socketvid.listen(10)
    print('渲染服务器开始运行')
    return socketvid


def video_stream_gen(video, myq):  # 生成视频流
    WIDTH = 600
    count = 0
    while (video.isOpened()):
        # try:
        _, frame = video.read()
        if frame is None:
            if count < 10:
                # print('视频传输到尽头，重新传输')
                video = cv2.VideoCapture(filename)
                count += 1
                continue
            else:
                break
        frame = imutils.resize(frame, width=WIDTH)  # 调整大小
        myq.put(frame)
        # except :
        #     print('因为这个退出？') # 真是这里
        #     os._exit(1)
    print('Player closed')
    video.release()


def video_stream(cl_socket, client_addr, qNew, video):
    FPS = video.get(cv2.CAP_PROP_FPS)
    TS = (0.8 / FPS)  # 每帧花多少个0.8s？渲染采样时间
    fps, st, frames_to_count, cnt = (0, 0, 8, 0)  # 这几个变量和TS都是每个用户独有的。frames_to_count应该是每多少帧检测FPS这样
    # cv2.namedWindow('TRANSMITTING VIDEO')        
    # cv2.moveWindow('TRANSMITTING VIDEO', 10, 30) 
    print('GOT connection from ', client_addr)
    WIDTH = 600
    try:
        while (True):
            frame = qNew.get()
            encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            message = base64.b64encode(buffer)
            message = struct.pack("Q", len(message)) + message
            cl_socket.sendall(message)
            frame = cv2.putText(frame, 'FPS: ' + str(round(fps, 1)), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (0, 0, 255), 2)
            if cnt == frames_to_count:
                try:
                    fps = (frames_to_count / (time.time() - st))  # 记录时间
                    st = time.time()
                    cnt = 0
                    if fps > FPS:
                        TS += 0.00005  # 粒度别太大了！
                    elif fps < FPS:  # 慢了惩罚高
                        if TS > 0:
                            TS -= 0.00005
                    else:
                        pass
                except:
                    pass
            cnt += 1
            if TS >= 0:
                time.sleep(TS)
            # key = cv2.waitKey(int(1000 * TS)) & 0xFF	
            # cv2.imshow('TRANSMITTING VIDEO', frame) # 是在服务器也显示视频时才会做的检测q退出
            # if key == ord('q'):
            #     os._exit(1)
            # TS=False
            # break
    except ConnectionAbortedError as ce:
        print(f'{client_addr}断开链接')
    print('video_stream结束')


if __name__ == "__main__":
    Thread(target=agent_start, args=(hostip,agent_port,MaxBandWidth/1024,)).start()
    res = registerOrlogout(Content,sli_ip,sli_port)
    if res == False:
        print('向SLI注册失败')
        exit(1)
    print('向SLI注册成功')
    # res = registerOrlogout({'serverip':hostip,'tp':1},sli_ip,sli_port)
    # if res == False:
    #     print('向SLI注销失败')
    #     exit(1)
    # print('向SLI注销成功')
    vidListen = init()
    while True:
        try:
            conn, addr = vidListen.accept()
        except:
            print('接收终端通信失败。')
            break
        ans = videoNew = cv2.VideoCapture(filename)  # 新建一个？会一个快一个慢orz咋回事
        if (videoNew.isOpened() == False):
            print('打开文件失败', filename)
            print(ans)
            break
        qNew = queue.Queue(maxsize=10)  # 每个用户建一个帧队列
        t1 = Thread(target=video_stream_gen, args=(videoNew, qNew))  # 为啥它结束之后会自动服务器停掉啊？？
        t2 = Thread(target=video_stream, args=(conn, addr, qNew, videoNew))
        t1.setDaemon(True)  # 能随着control-c一起退出 算了目前还是不行
        t2.setDaemon(True)
        t1.start()
        t2.start()
    vidListen.close()

