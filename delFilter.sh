#!/bin/bash
#参数1是分类结果，2是用户ip，是删除用户切片分类器（filter）的脚本
if [ ${1} -eq 0 ];
then
    tc filter del dev ens33 protocol ip pref 6 u32 match ip dst ${2} flowid 1:40
elif [ ${1} -eq 1 ];
then
    tc filter del dev ens33 protocol ip pref 5 u32 match ip dst ${2} flowid 1:30
elif [ ${1} -eq 2 ];
then
    tc filter del dev ens33 protocol ip pref 4 u32 match ip dst ${2} flowid 1:20
elif [ ${1} -eq 3 ];
then 
    tc filter del dev ens33 protocol ip pref 3 u32 match ip dst ${2} flowid 1:10
fi

#exp: ./delFilter.sh 3 1.0.0.1