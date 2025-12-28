
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

class Is_Not_Init(py_trees.behaviour.Behaviour):

    def __init__(self,  name="开始游戏"):
        super(Is_Not_Init, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="init_dll", access=py_trees.common.Access.READ)#READ
        self.time = 0
    def update(self) -> py_trees.common.Status:
        if not self.blackboard.init_dll and arc_api.select_mode() !="2":
            print("正在初始化dll")
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE