from calendar import c
import os
import sys
import keyboard
# from arcapi.api_client import ApiClient
# client = ApiClient()
# client.clear_talk_channel("arc_game",1)
script_dir = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
sys.path.append(os.path.join(script_dir,))  # 添加上一级目录
sys.path.append(f"{script_dir}\\action")
sys.path.append(f"{script_dir}\\arcapi")
sys.path.append(f"{script_dir}\\pic")
from arcapi import Arc_api
import py_trees
from action.mission import main_tree
import traceback
import time
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    arc_api = Arc_api()
    arc_api.init_data()
    blackboard = py_trees.blackboard.Blackboard()
    blackboard.set("bind_windows",False)
    blackboard.set("in_game",False)
    blackboard.set("need_collect",False)
    blackboard.set("window_hwd",None)
    blackboard.set("create_collect",None)
    blackboard.set("init_dll",False)
    blackboard.set("middle_window_click",False)
    tree =  main_tree()
    
    while True:
        try:
            if keyboard.is_pressed('down'):
                arc_api.UnBindWindow()
                break 
            tree.tick()
           
        except Exception as e:
            print(f"发生了一个错误: {e}")
            try:
                traceback.print_exc()
            except:
                pass
            
            # 遇到错误不要退出循环，而是尝试清理并继续
            print("尝试从错误中恢复...")
            try:
                arc_api.UnBindWindow()
            except:
                pass
            time.sleep(1) # 防止死循环刷屏
