#!/bin/bash
# 需在root用户下运行
# 本实验中，对网卡建立四个子分类，对应四种切片，低时延需要高优先级，高带宽需要带宽分配。
# 对于分类，按其分类的编号顺序起作用，编号小的优先；一旦符合某个分类匹配规则，通过该分类发送数据包
# pri越小，优先级越高
tc qdisc del dev ens33 root  # 清空原有规则
tc qdisc add dev ens33 root handle 1: htb default 1
# 创建一个主分类绑定100Mbit带宽资源
tc class add dev ens33 parent 1:0 classid 1:1 htb rate 100Mbit

# 默认带宽22.5Mbit（服务器空闲时最大50），优先级2 代表moba型
# 默认带宽7.5Mbit（服务器空闲时最大25），优先级1 代表delay型
# 默认带宽5Mbit（服务器空闲时最大40），优先级4 代表bandwitdh型
# 默认带宽5Mbit（服务器空闲时最大15），优先级6 代表defalut型
tc class add dev ens33 parent 1:1 classid 1:10 htb prio 2 rate 45Mbit ceil 100Mbit 
tc class add dev ens33 parent 1:1 classid 1:20 htb prio 1 rate 15Mbit ceil 50Mbit
tc class add dev ens33 parent 1:1 classid 1:30 htb prio 4 rate 30Mbit ceil 80Mbit  
tc class add dev ens33 parent 1:1 classid 1:40 htb prio 6 rate 10Mbit ceil 40Mbit 

# 全面初始化为默认类型
tc filter add dev ens33 protocol ip parent 1:0 prio 7 u32 match ip dst 0.0.0.0/0 flowid 1:40



