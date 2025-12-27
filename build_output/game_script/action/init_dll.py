
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
from game_manager import ArcGameManager
arc_api = Arc_api()
client = ApiClient()
game_manager = ArcGameManager()


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
        init_thread = Thread(target=game_manager.init_game_data)
        init_thread.daemon = True
        init_thread.start()

    def _handle_steam_glob_click(self, x1, y1, x2, y2, click_x, click_y_steam, click_y_glob):
        """处理 Steam/Global 图标识别并点击"""
        steam_pos = arc_api.FindColorE(x1, y1, x2, y2, "f7ecdd-000000|020202-000000|000000-000000", 1.0, 0)
        steam_pos = steam_pos.split("|")
        glob_pos = arc_api.FindColorE(x1, y1, x2, y2, "312f2c-000000|f4e9da-000000|b8b0a5-000000", 1.0, 0)
        glob_pos = glob_pos.split("|")
        
        if int(steam_pos[0]) > 0 or int(glob_pos[0]) > 0:
            arc_api.mouse_click(click_x, click_y_steam, 0)
        else:
            arc_api.mouse_click(click_x, click_y_glob, 0)

    def update(self) -> py_trees.common.Status:
        # 1. 检查是否在游戏中
        pos = arc_api.FindColorE(26,787,266,869,"54c8e9-000000|ffffff-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[1]) > 0:
            print("正在游戏")
            time.sleep(0.5)
            self.blackboard.in_game = True
            time.sleep(1)
            return py_trees.common.Status.RUNNING
        # 2. 检查继续按钮
        if self._check_and_click_continue():
            return py_trees.common.Status.RUNNING
        # 4. 检查是否在 ESC 菜单或其他界面
        pos = arc_api.FindColorE(1317,124,1391,148,"ffbc13-000000|090c19-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) <= 0 :
            time.sleep(0.5)
            print("点击esc")
            self.click_account = 0
            arc_api.click_keyworld("esc")
            time.sleep(1.5)
            return py_trees.common.Status.RUNNING
        # 5. 检查特定位置颜色 (Near Pos?)
        near_pos = arc_api.FindColorE(685,117,758,152,"f9eedf-000000",1.0,0)
        near_pos = near_pos.split("|")
        if int(near_pos[0]) <= 0 :
            print("点击最近")
            time.sleep(1.5)
            arc_api.mouse_click(722,136,0)
            return py_trees.common.Status.RUNNING

        # 6. 主要逻辑：点击并检查加号位置
        time.sleep(1.5)
        arc_api.mouse_click(830,236,1)
        time.sleep(1.5)
        
        # 检查位置 1
        add_pos = arc_api.FindColorE(830,236,1038,446,"37373f-000000",1.0,0)
        add_pos = add_pos.split("|") 
        if int(add_pos[1]) > 0 : 
            self._async_init_data()
            self._handle_steam_glob_click(837, 277, 860, 300, 910, 320, 288)
            self.blackboard.init_dll = True
        else:
            # 没找到位置 1，尝试位置 2
            time.sleep(1.5)
            arc_api.mouse_click(1275,236,1)
        
        time.sleep(1.5)
        arc_api.mouse_click(1275,236,1)
        time.sleep(1.5)
        
        # 检查位置 2
        add_pos = arc_api.FindColorE(1275,236,1486,457,"37373f-000000",1.0,0)
        add_pos = add_pos.split("|") 
        if int(add_pos[1]) > 0 : 
            self._async_init_data()
            self._handle_steam_glob_click(1283, 278, 1305, 299, 1355, 320, 290)
            self.blackboard.init_dll = True
        else:
            time.sleep(1.5)
            arc_api.mouse_click(830,236,1)
            
        time.sleep(1.5)
        
        # 滚轮操作
        while self.account != 3:
            arc_api.WheelDown()
            self.account += 1
            time.sleep(0.5)
            
        # 完成后返回
        if self.blackboard.init_dll:
            time.sleep(0.5)
            print("返回")
            self.click_account = 0
            arc_api.click_keyworld("esc")
        self.account = 0
        return py_trees.common.Status.RUNNING