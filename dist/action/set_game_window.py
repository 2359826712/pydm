
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
from game_manager import ArcGameManager
arc_api = Arc_api()
game_manager = ArcGameManager()

import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

import winreg

class Set_Game_Window(py_trees.behaviour.Behaviour):

    def __init__(self,  name="设置游戏窗口"):
        super(Set_Game_Window, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="bind_windows", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="bind_windows", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="window_hwd", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="window_hwd", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="init_dll", access=py_trees.common.Access.WRITE)#READ
        self.time = 0
        self.time1 = 0
        self.retry_count = 0
        self.clean_data = False
        self.last_window_hwd = 0
        self._disable_wer()

    def _disable_wer(self):
        """禁用 Windows Error Reporting 以防止崩溃弹窗"""
        try:
            key_path = r"Software\Microsoft\Windows\Windows Error Reporting"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "DontShowUI", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "Disabled", 0, winreg.REG_DWORD, 1)
            print("已禁用 Windows Error Reporting (WER)")
        except Exception as e:
            print(f"禁用 WER 失败: {e}")

    def update(self) -> py_trees.common.Status:
        # 优先检测崩溃弹窗
        wer_hwd = arc_api.FindWindowByProcess("WerFault.exe")
        if wer_hwd > 0:
            print("检测到崩溃弹窗 (WerFault)，正在清理...")
            arc_api.KillProcess("WerFault.exe")
            arc_api.KillProcess("PioneerGame.exe")
            time.sleep(1)
            # 强制重置 window_hwd 触发重启逻辑
            window_hwd = 0
        else:
            window_hwd = arc_api.FindWindowByProcess("PioneerGame.exe")
            
        self.blackboard.set("window_hwd",window_hwd)

        if window_hwd != self.last_window_hwd:
            self.blackboard.set("bind_windows", False)
            self.last_window_hwd = window_hwd

        if window_hwd > 0:
            # 二次验证：确保句柄真的有效（避免进程刚死但句柄还在的极短窗口期）
            if arc_api.GetWindowState(window_hwd, 0) == 0:
                print("窗口句柄已失效")
                window_hwd = 0
                self.blackboard.set("window_hwd", 0)
        
        if window_hwd > 0:
            self.clean_data = False
            self.retry_count = 0
            window_rect = arc_api.GetWindowRect(window_hwd)
            if window_rect[3] - window_rect[1] <= 800 and window_rect[4] - window_rect[2] <= 450 :
                print("游戏加载...")
                return py_trees.common.Status.RUNNING
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
            self.blackboard.set("init_dll",False)
            if not self.clean_data:
                game_manager.cleanup_game_data()
                self.clean_data = True
            if self.time1 and time.time() - self.time1 < 180 :
                print("等待游戏启动")
                time.sleep(1)
                return py_trees.common.Status.RUNNING
            elif self.time1 == 0 or time.time() - self.time1 >= 180 :
                print("cmd启动游戏")
                # 启动前清理可能的僵尸进程和错误弹窗
                arc_api.KillProcess("WerFault.exe")
                arc_api.KillProcess("PioneerGame.exe")
                
                os.startfile("steam://rungameid/1808500")
                self.time1 = time.time()
                self.retry_count += 1
                if self.retry_count > 3:
                    arc_api.KillProcess("PioneerGame.exe")
                    time.sleep(1)
                    arc_api.KillProcess("steam.exe")
                    self.retry_count = 0
            return py_trees.common.Status.FAILURE
        
