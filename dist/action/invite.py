
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

class Invite(py_trees.behaviour.Behaviour):

    def __init__(self,  name="加好友"):
        super(Invite, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_invite", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="count_game", access=py_trees.common.Access.READ)#READ
        self.time = 0
        self.account = 0
        self.click_account = 0
    def update(self) -> py_trees.common.Status:
        self.blackboard.in_game = False
        pos = arc_api.FindColorE(26,787,266,869,"54c8e9-000000|ffffff-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[1]) > 0:
            time.sleep(0.5)
            self.blackboard.need_invite = False
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
        if self.blackboard.count_game < 4:
            self.blackboard.need_invite = False
            return py_trees.common.Status.RUNNING
        pos = arc_api.FindColorE(1317,124,1391,148,"ffbc13-000000|090c19-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) <= 0 :
            time.sleep(0.5)
            print("点击esc")
            self.click_account = 0
            arc_api.click_keyworld("esc")
            time.sleep(1.5)
            return py_trees.common.Status.RUNNING
        near_pos = arc_api.FindColorE(685,117,758,152,"f9eedf-000000",1.0,0)
        near_pos = near_pos.split("|")
        if int(near_pos[0]) <= 0 :
            time.sleep(0.5)
            time.sleep(1)
            arc_api.mouse_click(722,136,0)
            return py_trees.common.Status.RUNNING
        time.sleep(1.5)
        arc_api.mouse_click(830,236,1)
        time.sleep(1.5)
        add_pos = arc_api.FindColorE(830,236,1038,446,"37373f-000000",1.0,0)
        add_pos = add_pos.split("|") 
        if int(add_pos[1]) > 0 : 
            steam_pos = arc_api.FindColorE(837,277,860,300,"f7ecdd-000000|020202-000000|000000-000000",1.0,0)
            steam_pos = steam_pos.split("|")
            glob_pos = arc_api.FindColorE(837,277,860,300,"312f2c-000000|f4e9da-000000|b8b0a5-000000",1.0,0)
            glob_pos = glob_pos.split("|")
            if int(steam_pos[0]) > 0 or int(glob_pos[0]) > 0 :
                arc_api.mouse_click(910,320,0)
            else:
                arc_api.mouse_click(910,288,0)
        else:
            time.sleep(1.5)
            arc_api.mouse_click(1275,236,1)
        time.sleep(1.5)
        arc_api.mouse_click(1275,236,1)
        time.sleep(1.5)
        add_pos = arc_api.FindColorE(1275,236,1486,457,"37373f-000000",1.0,0)
        add_pos = add_pos.split("|") 
        if int(add_pos[1]) > 0 : 
            steam_pos = arc_api.FindColorE(1283,278,1305,299,"f7ecdd-000000|020202-000000|000000-000000",1.0,0)
            steam_pos = steam_pos.split("|")
            glob_pos = arc_api.FindColorE(1283,278,1305,299,"312f2c-000000|f4e9da-000000|b8b0a5-000000",1.0,0)
            glob_pos = glob_pos.split("|")
            if int(steam_pos[0]) > 0 or int(glob_pos[0]) > 0 :
                arc_api.mouse_click(1355,320,0)
            else:
                arc_api.mouse_click(1355,290,0)
        else:
            time.sleep(1.5)
            arc_api.mouse_click(830,236,1)
        time.sleep(1.5)
        while self.account != 3:
            arc_api.WheelDown()
            self.account += 1
            time.sleep(0.5)
        bottom_pos =  arc_api.FindColorE(1520,774,1534,779,"1b1b1d-000000|777370-000000|f9eedf-000000",1.0,0)
        bottom_pos = bottom_pos.split("|")
        if int(bottom_pos[1]) > 0:
            time.sleep(0.5)
            print("返回")
            self.blackboard.need_invite = False
            self.click_account = 0
            arc_api.click_keyworld("esc")
        self.account = 0
        return py_trees.common.Status.RUNNING
