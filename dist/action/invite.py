
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
from http_add_friend import add_friend_by_http # Use the correct function

arc_api = Arc_api()
client = ApiClient()

import queue
import multiprocessing
import random
import asyncio
from multiprocessing import Process, Queue, Manager, Lock
from http_add_friend import add_friend_by_http, add_friend_by_http_async, add_friend_by_id_async # Use the correct function

import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

def worker(token):
    """
    工作进程函数：持续查询并发送请求 (Async Version)
    每个进程独立计数，各自发送固定好友请求
    """
    # 在进程内部初始化 ApiClient
    local_client = ApiClient()
    
    print(f"进程启动: Token [...{token[-6:]}]")

    # 定义异步主循环
    async def async_worker_loop():
        local_count = 0
        loop = asyncio.get_running_loop()
        background_tasks = set()
        MAX_CONCURRENT_TASKS = 50  # 限制最大并发任务数
        
        while True:
            try:
                # 检查后台任务数量，如果太多则稍作等待
                if len(background_tasks) >= MAX_CONCURRENT_TASKS:
                    await asyncio.sleep(0.1)
                    continue

                # 1. 查询数据 (直接调用异步方法)
                status_code, response = await local_client.query_data_async("arc_game", 86400, 1, 10)
                
                friend_items = []
                if status_code == 200:
                    data = response.get("data", [])
                    if isinstance(data, list):
                        for item in data:
                            account = item.get("account")
                            if account:
                                friend_items.append(item)
                
                if not friend_items:
                    # 如果没查到数据，休眠一会再试
                    await asyncio.sleep(5)
                    await local_client.clear_talk_channel_async("arc_game", 1)
                    continue
                    
                # 2. 异步并发处理查询到的好友 (Fire-and-forget 模式)
                for item in friend_items:
                    account = item.get("account")
                    b_zone = item.get("b_zone")
                    
                    # 移除 sleep，因为我们现在控制并发总数而不是发完一批再发下一批
                    # await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    print(f"Token [...{token[-6:]}] 正在向好友 {account} 发送请求 (b_zone={b_zone})...")
                    
                    if b_zone and b_zone != "1":
                        task = asyncio.create_task(add_friend_by_id_async(str(b_zone), token))
                    else:
                        task = asyncio.create_task(add_friend_by_http_async(account, token))
                    
                    # 添加到后台任务集合，完成后自动移除
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)
                    
                    local_count += 1

                    # 检查是否需要发送固定好友
                    if local_count > 0 and local_count % 100 == 0:
                        print(f"Token [...{token[-6:]}] 本次运行已发送 {local_count} 次，正在发送固定好友: MMOEXPsellitem18#0342")
                        fixed_task = asyncio.create_task(add_friend_by_http_async("MMOEXPsellitem18#0342", token))
                        background_tasks.add(fixed_task)
                        fixed_task.add_done_callback(background_tasks.discard)

                # 不再等待 asyncio.gather，直接进入下一轮循环
                # await asyncio.gather(*tasks) 
                
            except Exception as e:
                print(f"Worker 进程异常: {e}")
                await asyncio.sleep(5)

    # 运行异步循环
    asyncio.run(async_worker_loop())

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
            return py_trees.common.Status.SUCCESS
            
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
