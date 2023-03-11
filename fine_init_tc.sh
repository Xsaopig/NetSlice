# 需在root用户下运行
# 本实验中，对网卡建立四个子分类，对应四种切片，低时延需要高优先级，高带宽需要带宽分配。
# 对于分类，按其分类的编号顺序起作用，编号小的优先；一旦符合某个分类匹配规则，通过该分类发送数据包
# pri越小，优先级越高
# 清空原有规则
tc qdisc del dev ens33 root

tc qdisc add dev ens33 root handle 1: htb default 1

# 创建一个主分类绑定所有带宽资源
tc class add dev ens33 parent 1:0 classid 1:1 htb rate $1Mbit ceil $1Mbit

# 全面初始化为默认类型
tc filter add dev ens33 protocol ip parent 1:0 prio 7 u32 match ip dst 0.0.0.0/0 flowid 1:2
