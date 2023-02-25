import gym
from gym import spaces
import numpy as np
import random
import time
from threading import Thread

import time
from threading import Thread
import sys
import os
import MLtrainsli

MAX_BANDWIDTH = 100
user_num = 5
TOTAL_BANDWIDTH = MAX_BANDWIDTH
OCCUPIED_BANDWIDTH = 0
PRIORITY1_BANDWIDTH = 0
PRIORITY2_BANDWIDTH = 0
reward_extra = 0.1


class MyEnv(gym.Env):

    def __init__(self, users):
        super().__init__()
        self.users = users
        # self.reward_range = (0, MAX_ACCOUNT_BALANCE)
        # 定义动作和观测空间, 两者必须为 gym.spaces 对象
        self.user_num = user_num
        self.total_bandwidth = TOTAL_BANDWIDTH
        self.occupied_bandwidth = 0
        self.priority1_bandwidth = 0
        self.priority2_bandwidth = 0
        # 动作的格式为: priority+bandwise
        self.action_space = self._get_action_space()
        self.observation_space = self._get_observation_space()
        self.current_step = 0

    def _get_observation_space(self):
        # [user_type,user_qoe, predict_bandwise,
        # total_bandwise,occupied_bandwise
        # [priority1,priority1_bandwise],[priority2,priority2_bandwise]]
        high_arr = np.zeros((user_num + 1, 3))
        for user in range(user_num):
            high_arr[user] = [10, 5, MAX_BANDWIDTH]
        high_arr[user_num] = [MAX_BANDWIDTH, MAX_BANDWIDTH, MAX_BANDWIDTH]
        return spaces.Box(low=np.zeros((user_num + 1, 3), dtype='float32').flatten()
                          , high=high_arr.flatten())

    def _get_action_space(self):
        return spaces.Box(low=np.array([0, 0]), high=np.array([2, MAX_BANDWIDTH]))

    def reset(self):
        # 重置环境的状态到初始状态
        self.user_num = user_num
        self.total_bandwidth = TOTAL_BANDWIDTH
        self.occupied_bandwidth = random.uniform(0, self.total_bandwidth)
        self.priority1_bandwidth = random.uniform(0, self.occupied_bandwidth)
        self.priority2_bandwidth = self.occupied_bandwidth - self.priority1_bandwidth

        # 设置当前 step 到一个随机点
        self.current_step = random.randint(
            0, user_num)

        return self._next_observation()

    def _next_observation(self):
        frame = np.zeros((5, 3), dtype='float32')
        # 获取最后五天的数据点, 并归一
        for user in range(user_num):
            if user < self.current_step:
                frame[user] = [self.users[user][0], 0, 0]
            else:
                frame[user] = [self.users[user][0], (self.users[user][1]) / 5, (self.users[user][2]) / MAX_BANDWIDTH]

        # 添加额外的信息, 归一
        obs = np.append(frame, [[
            self.occupied_bandwidth / MAX_BANDWIDTH,
            self.priority1_bandwidth / MAX_BANDWIDTH,
            self.priority2_bandwidth / MAX_BANDWIDTH,
        ]], axis=0)
        obs = obs.flatten()
        return obs

    def step(self, action):
        # 在环境中执行一步
        self._take_action(action)
        # reward
        reward = 0
        current_num = 0
        for user in range(user_num):
            if self.users[user][0] != -1:
                current_num += 1
        for user in range(current_num):
            if self.current_step >= user:
                reward += self.users[user][1] * (1 + reward_extra)  # 对于已经分配过的用户qoe进行一个额外的奖励来让策略更加兼顾全局最优
            else:
                reward += self.users[user][1]
        reward /= current_num
        # updata step
        self.current_step += 1
        done = (self.current_step >= current_num)
        if self.current_step >= current_num:
            self.current_step = 0
        obs = self._next_observation()

        # {} 是要打印的信息
        return obs, reward, done, {}

    def _take_action(self, action):
        action_type = action[0]
        amount = action[1]
        if amount > self.total_bandwidth - self.occupied_bandwidth:
            amount = self.total_bandwidth - self.occupied_bandwidth

        if action_type < 1:
            # allocated to priority1
            self.occupied_bandwidth += amount
            self.priority1_bandwidth += amount

        elif action_type < 2:
            # allocated to priority2
            self.occupied_bandwidth += amount
            self.priority2_bandwidth += amount
        # 调用
        current_state = self._compute_state(self.current_step, action)
        current_state = np.append(current_state,[[self.occupied_bandwidth, self.priority1_bandwidth, self.priority1_bandwidth]],axis=0)
        self.users = np.array(current_state)

    def _compute_state(self, current_step, action):
        # 从服务器中获取数据
        # sli = MLtrainsli.finsli()
        # Thread(target=sli.startlisten).start()
        # print('成功运行切片策略服务器,等待qoe中')
        #
        # time.sleep(25)  # 初始化策略服务器后要给时间让终端接入并发送切片请求，不然部署下去key是不存在的error。（我做个捕获吧）
        # if action[0] < 1:
        #     action_type = 2
        # elif action[0] <= 2:
        #     action_type = 6
        # print('获取action执行后的state,current_step: '+str(current_step)+' action_type '+str(action_type)+' action[1] '+str(action[1]))
        # res1 = sli.doAct_GetQoe(current_step+1, [action_type, action[1]])
        # print('--------------------------------------')
        # print('res:', res1)
        # res1 = np.array(res1)
        res1 = np.array([[3, 3.538131651797458, 22.268181818181816]])
        for user in range(user_num):
            if user >= res1.shape[0]:
                res1 = np.append(res1, [[-1, 5, 0]], axis=0)
        return res1


class test1():
    print('--------')


def main():
    users = np.array([[1, 4, 10],
                      [2, 3.7, 20],
                      [3, 3, 30],
                      [4, 2, 40],
                      [5, 1, 50],
                      ])
    users = np.append(users, [[0, 0, 0]], axis=0)
    env = MyEnv(users)
    a = [1, 10]
    s_prime, r, done, info = env.step(a)
    print(a)
    print(s_prime)
    print(r)
    print(done)


if __name__ == '__main__':
    main()
