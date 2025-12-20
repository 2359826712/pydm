
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

class Start_Game(py_trees.behaviour.Behaviour):

    def __init__(self,  name="开始游戏"):
        super(Start_Game, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="need_invite", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="count_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="count_game", access=py_trees.common.Access.READ)#READ
        self.time = 0
    def update(self) -> py_trees.common.Status:
        print("开始游戏")
        close_pos = arc_api.FindPicE(0,0,1450,645,"close.bmp","000000",1.0,0)
        close_pos = close_pos.split("|")
        if int(close_pos[1]) > 0 :
            time.sleep(0.5)
            print("点击关闭")
            arc_api.mouse_click(472,558,0)
            return py_trees.common.Status.RUNNING
        ans_pos = arc_api.FindColorE(811,536,879,553,"b39347-000000|665632-000000",1.0,0)
        ans_pos = ans_pos.split("|")
        if int(ans_pos[1]) > 0:
            time.sleep(0.5)
            print("反馈页面")
            arc_api.mouse_click(739,545,0)
            return py_trees.common.Status.RUNNING
        pos2 = arc_api.FindColorE(916,523,986,539,"ffbc13-000000",1.0,0)
        pos2 = pos2.split("|")
        if int(pos2[1]) > 0:
            time.sleep(0.5)
            print("点击中间弹窗")
            arc_api.mouse_click(948,523,0)
            return py_trees.common.Status.RUNNING
        if self.blackboard.need_invite:
            print("需要邀请")
            return py_trees.common.Status.FAILURE
        if self.blackboard.in_game:
            print("在游戏内")
            return py_trees.common.Status.SUCCESS
        if self.blackboard.count_game >= 4:
            self.blackboard.count_game = 0
        pos = arc_api.FindColorE(1317,124,1391,148,"ffbc13-000000|090c19-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) > 0 :
            time.sleep(0.5)
            print("点击esc")
            self.click_account = 0
            arc_api.click_keyworld("esc")
            time.sleep(1.5)
            return py_trees.common.Status.RUNNING
        play_pos = arc_api.FindPicE(544,418,945,697,"da_ba.bmp","000000",1.0,0)
        play_pos = play_pos.split("|")
        if int(play_pos[1]) > 0 :
            time.sleep(0.5)
            print("点击大坝战场")
            arc_api.mouse_click(745,475,0)
            return py_trees.common.Status.RUNNING
        pos = arc_api.FindColorE(1256,711,1549,781,"ffbc13-000000|090c19-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) > 0 :
            time.sleep(0.5)
            print("点击开始")
            arc_api.mouse_click(1402,736,0)
            return py_trees.common.Status.RUNNING
        return py_trees.common.Status.SUCCESS
