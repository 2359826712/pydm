from calendar import c
import os
import sys
import keyboard
script_dir = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
sys.path.append(os.path.join(script_dir,))  # 添加上一级目录
sys.path.append(f"{script_dir}\\action")
sys.path.append(f"{script_dir}\\arcapi")
sys.path.append(f"{script_dir}\\pic")
from arcapi import Arc_api
from api_client import ApiClient
client = ApiClient()
arc_api = Arc_api()
