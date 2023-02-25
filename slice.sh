#!/bin/bash
#参数1是分类结果，2是用户ip，是给用户切片的脚本
if [ ${1} -eq 0 ];
then
     tc filter add dev ens33 protocol ip parent 1:0 prio 6 u32 match ip dst ${2} flowid 1:40
elif [ ${1} -eq 1 ];
then
    tc filter add dev ens33 protocol ip parent 1:0 prio 5 u32 match ip dst ${2} flowid 1:30
elif [ ${1} -eq 2 ];
then
    tc filter add dev ens33 protocol ip parent 1:0 prio 4 u32 match ip dst ${2} flowid 1:20
elif [ ${1} -eq 3 ];
then 
    tc filter add dev ens33 protocol ip parent 1:0 prio 3 u32 match ip dst ${2} flowid 1:10
fi
