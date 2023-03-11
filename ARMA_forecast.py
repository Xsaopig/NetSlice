"""
    输入 一个OD对的流量时序
    输出：下一个时刻该业务的流量
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import sys, getopt

# data是历史带宽数据，length是预测未来时间长度
def forecast(data, length): 
    # print('-'*20, 'IGNORE THIS WARNING', '-'*20)
    data = [round(x/1024, 4) for x in data] # 转换为保留4位的Mbit 输入应该是Kbps！
    if len(data) == 0:
        data = [3.1, 3.2, 3.1, 3.2, 3.1, 3.2, 3.4, 3.5, 3.2, 3.3]
        length = len(data) - 1
    data_d = np.diff(data)
    time_series = pd.Series(data_d)
    # model = ARMA(time_series, (0, 1)).fit() #这个模型好像已经用不了了
    model = ARIMA(endog=time_series,order=(0,1,1)).fit()

    answer = model.forecast(length)
    result = data[-length:-1]
    mean = answer.mean()
    result = [val+mean for val in result]
    # print('-'*20, 'IGNORE THIS WARNING', '-'*20)
    # print('Forecast result:', result)
    result = [round(x, 1) for x in result] # 转换为保留1位的Mbit
    return result

    # TM[i][j] = last_TM[i][j] + result


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "i:o:t:D")
    DEBUG = False
    input_file = "input.txt"
    output_file = "output.txt"
    input_str = ""
    for op, value in opts:
        if op == "-i":
            input_file = value
        elif op == "-o":
            output_file = value
        elif op == "-t":
            input_str = value
        elif op == "-D":
            DEBUG = True
    data = []#输入是Kbps
    if input_str == "":
        with open(input_file,"r") as fp:
            data = fp.readlines()
            fp.close()
        data=[float(str) for str in data]
    else:
        data = [float(str) for str in input_str.split(',')]

    result = forecast(data,len(data)-1)#输出是Mbit
    with open(output_file,"w") as fp:
        fp.writelines([str(val) for val in result])
        fp.close()

    if DEBUG: 
        print(sys.argv)
        print(data)
        print(result)


    



