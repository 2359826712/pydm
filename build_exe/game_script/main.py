from calendar import c
import os
import sys
import keyboard

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir,))  # 添加上一级目录
sys.path.append(f"{script_dir}\\action")
sys.path.append(f"{script_dir}\\arcapi")
sys.path.append(f"{script_dir}\\pic")
from arcapi import Arc_api
import py_trees
from action.mission import main_tree
arc_api = Arc_api()
arc_api.init_data()
if __name__ == "__main__":
    blackboard = py_trees.blackboard.Blackboard()
    blackboard.set("bind_windows",False)
    blackboard.set("in_game",False)
    blackboard.set("need_collect",False)
    blackboard.set("window_hwd",None)
    blackboard.set("create_collect",None)
    blackboard.set("init_dll",False)
    tree =  main_tree()
    
    while True:
        try:
            if keyboard.is_pressed('down'):
                arc_api.UnBindWindow()
                break 
            tree.tick()
           
        except Exception as e:
            print(f"发生了一个错误: {e}")
            traceback.print_exc()
            arc_api.UnBindWindow()