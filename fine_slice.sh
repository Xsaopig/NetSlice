# 在大类基础上为每个用户定制的细粒度切片脚本
# 输入参数：${1}代表分配的flowid,从3开始，${2}代表优先级等级，为2或6(2优先)
# ${3}代表分配带宽的字符串，${4}代表ip地址
tc class add dev ens33 parent 1:1 classid 1:$1 htb prio $2 rate $3Mbit
tc filter add dev ens33 protocol ip parent 1:0 prio $2 u32 match ip dst $4 match ip dport $5 0xffff flowid 1:$1
# 上一行的${1}是filter中的优先级，由于删除时prio作为删除的唯一标示，只能和id同理才好删。
# 同时，由于一个ip只会匹配一个filter，因此这里的优先级大小不重要。