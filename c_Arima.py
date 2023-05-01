"""
ARIMA带宽预测 新版，集成参数选择和训练。
第一步：完成数据读取与格式转化
第二步：完成差分参数d的确认（通过平稳性检验来确定）
第三步：完成基于AIC/BIC/HQIC方法的p,q参数确认
第四步：训练。并可检验其效果（验证代码有效性时）
TODO:
出现问题：预测之后后几秒有效果，再远的话需要SARIMAX才好？考虑尝试

用户聚类问题
在此基础上，实现对用户聚类，即同类用户用一个模型预测。
聚类依据是用户需求的分类结果（这一阶段采用该方法）
实现需要：
1.基于所有用户的数据确认参数？（可行）（已完成）
不在子序列基础上进一步缩小时间段的话，分别为：
[(4, 0, 2), (4, 0, 3), (3, 0, 2), (1, 0, 1), (2, 0, 2), (3, 0, 4), (3, 0, 2)]
[(3, 0, 3), (1, 0, 1), (4, 0, 5), (3, 0, 3), (4, 0, 3), (1, 0, 1)]
2.基于所有用户展开训练？
问题：如何保存模型？（已完成）如何在已有的模型基础上再训练？（已验证无法实现）
TODO:
3.与用户聚类结合的选择参数
暂时是每个用户创建一个？
"""

import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller


class Arima(object):

    def __init__(self):
        self.res = None
        self.model = None
        self.p_max, self.q_max = (5, 5)
        self.p = 1
        self.d = 0
        self.q = 1

    # 差分直到阶数d确定
    def getd(self, data):
        bit = np.array(data)
        adf_result = adfuller(bit)  # 生成adf检验结果
        p_v = adf_result[1]
        while p_v > 0.05:
            bit = np.diff(bit)
            self.d += 1
            adf_res = adfuller(bit)
            p_v = adf_res[1]
        return bit.tolist()

    # 获取p, q参数
    def AICc(self, data):
        aicc_matrix = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for p in range(1, self.p_max):
                tmp = []
                for q in range(1, self.q_max):
                    tmp.append(ARIMA(data, order=(p, self.d, q)).fit().aicc)
                aicc_matrix.append(tmp)
            aicc_matrix = pd.DataFrame(aicc_matrix)
        p, q = aicc_matrix.stack().idxmin()  # 矩阵中从0开始对应实际值从1开始，所以要加一
        p += 1
        q += 1
        # print(u 'AICc最小p，q值：%s、%s' % (p, q))
        return p, q

    # # 绘制预测和原本的图
    # def plt_for(self, list1, list2, title):
    #     plt.figure(figsize=(7, 5), dpi=80)
    #     x1 = range(len(list1))
    #     x2 = range(len(list2))
    #     plt.plot(x1, list1, 'r-o', label='bit')
    #     plt.plot(x2, list2, 'b-o', label='forecast')
    #     plt.legend()  # 默认loc=Best
    #     plt.title(title, fontsize=16)
    #     plt.show()

    def train_pq(self, bitRate):  # 训练pq
        try:
            self.getd(bitRate)
            self.p, self.q = self.AICc(bitRate)
        except Exception as e:
            print('出现异常数据', e)

    def fit(self, bitRate, need_pq):  # 纯训练的代码
        """
        训练函数，成功创建res和model
        :param bitRate: 历史码率数据
        :param need_pq: 是否需要先pq定阶
        :return:
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if need_pq:
                self.train_pq(bitRate)
            self.model = ARIMA(bitRate, order=(self.p, self.d, self.q))
            self.res = self.model.fit()

    def forecast(self, bitRate=[], hasFit=0, need_pq=1, length=10):
        """
        集成了训练和预测的函数
        :param bitRate: 历史码率数据
        :param hasFit:  调用者认为该模型是否已经训练过 默认为0 需要训练。为1时会判断模型是否为none，是则还是训练
        :param need_pq: 是否需要运用AICc方法对p q定阶（不直接调用，传给fit决定）
        :param length:  预测区间长度
        :return: 长度为length的预测结果
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if hasFit:  # 已经用bitRate训练过了
                if self.model is not None:
                    fo = self.res.forecast(length)
                    return fo
            self.fit(bitRate, need_pq)  # 训练模型
            fo = self.res.forecast(length)  # 得到预测结果
            return fo

# [3.7666, 3.624, 3.7471, 3.5322, 3.7432, 3.3965, 3.7002, 3.7373, 3.7656, 3.4658, 3.3838, 3.7861, 3.7939, 3.5596,
# 3.3027, 3.8262, 3.5049, 3.3164, 3.2891, 3.3047]
# [30.6484, 30.6553, 30.8516, 30.9043, 30.5889, 28.835, 31.2266, 22.7822, 22.7051, 25.8936,
# 23.7285, 23.0674, 24.0527, 23.2451, 22.2324, 23.874, 23.4893, 23.2402, 22.8174, 27.7373]


# if __name__ == "__main__":
#     data = [2.3223, 2.4092, 2.4961, 2.498, 2.5244, 2.4639, 2.4189, 2.0049, 2.0342, 2.5449, 2.0811, 2.3672, 2.4141,
#             2.4629, 2.5439, 2.4238, 2.5635, 2.4746, 2.4512, 1.8369]
#     fo = Arima()
#     fo.fit(data, 1)
#     print(fo.p, fo.q)
#     print(fo.forecast(hasFit=1))
