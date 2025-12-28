
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

# ... (imports)

# Removed static tokens definition
# tokens = [ ... ]

import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

def worker(token, task_queue):
    """
    工作进程函数：持续从队列获取账号并发送请求
    每个进程独立计数，各自发送固定好友请求
    """
    local_count = 0
    while True:
        try:
            # 非阻塞获取，如果队列空了就退出
            account = task_queue.get_nowait()
        except queue.Empty:
            break
            
        try:
            add_friend_by_http(account, token)
            local_count += 1
            
            # 各自计数，各自发送
            if local_count > 0 and local_count % 100 == 0:
                print(f"Token [...{token[-6:]}] 本次运行已发送 {local_count} 次，正在发送固定好友: MMOEXPsellitem18#0342")
                try:
                    add_friend_by_http("MMOEXPsellitem18#0342", token)
                except Exception as e:
                    print(f"固定好友发送失败: {e}")
                
        except Exception as e:
            print(f"Token 处理异常: {e}")

class Invite(py_trees.behaviour.Behaviour):

    def __init__(self,  name="加好友"):
        super(Invite, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.WRITE)#READ
        self.time = 0
        self.create_number = 0
        self.count = 0
        
    def update(self) -> py_trees.common.Status:
        if arc_api.select_mode() !="2" :
            print("收集id")
            return py_trees.common.Status.FAILURE
            
        # 每次 update 都重新读取 Token，支持运行时修改配置文件
        tokens = arc_api.get_tokens()
        if not tokens:
            print("未找到有效 Token，请检查 select_mode.txt")
            time.sleep(5)
            return py_trees.common.Status.RUNNING

        status_code, response = client.query_data("arc_game", 86400, 1, 10)
        if status_code != 200:
            print("查询游戏数据失败")
            return py_trees.common.Status.RUNNING
        data = response.get("data", [])
        names = []
        if isinstance(data, list):
            for item in data:
                account = item.get("account")
                if account:
                    names.append(account)
        self.count = 0
        
        if not names:
            return py_trees.common.Status.RUNNING

        print(f"开始处理 {len(names)} 个好友请求，使用 {len(tokens)} 个 Token 并发处理...")
        
        # 使用多进程队列管理任务
        task_queue = multiprocessing.Queue()
        for name in names:
            task_queue.put(name)
            
        # 为每个 Token 启动一个进程
        processes = []
        for token in tokens:
            # 各自计数，不需要共享变量
            p = multiprocessing.Process(target=worker, args=(token, task_queue))
            p.daemon = True
            p.start()
            processes.append(p)
            
        # 等待所有进程完成
        for p in processes:
            p.join()

        names.clear()
        return py_trees.common.Status.RUNNING
