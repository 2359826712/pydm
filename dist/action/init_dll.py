
from re import A
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))  # 添加上一级目录
from threading import local, Thread
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

class Init_Dll(py_trees.behaviour.Behaviour):

    def __init__(self,  name="初始化dll"):
        super(Init_Dll, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="init_dll", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="init_dll", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.time = 0
        self.account = 0 # 确保 self.account 被初始化

    def _check_and_click_continue(self):
        """检查并点击继续按钮"""
        # 检查图片
        continue_pos_pic = arc_api.FindPic(1480,875,1541,911,"continue.bmp","000000",1.0,0)
        if int(continue_pos_pic[1]) > 0:
            time.sleep(0.5)
            print("点击继续(图片)")
            arc_api.mouse_click(1501,860,0)
            return True
            
        # 检查颜色
        continue_pos = arc_api.FindColorE(1480,875,1541,911,"f9eedf-000000|646264-000000",1.0,0)
        continue_pos = continue_pos.split("|")
        if int(continue_pos[1]) > 0:
            time.sleep(0.5)
            print("点击继续(颜色)")
            arc_api.mouse_click(1501,860,0)
            return True
        return False
    
    def _async_init_data(self):
        """异步执行 game_manager.init_game_data()"""
        init_thread = Thread(target=arc_api.game_manager.init_game_data)
        init_thread.daemon = True
        init_thread.start()
        time.sleep(2)


    def update(self) -> py_trees.common.Status:
        pos = arc_api.FindColorE(26,787,266,869,"54c8e9-000000|ffffff-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[1]) > 0:
            print("正在游戏")
            time.sleep(0.5)
            self.blackboard.in_game = True
            self._async_init_data()
            self.blackboard.init_dll = True
            time.sleep(1)
            return py_trees.common.Status.RUNNING
        # 2. 检查继续按钮
        if self._check_and_click_continue():
            return py_trees.common.Status.RUNNING
        self._async_init_data()
        time.sleep(0.1)
        arc_api.mouse_click(739,545,0)
        self.blackboard.init_dll = True
        return py_trees.common.Status.RUNNING