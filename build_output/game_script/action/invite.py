
from http.client import responses
import sys
import os
import token
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))  # 添加上一级目录
from threading import local
import time 
import py_trees
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from arcapi import Arc_api, dm
from api_client import ApiClient
# from http_friend_manager import HttpFriendManager # Removed incorrect import
from http_add_friend import add_friend_by_http # Use the correct function

arc_api = Arc_api()
client = ApiClient()

import queue
import multiprocessing
from multiprocessing import Process, Queue, Manager, Lock

import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

def worker(token):
    """
    工作进程函数：持续查询并发送请求
    每个进程独立计数，各自发送固定好友请求
    """
    # 在进程内部初始化 ApiClient
    local_client = ApiClient()
    local_count = 0
    
    print(f"进程启动: Token [...{token[-6:]}]")
    
    while True:
        try:
            # 1. 查询数据
            status_code, response = local_client.query_data("arc_game", 86400, 1, 10)
            
            names = []
            if status_code == 200:
                data = response.get("data", [])
                if isinstance(data, list):
                    for item in data:
                        account = item.get("account")
                        if account:
                            names.append(account)
            
            if not names:
                # 如果没查到数据，休眠一会再试，避免频繁请求
                time.sleep(5)
                continue
                
            # 2. 处理查询到的好友
            for account in names:
                try:
                    time1=time.time()
                    add_friend_by_http(account, token)
                    print("add_friend_by_http时间",time.time()-time1)
                    local_count += 1
                    
                    # 各自计数，各自发送固定好友
                    if local_count > 0 and local_count % 10 == 0:
                        print(f"Token [...{token[-6:]}] 本次运行已发送 {local_count} 次，正在发送固定好友: MMOEXPsellitem18#0342")
                        try:
                            add_friend_by_http("MMOEXPsellitem18#0342", token)
                        except Exception as e:
                            print(f"固定好友发送失败: {e}")
                            
                except Exception as e:
                    print(f"Token 处理异常: {e}")
            
        except Exception as e:
            print(f"Worker 进程异常: {e}")
            time.sleep(5)

class Invite(py_trees.behaviour.Behaviour):

    def __init__(self,  name="加好友"):
        super(Invite, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.WRITE)#READ
        self.time = 0
        self.create_number = 0
        self.count = 0
        self.time1 =0
        self.processes = {}
        
    def update(self) -> py_trees.common.Status:
        self.time1 = time.time()
        if arc_api.select_mode() !="2" :
            print("收集id")
            return py_trees.common.Status.FAILURE
            
        # 每次 update 都重新读取 Token，支持运行时修改配置文件
        tokens = arc_api.get_tokens()
        if not tokens:
            print("未找到有效 Token，请检查 select_mode.txt")
            time.sleep(5)
            return py_trees.common.Status.RUNNING

        # 维护进程状态
        current_tokens = set(tokens)
        active_tokens = set(self.processes.keys())

        # 清理失效Token的进程
        for token in active_tokens - current_tokens:
            p = self.processes.pop(token)
            if p.is_alive():
                p.terminate()

        # 启动或重启进程
        for token in tokens:
            if token not in self.processes or not self.processes[token].is_alive():
                # 不再传递 task_queue，进程内部自己管理
                p = multiprocessing.Process(target=worker, args=(token,))
                p.daemon = True
                p.start()
                self.processes[token] = p

        # 主线程不再负责查询和分发任务，只负责维护进程
        return py_trees.common.Status.RUNNING
