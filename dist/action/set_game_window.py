
from re import A
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))  # 添加上一级目录
from threading import local
from time import thread_time_ns
import py_trees
import time
from arcapi import Arc_api, dm
arc_api = Arc_api()


import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

class Set_Game_Window(py_trees.behaviour.Behaviour):

    def __init__(self,  name="设置游戏窗口"):
        super(Set_Game_Window, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="bind_windows", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="bind_windows", access=py_trees.common.Access.READ)#READ
        self.time = 0
    def update(self) -> py_trees.common.Status:
        # FindWindow(class, title)
        window_hwd = arc_api.FindWindowByProcess("PioneerGame.exe")
        if window_hwd > 0:
            print(f"游戏已启动, 句柄: {window_hwd}")
            if not self.blackboard.get("bind_windows"):
                if arc_api.BindWindow(window_hwd):
                    print("绑定窗口")
                    self.blackboard.set("bind_windows",True)
            if self.time == 0 or time.time() - self.time > 60 :
                self.time = time.time()
                arc_api.SetWindowState(window_hwd,7)
                print("置顶窗口")
                arc_api.SetWindowState(window_hwd,8)
                print("解除置顶窗口")
                arc_api.SetWindowState(window_hwd,9)
                window_rect = arc_api.GetWindowRect(window_hwd)
                if window_rect[0] == 1 :
                    if window_rect[1] !=0 and window_rect[2]!=0 :
                        arc_api.MoveWindow(window_hwd,0,0)
                    if window_rect[3] - window_rect[1] < 1600 or window_rect[4] - window_rect[2] < 900 :
                        arc_api.SetWindowSize(window_hwd,1600,900)
            return py_trees.common.Status.SUCCESS
        else:
            print("游戏未启动")
            return py_trees.common.Status.FAILURE
        