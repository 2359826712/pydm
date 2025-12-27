
from re import A
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))  # 添加上一级目录
from threading import local
import time 
import py_trees
import time
from arcapi import Arc_api, dm
from api_client import ApiClient
from game_manager import ArcGameManager
arc_api = Arc_api()
client = ApiClient()
game_manager = ArcGameManager()


import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

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
        time.sleep(0.5)
        self.count = 0
        for account in names:
            if '#' in account:
                parts = account.split('#')
                if len(parts) >= 2:
                    name = parts[0] 
                    friend_id = parts[1]
                    game_manager.add_friend(name, friend_id)
                    time.sleep(0.1)
                    
                    # 计数器递增
                    self.count += 1
                    # 每1000次插入一次固定好友
                    if self.count % 10 == 0:
                        print("已添加1000次，插入固定好友: MMOELD.COM_items#8311")
                        game_manager.add_friend("MMOEXPsellitem18", "0342")
                        time.sleep(0.2)
        names.clear()
        return py_trees.common.Status.RUNNING
