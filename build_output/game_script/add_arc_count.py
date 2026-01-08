from calendar import c
import os
import sys
import keyboard
from pyautogui import click
script_dir = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
sys.path.append(os.path.join(script_dir,))  # 添加上一级目录
sys.path.append(f"{script_dir}\\action")
sys.path.append(f"{script_dir}\\arcapi")
sys.path.append(f"{script_dir}\\pic")
from arcapi import Arc_api
arc_api = Arc_api()
arc_api.create_new_game("arc_account")

def import_accounts():
    file_path = os.path.join(script_dir, "account.text")
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    print(f"开始读取文件: {file_path}")
    count = 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split("|")
                if len(parts) >= 2:
                    account = parts[0].strip()
                    password = parts[1].strip()
                    
                    # 默认参数
                    b_zone = "1"
                    s_zone = "1"
                    status = 0     # 0:未封号
                    in_use = "0"     # 0:未使用
                    level = "1"
                    computer_number = "0"
                    
                    print(f"正在插入账号: {account}")
                    # 调用 arc_api.insert_data_game
                    # 参数: game_name, account, password, b_zone, s_zone, status, in_use, level, computer_number
                    arc_api.insert_data_game("arc_account", account, password, b_zone, s_zone, status, in_use, level, computer_number)
                    count += 1
                else:
                    print(f"格式错误行: {line}")
                    
        print(f"导入完成，共导入 {count} 个账号")
        
    except Exception as e:
        print(f"读取或导入过程发生错误: {e}")

if __name__ == "__main__":
    import_accounts()
