
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

class Collect(py_trees.behaviour.Behaviour):

    def __init__(self,  name="收集好友id"):
        super(Collect, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="create_collect", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="create_collect", access=py_trees.common.Access.WRITE)#READ
        self.time = 0
    def update(self) -> py_trees.common.Status:
        self.blackboard.in_game = False
        pos = arc_api.FindColorE(26,787,266,869,"54c8e9-000000|ffffff-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[1]) > 0:
            print("在游戏中")
            time.sleep(0.5)
            self.blackboard.need_collect = False
            self.blackboard.in_game = True
            time.sleep(1)
            return py_trees.common.Status.RUNNING
        continue_pos_pic = arc_api.FindPic(1480,875,1541,911,"continue.bmp","000000",1.0,0)
        if int(continue_pos_pic[1]) > 0:
            time.sleep(0.5)
            print("点击继续")
            arc_api.mouse_click(1501,860,0)
            return py_trees.common.Status.RUNNING
        continue_pos = arc_api.FindColorE(1480,875,1541,911,"f9eedf-000000|646264-000000",1.0,0)
        continue_pos = continue_pos.split("|")
        if int(continue_pos[1]) > 0:
            time.sleep(0.5)
            print("点击继续")
            arc_api.mouse_click(1501,860,0)
            return py_trees.common.Status.RUNNING
        pos = arc_api.FindColorE(1317,124,1391,148,"ffbc13-000000|090c19-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) <= 0 :
            self.blackboard.need_collect = False
            friend_list = game_manager.get_friend_list()
            print(f"\n===== 好友列表（共 {len(friend_list)} 个） =====")
            for idx, friend in enumerate(friend_list):
                client.insert_data("arc_game",friend['name'],"1","1",50)
            return py_trees.common.Status.RUNNING
        
        return py_trees.common.Status.RUNNING
