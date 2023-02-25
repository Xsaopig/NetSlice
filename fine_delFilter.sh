#参数1是flowid，2是用户ip，是删除用户切片分类器（filter）的脚本
tc filter del dev ens33 protocol ip pref $1 u32 match ip dst $2
#exp: ./delFilter.sh 3 1.0.0.1