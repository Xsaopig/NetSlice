# 测试MLtrainsli.py
import MLtrainsli
import time
from threading import Thread

sli = MLtrainsli.finsli()
Thread(target=sli.startlisten).start()
print('成功运行切片策略服务器,等待qoe中')

time.sleep(25) # 初始化策略服务器后要给时间让终端接入并发送切片请求，不然部署下去key是不存在的error。（我做个捕获吧）
res1 = sli.doAct_GetQoe(1,[2, 30])
print('--------------------------------------')
print('res:' , res1)