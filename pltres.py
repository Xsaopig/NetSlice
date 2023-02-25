'''
画图工具。
功能要求：
（1）显示整个系统的QoE变化情况
（2）显示每个用户的QoE变化情况
（3）显示每个用户带宽、时延抖动，丢包率的变化情况
（4）显示该用户的预测带宽和实际带宽
（5）显示用户各个指标的合格率变化情况

设计思路：
读取sli_fine中存储的以下数据：
（1）各个用户的网络质量矩阵
（2）用户QoE计算结果和总QoE计算结果
（3）用户预测带宽
'''
import matplotlib
import matplotlib.pyplot as plt

# plt.rcParams['font.sans-serif'] = ['SimHei'] #显示中文
# plt.rcParams['font.family'] = 'sans-serif'  # ubuntu按网上教程也没配好中文，暂时搁置
plt.rcParams['axes.unicode_minus'] = False
'''
将list可视化的函数
参数：
list（内容作为y的点）
xlabel 字符串 x轴名称，ylabel 字符串 y轴名称，title 字符串 图片名称。

'''
def initfig():
    plt.figure(figsize=(7,5), dpi=80 )

def pltlist(list, xlabel, ylabel, title):
    x = range(len(list))
    plt.plot(x, list, 'r-o') 
    plt.xlabel(xlabel ,fontsize=16)
    plt.ylabel(ylabel, fontsize=16)
    plt.title(title, fontsize=16)


# 画一条x=a的线，标签为lb
def pltylin(a, lb):
    plt.axvline(a, label=lb)


# 保存文件的函数，参数：isshow是否展示图片
def finish(fgname):
    plt.savefig(f'./res/{fgname}.png')

if __name__ == "__main__":
    print(matplotlib.get_cachedir())
    print(matplotlib.matplotlib_fname())