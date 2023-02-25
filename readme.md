### 1.py文件：  
 **对应拓扑图的两个主要运行文件**：

sli_fine.py是细粒度切片策略服务器，目前正在写在用的一版  
service.py与service_tcp.py是模拟渲染服务器（按帧传输视频文件），tcp方式


**各模块文件**  
ARMA_forecast.py 预测带宽模块  
QoEcal.py 网络间接qoe计算模块
sliUtil.py是解析报文，列表字符串转换等的封装  
pltres.py是将QoE可视化的文件


**强化学习策略尝试**  
MLtrainsli.py是对接强化学习训练时的策略服务器
testMLtrainsli.py是其使用测试示例

train.py是训练代码
agent.py, algorithm.py, env.py, RL_v1.py, replay_memory.py, model.py, net_qoe.py是强化学习的代理、算法、环境、强化学习、经验重放、神经网络模型、网络环境qoe计算等强化学习相应步骤的实现模块。  

### 2.sh文件：
sh开头的脚本是切片相关部署命令，参数要求见对应文件  
切片操作目前有两种  
一种是直接分四大类切片，大类设置好优先级和带宽，而后对用户进行分类装箱  
另一种（细粒度操作）是对每个用户创建class和filter设置其优先级和带宽  

工具：show.sh 展示traffic control的class分类和filter过滤器设置  

init_tc.sh是traffic control工具初始化  
init_tc_old.sh是将xxxMbit带宽资源全部考虑的初始化。
slice.sh是切片操作  
delFilter.sh删除filter分类器  

以上三个sh的fine_开头(fine_init_tc.sh, fine_slice.sh，fine_delFilter.sh)代表细粒度操作。  
fine_change.sh修改细粒度下为用户的class修改并对修改后的创建新filter  
 细粒度的初始化工具

### 3.文件夹：
data是跑出来的历史数据  
video是传输的音视频文件  
test是三种策略py文件
算法输入输出形式是构想的训练数据形式，可以是qoe和需求，也可以实验包含时延抖动的具体数据。
