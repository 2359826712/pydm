
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
        self.blackboard.register_key(key="window_hwd", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="window_hwd", access=py_trees.common.Access.READ)#READ
        self.time = 0
        self.time1 = 0
    def update(self) -> py_trees.common.Status:
        # FindWindow(class, title)
        window_hwd = arc_api.FindWindowByProcess("PioneerGame.exe")
        self.blackboard.set("window_hwd",window_hwd)
        if window_hwd > 0:
            window_rect = arc_api.GetWindowRect(window_hwd)
            if window_rect[3] - window_rect[1] <= 800 and window_rect[4] - window_rect[2] <= 450 :
                print("游戏加载...")
                return py_trees.common.Status.RUNNING
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
                if window_rect[0] == 1 :
                    if window_rect[1] !=0 and window_rect[2]!=0 :
                        print("移动窗口")
                        arc_api.MoveWindow(window_hwd,0,0)
                        self.time = 0
            if window_rect[3] - window_rect[1] != 1616 or window_rect[4] - window_rect[2] != 939 :
                print("设置窗口大小") 
                arc_api.SetWindowSize(window_hwd,1616,939)
                arc_api.SetClientSize(window_hwd,1600,900)
                return py_trees.common.Status.RUNNING
            return py_trees.common.Status.SUCCESS
        else:
            print("游戏未启动")
            self.blackboard.set("bind_windows",False)
            steam_window_hwd = arc_api.FindWindowByProcess("steamwebhelper.exe")
            if steam_window_hwd > 0 and not self.blackboard.get("window_hwd"):
                print("绑定steam窗口")
                arc_api.BindWindow(steam_window_hwd)
                print("最大化steam窗口")
                arc_api.SetWindowState(steam_window_hwd,7)
                print("置顶steam窗口")
                arc_api.SetWindowState(steam_window_hwd,8)
                print("解除置顶steam窗口")
                arc_api.SetWindowState(steam_window_hwd,9)
                print("查找启动按钮")
                start_button = arc_api.FindPicE(0,0,2000,2000,"start_button.bmp","000000",0.9,0)
                start_button = start_button.split("|")
                if int(start_button[1]) > 0 :
                    time.sleep(0.5)
                    print("点击启动按钮")
                    arc_api.mouse_click(start_button[1],start_button[2],0)
                    time.sleep(1.5)
                arc_api.UnBindWindow()
            return py_trees.common.Status.FAILURE
        