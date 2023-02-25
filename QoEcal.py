import math
from tokenize import Double
import numpy as np
import sliceUtil as sutil
DEBUG = 1 # 忽视时延抖动丢包的情况
# 判断带宽的网络质量。基于腾讯先锋云游戏提供的720p30fps和1080p60fps提供两种带宽需求
def getBandMos(b, req):
    c = -0.00125
    bd = 2000
    if req == 1 or req == 3:
        c = -0.0003 # -0.0004
        bd = 22000 # 26500
    return 5/(1+np.exp(c * (b-bd)))

# 基于论文Video stream QoE estimation model in IP network
# 考虑云游戏和音视频应用场景不同，引入时延，并调高参数b(0.012->0.015)
# 定位指标：100ms时延 15ms抖动 4.33左右。丢包不超过3%。
# 50ms时延15ms抖动，4.5左右（非常满意）
def getMoS(d, j, pl): 
    a = 4.995
    b = 0.008
    c = 0.231
    return a - b * (1.8 * j + d) - c * pl

# 基于带宽和时延抖动的MoS进行QoE判断。req不同权重也不一样。结果值在[0,5]之间
def MosToQoE(bqoe, djpqoe, req):
    if djpqoe < 2.5:# 高要求对时延抖动等体验进行准确评价。带宽可能与实时需要传输内容相关，不应该作为太高比例的判断基准。
        return 0
    elif djpqoe < 3 and (req == 2 or req == 3): 
        return 0
    if DEBUG:
        return bqoe
    if req == 0 or req == 3:
        return 1/3 * bqoe + 2/3 * djpqoe
    elif req == 1:
        return 1/2 * bqoe + 1/2 * djpqoe
    elif req == 2:
        return 1/4 * bqoe + 3/4 * djpqoe

'''
返回reslist，对应这10s内每一秒的qoe
实验中的丢包率p因为每秒只用一个包测，因此先只用每秒的当前120s丢包率统计值。
真实环境中接入的再说。那个应该就可以1s很多包，统计的丢包率真实可信
计算方法待改进
'''
def get_QoE(bandwidth,  delay,  jitter,  p, req):
    # print(bandwidth, delay, jitter)
    p = p[0] # 如果丢包率测量的好有大量包发送，每秒均有一定变化的话，则不用只读p[0]
    reslist = []
    length = min(len(bandwidth), len(delay), len(jitter))
    for i in range (length):
        reslist.append(MosToQoE(getBandMos(bandwidth[i], req), getMoS(delay[i], jitter[i], p), req))
    return reslist

    # if np.mean(delay) == 0 and np.mean(jitter) == 0: # 本地测试时会出现的
    #     t = math.exp(k4/5.0 * p) * 0.1 # 现在的k4/5是因为本地测试暂时没统计那么久的丢包率，不够稳定。
    #     for i in range(len(bandwidth)):
    #         reslist.append(f1b(bandwidth[i])/t)
    # else:
    #     for i in range(len(bandwidth)):
    #         reslist.append(f1b(bandwidth[i], k1, k5) / ((f2d(delay[i], k2) + f3j(jitter[i], k3)) * math.exp(k4/5.0 * p)) )
        

# qoe归一化，为了让各个需求类型的请求影响权重差不多
# 参数是带入下面注释中的几组网络质量得到的'满足'和'不合格'网络质量
    # if req == 0 or req == 3:
    #     if res < 0.0307567:
    #         res = 60 * (res/0.0307567)
    #     else:
    #         res = 60 + 40 * (res - 0.0307567) / (3.248 - 0.0307567)
    # if req == 1:
    #     if res < 0.0615134:
    #         res = 60 * (res/0.0615134)
    #     else:
    #         res = 60 + 40 * (res - 0.0615134) / (6.496 - 0.0615134)
    # if req == 2:
    #     if res < 0.002097167:
    #         res = 60 * (res / 0.0020971669)
    #     else:
    #         res = 60 + 40 * (res - 0.0020971669)/(0.27049798324 - 0.0020971669)
    # print(f'In QoE: res is{res}')
# 3.247969238516893
# 6.495938477033786
# 0.270497983239
# print(get_QoE(3000, 50, 16, 1, 0)) 
# print(get_QoE(3000, 50, 16, 1, 1)) 
# print(get_QoE(3000, 50, 16, 1, 2))
# print(get_QoE(3000, 50, 16, 1, 3))
# # 0.030756702374289777
# # 0.06151340474857955
# # 0.0020971669
# print(get_QoE(1250, 100, 32, 1.5, 0)) 
# print(get_QoE(1250, 100, 32, 1.5, 1))
# print(get_QoE(1250, 100, 32, 1.5, 2))
# print(get_QoE(1250, 100, 32, 1.5, 3))