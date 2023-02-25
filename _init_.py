import os
import sys

sys.path.append(os.getcwd())
print(os.path)
from ddpg import net_qoe
print(net_qoe.test1())