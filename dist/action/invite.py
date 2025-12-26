
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
arc_api = Arc_api()
client = ApiClient()


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
    def update(self) -> py_trees.common.Status:
        if arc_api.select_mode !="2" :
            print("发送好友申请")
            return py_trees.common.Status.FAILURE
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
            print("点击最近")
            time.sleep(1.5)
            arc_api.mouse_click(722,136,0)
            return py_trees.common.Status.RUNNING
        
        
        return py_trees.common.Status.RUNNING
