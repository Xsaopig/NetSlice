#参数1是优先级，参数2是用户ip，是删除用户切片分类器（filter）的脚本，参数2是用户连接端口
tc filter del dev ens33 protocol ip pref $1 u32 match ip dst $2 match ip dport $3 0xffff
#exp: ./delFilter.sh 1.0.0.1 1234