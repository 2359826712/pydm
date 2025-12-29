import sys
import os
import py_trees
import time
from arcapi import Arc_api
from api_client import ApiClient
import multiprocessing
import asyncio
import aiohttp
from http_add_friend import add_friend_by_http_async, add_friend_by_id_async, get_stats
import logging

# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))  # 添加上一级目录

arc_api = Arc_api()

def worker(token, talk_channel, claimed_map, claimed_lock, use_sync):
    """
    工作进程函数：持续查询并发送请求 (Async Version)
    每个进程独立计数，各自发送固定好友请求
    """
    # 在进程内部初始化 ApiClient
    local_client = ApiClient()
    
    print(f"进程启动: Token [...{token[-6:]}]")

    # 定义异步主循环
    async def async_worker_loop():
        pid = os.getpid()
        local_count = 0
        loop = asyncio.get_running_loop()
        background_tasks = set()
        bd_round = 1
        friend_items_num = 0
        # 包装任务以捕获异常
        async def run_add_task(coro):
            try:
                await coro
            except Exception as e:
                print(f"Task error: {e}")

        # 配置连接池和超时
        # limit: 同时存在的最大连接数
        # limit_per_host: 同一个 host 的最大连接数 (避免触发防火墙)
        # ttl_dns_cache: DNS 缓存时间
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10, ttl_dns_cache=300)
        timeout = aiohttp.ClientTimeout(total=60, connect=20)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            while True:
                try:
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
                        bd_round+=1
                        await asyncio.sleep(5)
                        await local_client.clear_talk_channel_async("arc_game", 1)
                        if use_sync:
                            with claimed_lock:
                                claimed_map.clear()
                        friend_items_num = 0
                        continue
                    
                    friend_items_num = len(friend_items)+friend_items_num
                    success, blocked = get_stats()
                    print(f"进程id{pid} | 第{talk_channel}个Token | 已进行{bd_round}轮，已发送{local_count}次，正在进行添加{friend_items_num}个好友，成功{success}个，被拉黑{blocked}个")
                    # 2. 异步并发处理查询到的好友
                    current_batch_tasks = []
                    for item in friend_items:
                        account = item.get("account")
                        b_zone = item.get("b_zone")
                        
                        task_coro = None
                        if b_zone and b_zone != "1":
                            key = f"id:{b_zone}"
                            # 跨进程去重 (仅在模式3启用)
                            if use_sync:
                                with claimed_lock:
                                    if key in claimed_map:
                                        continue
                                    claimed_map[key] = pid
                            task_coro = add_friend_by_id_async(str(b_zone), token, session)
                        else:
                            key = f"acct:{account}"
                            # 跨进程去重 (仅在模式3启用)
                            if use_sync:
                                with claimed_lock:
                                    if key in claimed_map:
                                        continue
                                    claimed_map[key] = pid
                            task_coro = add_friend_by_http_async(account, token, session)
                        
                        # 使用包装器创建任务
                        task = asyncio.create_task(run_add_task(task_coro))
                        current_batch_tasks.append(task)
                        
                        # 添加到后台任务集合 (为了防止被 GC，虽然等待它们完成，但保留引用是个好习惯)
                        background_tasks.add(task)
                        task.add_done_callback(background_tasks.discard)
                        
                        # 降低循环速度减少请求超时，每次添加好友间隔 0.2 秒
                        await asyncio.sleep(0.2)
                        
                        local_count += 1

                        # 检查是否需要发送固定好友
                        if local_count > 0 and local_count % 100 == 0:
                            # print(f"Token [...{token[-6:]}] 本次运行已发送 {local_count} 次，正在发送固定好友: MMOEXPsellitem18#0342")
                            fixed_coro = add_friend_by_http_async("MMOEXPsellitem18#0342", token, session)
                            fixed_task = asyncio.create_task(run_add_task(fixed_coro))
                            background_tasks.add(fixed_task)
                            fixed_task.add_done_callback(background_tasks.discard)
                            current_batch_tasks.append(fixed_task)
                    
                    # 等待本批次所有任务完成
                    if current_batch_tasks:
                        await asyncio.gather(*current_batch_tasks)
                    
                    

                except Exception as e:
                    print(f"Worker 进程异常: {e}")
                    await asyncio.sleep(5)

    # 运行异步循环
    asyncio.run(async_worker_loop())

class Invite(py_trees.behaviour.Behaviour):

    def __init__(self,  name="加好友"):
        super(Invite, self).__init__(name)
        self.processes = {}
        # 跨进程共享的已领取键集合（用 dict 模拟 set）
        self.manager = multiprocessing.Manager()
        self.claimed_map = self.manager.dict()
        self.claimed_lock = self.manager.Lock()
        
    def update(self) -> py_trees.common.Status:
        mode = arc_api.select_mode()
        if mode not in ["2", "3"]:
            return py_trees.common.Status.SUCCESS
            
        # 每次 update 都重新读取 Token，支持运行时修改配置文件
        tokens = arc_api.get_tokens()
        tokens = [t.strip() for t in tokens if t and t.strip()]
        _seen = set()
        _unique_tokens = []
        for _t in tokens:
            if _t not in _seen:
                _seen.add(_t)
                _unique_tokens.append(_t)
        tokens = _unique_tokens
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
        for idx, token in enumerate(tokens):
            channel = (idx % 6) + 1
            use_sync = (mode == "3")
            if token not in self.processes:
                p = multiprocessing.Process(target=worker, args=(token, channel, self.claimed_map, self.claimed_lock, use_sync))
                p.daemon = True
                p.start()
                self.processes[token] = p
            else:
                p = self.processes[token]
                # 仅当进程已结束（exitcode 不为 None）时才重启，避免刚启动时 is_alive() 为 False 的竞态
                if not p.is_alive() and p.exitcode is not None:
                    p = multiprocessing.Process(target=worker, args=(token, channel, self.claimed_map, self.claimed_lock, use_sync))
                    p.daemon = True
                    p.start()
                    self.processes[token] = p

        # 主线程不再负责查询和分发任务，只负责维护进程
        return py_trees.common.Status.RUNNING
