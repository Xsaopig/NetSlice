'''
工具类，用于解析终端传递的msg字符串
将list转化为str
等
'''
# 解析终端发送的数据
def parsemsg(msg, tp):
    if tp == 0:
        band = getarray(msg, 'BandWidth=[')
        pack = getarray(msg, 'PacketLoss=[')
        delay = getarray(msg, 'Delay=[')
        jitter = getarray(msg, 'Jitter=[')
        jitter.append(0) # 长度为119的补充最后一位

        idx = msg.find('serviceip=')
        if idx != -1 :
            idx2 = msg.find(',', idx)
            serviceip = msg[idx + len('Rsrq='):idx2]
        else:
            serviceip = ''

        return band, pack, delay, jitter,serviceip
    elif tp == 1:
        idx = msg.find('req=')
        if idx != -1:
            req = int(msg[idx + 4]) # 0-3
        else:
            req = -1
        
        idx = msg.find('UpBandWidth=')
        if idx != -1 :
            idx2 = msg.find(',', idx)
            ubw = int(msg[idx + len('UpBandWidth='):idx2])
        else:
            ubw = 0

        idx = msg.find('DownBandWidth=')
        if idx != -1 :
            idx2 = msg.find('}', idx)
            dbw = int(msg[idx + len('DownBandWidth='):idx2])
        else:
            dbw = 0

        idx = msg.find('dbm=')
        if idx != -1 :
            idx2 = msg.find(',', idx)
            dbm = int(msg[idx + len('dbm='):idx2])
        else:
            dbm = 0
        
        idx = msg.find('Rsrq=')
        if idx != -1 :
            idx2 = msg.find(',', idx)
            Rsrq = int(msg[idx + len('Rsrq='):idx2])
        else:
            Rsrq = 0

        band = getarray(msg, 'BandWidth=[')
        pack = getarray(msg, 'PacketLoss=[')
        delay = getarray(msg, 'Delay=[')
        jitter = getarray(msg, 'Jitter=[')
        jitter.append(0) # jitter补充最后一位

        idx = msg.find('serviceip=')
        if idx != -1 :
            idx2 = msg.find(',', idx)
            serviceip = msg[idx + len('serviceip='):idx2]
        else:
            serviceip = ''
        
        return req, ubw, dbw, dbm, Rsrq, band, pack, delay, jitter, serviceip

# 解析终端发送的网络数组数据，和上面那个函数可以放在同一个class里 比如util
def getarray(str, aim):
    ans = []
    idx = str.find(aim) + len(aim)
    if idx != -1:
        idx2 = str.find(']', idx)
        while idx < idx2:
            tidx = str.find(',', idx)
            if tidx == -1 or tidx > idx2:
                tidx = idx2
            ans.append(float(str[idx:tidx]))
            idx = tidx + 1
    return ans

# 将intlist转化为字符串的函数
def iListTStr(l):
    lstr = [str(x) for x in l]
    return ', '.join(lstr)


# 将存储网络状态or Qoe的list更新
def updatelist(listlast, listnew, maxlen):
    listlast = listlast + listnew
    # if len(listlast) > maxlen:
    #     listlast = listlast[len(listlast) - maxlen:]
    return listlast

# times合并为1s
def average(listt, l):
    res = []
    
    i = len(listt)
    while i > 0:
        if(i >= l):
            res.append(sum(listt[len(listt)-i:len(listt)-i+l])/l)
            i -= l
        else:
            res.append(sum(listt[len(listt)-i:])/i)
            i = 0
    return res

# 去掉0
def movezero(list):
    res = []
    for i in list:
        if i != 0:
            res.append(i)
    return res