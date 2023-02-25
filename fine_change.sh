# 对应修改类的优先级和带宽，并新建filter，需要先调用delFilter.sh（注：类修改不能修改祖先，只能改带宽）
# 输入参数：$1代表分类等级，$2代表修改的flowid,格式为xxxx，不能和10 20 30 40重合;$3代表分配带宽的字符串，$4代表ip地址
if [ $1 -eq 0 ];
then
    tc class change dev ens33 classid 1:$2 htb prio 6 rate $3Mbit
    tc filter add dev ens33 protocol ip parent 1:0 prio 6 u32 match ip dst $4 flowid 1:$2
elif [ $1 -eq 1 ];
then
    tc class change dev ens33 classid 1:$2 htb prio 4 rate $3Mbit
    tc filter add dev ens33 protocol ip parent 1:0 prio 5 u32 match ip dst $4 flowid 1:$2
elif [ $1 -eq 2 ];
then
    tc class change dev ens33 classid 1:$2 htb prio 1 rate $3Mbit
    tc filter add dev ens33 protocol ip parent 1:0 prio 4 u32 match ip dst $4 flowid 1:$2
elif [ $1 -eq 3 ];
then 
    tc class change dev ens33 classid 1:$2 htb prio 2 rate $3Mbit
    tc filter add dev ens33 protocol ip parent 1:0 prio 3 u32 match ip dst $4 flowid 1:$2
fi
#exp:./fine_change.sh 2 11 10 1.0.0.1