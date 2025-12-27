
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

class Exit_Game(py_trees.behaviour.Behaviour):

    def __init__(self,  name="退出游戏"):
        super(Exit_Game, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.WRITE)#READ
        self.time = 0
    def update(self) -> py_trees.common.Status:
        print("退出游戏")
        exit_pos = arc_api.FindColorE(98,628,123,659,"a3a4a9-000000|0b0e1b-000000|a4a5aa-000000",1.0,0)
        exit_pos = exit_pos.split("|")
        if int(exit_pos[1]) > 0:
            time.sleep(0.5)
            print("点击投降")
            arc_api.mouse_click(135,637,0)
        continue_pos_pic = arc_api.FindPic(0,0,1541,911,"continue.bmp","000000",1.0,0)
        if int(continue_pos_pic[1]) > 0:
            time.sleep(0.5)
            print("继续页面")
            self.blackboard.need_collect = True
            return py_trees.common.Status.RUNNING
        yse_pos = arc_api.FindColorE(937,508,962,538,"ffbc13-000000|705616-000000",1.0,0)
        yse_pos = yse_pos.split("|")
        if int(yse_pos[1]) > 0:
            time.sleep(0.5)
            print("点击是")
            arc_api.mouse_click(941,522,0)
        pos = arc_api.FindColorE(26,787,266,869,"54c8e9-000000|ffffff-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[1]) > 0:
            time.sleep(1.5)
            friend_list = game_manager.get_friend_list()
            print(f"\n===== 好友列表（共 {len(friend_list)} 个） =====")
            for idx, friend in enumerate(friend_list):
                client.insert_data("arc_game",friend['name'],"1","1",50)
            arc_api.click_keyworld("esc")
            self.blackboard.in_game = True
        return py_trees.common.Status.RUNNING
