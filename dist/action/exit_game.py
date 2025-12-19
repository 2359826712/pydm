
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
arc_api = Arc_api()


import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

class Exit_Game(py_trees.behaviour.Behaviour):

    def __init__(self,  name="退出游戏"):
        super(Exit_Game, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_invite", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="count_game", access=py_trees.common.Access.WRITE)#READ
        self.time = 0
    def update(self) -> py_trees.common.Status:
        print("退出游戏")
        continue_pos = arc_api.FindColorE(1478,848,1523,874,"f9eedf-000000|646264-000000",1.0,0)
        continue_pos = continue_pos.split("|")
        if int(continue_pos[1]) > 0:
            time.sleep(0.5)
            print("继续页面")
            self.blackboard.need_invite = True
            self.blackboard.count_game += 1
        
        exit_pos = arc_api.FindPicE(90,614,182,657,"exit.bmp","090c19-000000|ebdecb-000000|a4a5aa-000000",1.0,0)
        exit_pos = exit_pos.split("|")
        if int(exit_pos[1]) > 0:
            time.sleep(0.5)
            print("点击投降")
            arc_api.mouse_click(135,637,0)
        yse_pos = arc_api.FindColorE(937,508,962,538,"ffbc13-000000|705616-000000",1.0,0)
        yse_pos = yse_pos.split("|")
        if int(yse_pos[1]) > 0:
            time.sleep(0.5)
            print("点击是")
            arc_api.mouse_click(941,522,0)
        pos = arc_api.FindColorE(26,787,266,869,"54c8e9-000000|ffffff-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[1]) > 0:
            time.sleep(0.5)
            print("点击esc")
            arc_api.click_keyworld("esc")
            self.blackboard.in_game = True
            time.sleep(1)
        return py_trees.common.Status.RUNNING
