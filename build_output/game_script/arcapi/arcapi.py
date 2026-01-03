import win32com.client
import os
import sys
import struct
# import win32gui
# import win32process
import time
import configparser
from pathlib import Path
import pyperclip
import pyautogui
import requests
import base64
import io
import win32api
import win32con
import json
from game_manager import ArcGameManager
# 检查 Python 位数
is_64bits = struct.calcsize('P') * 8 == 64
if is_64bits:
    print("警告: 检测到当前 Python 为 64 位环境。")
    print("大漠插件 (dm.dll) 通常为 32 位，无法直接在 64 位 Python 中加载。")
    print("请切换到 32 位 Python 环境运行此脚本。")
try:
    dm = win32com.client.Dispatch('dm.dmsoft')
except Exception:
    # 尝试自动注册
    try:
        # 判断是否为打包后的环境
        if getattr(sys, 'frozen', False):
            # exe 运行模式：默认在 exe 同级目录下找 dm.dll
            base_dir = os.path.dirname(sys.executable)
            dll_path = os.path.join(base_dir, 'dm.dll')
            # 如果在 internal 目录（视打包方式而定，这里优先同级目录方便替换）
            if not os.path.exists(dll_path):
                 dll_path = os.path.join(base_dir, '_internal', 'dm.dll')
        else:
            # 源码运行模式
            dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dm.dll'))
        # print(dll_path)
        # if not os.path.exists(dll_path):
        #      # 最后的兜底
        #      dll_path = r"c:\Users\lsx\Desktop\pydm\dm.dll"
        
        if os.path.exists(dll_path):
            print(f"检测到未注册，正在尝试注册插件: {dll_path}")
            os.system(f'regsvr32 /s "{dll_path}"')
            dm = win32com.client.Dispatch('dm.dmsoft')
        else:
            raise Exception(f"找不到 dm.dll，请确保它在 {dll_path}")
    except Exception as e:
        print(f"大漠插件调用失败: {e}")
        sys.exit(1)

class Arc_api:
    _instance = None  # 用于存储类的唯一实例

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            pass
    def init_data(self):
        # print(f"当前大漠插件版本: {dm.Ver()}")
        ret = dm.RegEx("aa3284965360fb57d3f81ef4ce8379669bd756f91f5" , "" , "121.204.249.29|121.204.253.161|125.77.165.62|125.77.165.131")
        if ret != -1:
            print("注册成功")
        else:
            print("注册失败")
        dm.SetMouseDelay("normal",50)
        dm.SetKeypadDelay("normal",30)
        dm.SetMouseSpeed(6)
        dm.SetShowErrorMsg(0)
        dm.SetSimMode(0)
        self.game_manager = ArcGameManager()
        # 设置 pic 目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pic_dir = os.path.abspath(os.path.join(script_dir, "..", "pic"))
        self.pic_dir = pic_dir
        dm.SetKeypadDelay("normal",30)

    # 查找符合类名或者标题名的顶层可见窗口
    def FindWindow(self,clas="",title=""):
        return dm.FindWindow(clas,title )
    # 根据指定的进程名字，来查找可见窗口.
    def FindWindowByProcess(self,process_name,clas="",title=""):
        return dm.FindWindowByProcess(process_name,clas,title)
    # 绑定指定的窗口,并指定这个窗口的屏幕颜色获取方式,鼠标仿真模式,键盘仿真模式,以及模式设定
    def BindWindow(self,hwnd,display="normal",mouse="normal",keypad="normal",mode=0):
        return dm.BindWindow(hwnd,display,mouse,keypad,mode)

    def UnBindWindow(self):
        print("解绑窗口")
        return dm.UnBindWindow()
    # 查找窗口状态
    # flag: 0 : 判断窗口是否存在 1 : 判断窗口是否处于激活 2 : 判断窗口是否可见 3 : 判断窗口是否最小化
    # 4 : 判断窗口是否最大化
    # 5 : 判断窗口是否置顶
    # 6 : 判断窗口是否无响应
    # 7 : 判断窗口是否可用(灰色为不可用)
    # 8 : 另外的方式判断窗口是否无响应,如果6无效可以尝试这个
    # 9 : 判断窗口所在进程是不是64位#
    def GetWindowState(self,hwd,flag):
        ret = dm.GetWindowState(hwd,flag)
        return ret
    def GetWindowRect(self,hwd):
        ret = dm.GetWindowRect(hwd)
        return ret

    def SetWindowSize(self,hwnd,width,height):
        ret = dm.SetWindowSize(hwnd,width,height)
        return ret
    def SetClientSize(self,hwnd,width,height):
        ret = dm.SetClientSize(hwnd,width,height)
        return ret
    # 移动指定窗口到指定位置
    def MoveWindow(self,hwd,x,y):
        return dm.MoveWindow(hwd,x,y) 
    def system_move_to(self, x, y):
        """系统级鼠标移动(前台)"""
        win32api.SetCursorPos((int(x), int(y)))


    def system_click(self):
        """系统级鼠标移动并左键点击(前台)"""
        # self.system_move_to(x, y)
        # time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    # 设置窗口的状态
    # flag: 0 : 关闭指定窗口 1 : 激活指定窗口 2 : 最小化指定窗口,但不激活
    #   3 : 最小化指定窗口,并释放内存,但同时也会激活窗口.(释放内存可以考虑用FreeProcessMemory函数)
    # 4 : 最大化指定窗口,同时激活窗口.
    # 5 : 恢复指定窗口 ,但不激活 6 : 隐藏指定窗口 7 : 显示指定窗口 8 : 置顶指定窗口
    # 9 : 取消置顶指定窗口
    # 10 : 禁止指定窗口 11 : 取消禁止指定窗口 12 : 恢复并激活指定窗口
    # 13 : 强制结束窗口所在进程. 14 : 闪烁指定的窗口 15 : 使指定的窗口获取输入焦点
    def SetWindowState(self,hwnd,flag):
        ret = dm.SetWindowState(hwnd,flag)
        return ret  
    def move_to(self,x,y):
        ret = dm.MoveTo(x,y)
        return ret
    def mouse_click(self,x,y,state):
        mouse_mov = self.move_to(x,y)
        if mouse_mov == 1:
            if state == 0:
                dm.LeftClick()
            elif state == 1:
                dm.RightClick()
            elif state == 2:
                dm.LeftDoubleClick()

    def FindColorE(self,x1, y1, x2, y2, color, sim, dir):
        return dm.FindColorE(x1, y1, x2, y2, color, sim, dir)

    def FindMultiColorE(self,x1, y1, x2, y2,first_color,offset_color,sim, dir):
        return dm.FindMultiColorE(x1, y1, x2, y2,first_color,offset_color,sim, dir)
    def FindMulColor(self,x1, y1, x2, y2,color_list,sim):
        return dm.FindMultiColorE(x1, y1, x2, y2,color_list,sim)

    def FindMultiColor(self,x1, y1, x2, y2,first_color,offset_color,sim,dir,x=0,y=0):
        return dm.FindMultiColor(x1, y1, x2, y2,first_color,offset_color,sim,dir,x,y)
    def FindPicE(self,x1, y1, x2, y2, pic_name, delta_color,sim, dir):
        pic = f"{self.pic_dir}\\{pic_name}"
        return dm.FindPicE(x1, y1, x2, y2, pic, delta_color,sim, dir)
    def FindPic(self,x1, y1, x2, y2, pic_name, delta_color,sim, dir):
        pic = f"{self.pic_dir}\\{pic_name}"
        return dm.FindPic(x1, y1, x2, y2, pic, delta_color,sim, dir)
    def _vk_to_key_name(self, vk_code):
        vk_map = {
            "0": 48,
            "1": 49,
            "2": 50,
            "3": 51,
            "4": 52,
            "5": 53,
            "6": 54,
            "7": 55,
            "8": 56,
            "9": 57,
            "a": 65,
            "b": 66,
            "c": 67,
            "d": 68,
            "e": 69,
            "f": 70,
            "g": 71,
            "h": 72,
            "i": 73,
            "j": 74,
            "k": 75,
            "l": 76,
            "m": 77,
            "n": 78,
            "o": 79,
            "p": 80,
            "q": 81,
            "r": 82,
            "s": 83,
            "t": 84,
            "u": 85,
            "v": 86,
            "w": 87,
            "x": 88,
            "y": 89,
            "z": 90,
            "f10": 121,
            "esc": 27,
            "tab": 9,
            "enter": 13,
            "space": 32,
            "back": 8,
            "shift": 160,
            "ctrl": 17,
            "alt": 18,
            "left": 37,
            "up": 38,
            "right": 39,
            "down": 40,
            ".": 190,
            "`": 192,
            "]": 221,
            "-": 189,
            "=": 187,
            "/": 191,
            "pageup": 33,
            "f8": 119,
        }
        return vk_map.get(vk_code, '')

    def click_keyworld(self,key,state = 0):
        if state == 0:
            dm.KeyDownChar(key)
            time.sleep(0.1)
            dm.KeyUpChar(key)
        else:
            return 0
    def KeyDownChar(self,key):
        dm.KeyDownChar(key)
        
    def KeyUpChar(self,key):
        dm.KeyUpChar(key)
    def WheelDown(self):
        return dm.WheelDown()

    def KillProcess(self, process_name):
        """强制结束指定进程"""
        os.system(f'taskkill /f /im {process_name}')

    # 获取窗口客户区域在屏幕上的位置
    def GetClientRect(self,hwnd):
        ret = dm.GetClientRect(hwnd)
        return ret

    # 获取窗口客户区域的大小
    def GetClientSize(self,hwnd,width=0,height=0):
        ret = dm.GetClientSize(hwnd,width,height)
        return ret

    def get_script_config(self, getpath):
        config_path = f"{getpath}\\ggc.ini"
        if os.path.exists(config_path):
            setting = configparser.ConfigParser()
            setting.read(config_path)
            try:
                my_path = setting["UserInfo"]["ggc"]
                return my_path
            except KeyError as e:
                # print(f'KeyError: {e}')
                return 
    
    def read_first_n_lines(self, path, n=50, encoding="utf-8", strip=True):
        p = Path(path)
        result = []
        with p.open("r", encoding=encoding, errors="replace") as f:
            for i, line in enumerate(f):
                if i >= n:
                    break
                result.append(line.rstrip("\r\n") if strip else line)
        return result

    # 粘贴输入文本
    def paste_text(self, text):
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
    def select_mode(self):
        """读取 select_mode.txt 中的 model 值"""
        try:
            if getattr(sys, 'frozen', False):
                 # exe 模式
                 file_path = os.path.join(os.path.dirname(sys.executable), "select_mode.txt")
            else:
                 # 源码模式
                 script_dir = os.path.dirname(os.path.abspath(__file__))
                 file_path = os.path.abspath(os.path.join(script_dir, "..", "select_mode.txt"))
            
            if not os.path.exists(file_path):
                print(f"配置文件不存在: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if "model" in line and "=" in line:
                        parts = line.split('=')
                        if len(parts) > 1:
                            return parts[1].strip()
            return None
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return None
    def get_channel(self):
        try:
            if getattr(sys, 'frozen', False):
                file_path = os.path.join(os.path.dirname(sys.executable), "select_mode.txt")
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.abspath(os.path.join(script_dir, "..", "select_mode.txt"))
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "channel" in line and "=" in line:
                        parts = line.split("=", 1)
                        if len(parts) > 1:
                            v = parts[1].strip()
                            try:
                                n = int(v)
                                if 1 <= n <= 6:
                                    return n
                            except Exception:
                                pass
            return None
        except Exception:
            return None

    def get_tokens(self):
        """读取 select_mode.txt 中的 token 值"""
        try:
            if getattr(sys, 'frozen', False):
                 # exe 模式
                 file_path = os.path.join(os.path.dirname(sys.executable), "select_mode.txt")
            else:
                 # 源码模式
                 script_dir = os.path.dirname(os.path.abspath(__file__))
                 file_path = os.path.abspath(os.path.join(script_dir, "..", "select_mode.txt"))
            
            if not os.path.exists(file_path):
                print(f"配置文件不存在: {file_path}")
                return []
                
            # Check modification time to avoid frequent reads and logging
            mtime = os.path.getmtime(file_path)
            if hasattr(self, '_last_token_mtime') and self._last_token_mtime == mtime and hasattr(self, '_cached_tokens'):
                return self._cached_tokens

            tokens = []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 按行处理，支持多行 token 定义 (token = { ... | ... })
            lines = content.splitlines()
            full_token_str = ""
            found_token = False
            
            for line in lines:
                stripped_line = line.strip()
                if not found_token:
                    if "token" in stripped_line and "=" in stripped_line:
                        found_token = True
                        full_token_str += stripped_line
                else:
                    full_token_str += stripped_line
                
                # 如果已经找到 token 且当前行包含 }，则视为结束
                if found_token and "}" in stripped_line:
                    break
            
            if full_token_str:
                parts = full_token_str.split('=', 1)
                if len(parts) > 1:
                    raw_value = parts[1].strip()
                    
                    # 移除外层的括号
                    raw_value = raw_value.strip().strip('{}[]').strip()
                    
                    # 尝试分割
                    if '|' in raw_value:
                        raw_tokens = raw_value.split('|')
                    elif ',' in raw_value:
                            # 兼容逗号分割
                            raw_tokens = raw_value.split(',')
                    else:
                            raw_tokens = [raw_value]
                            
                    for t in raw_tokens:
                        # 清理多余的标点符号
                        clean_t = t.strip().strip('{}[]"\'').strip()
                        if clean_t and len(clean_t) > 20: # 简单的长度过滤，避免读取到空字符串或垃圾字符
                            tokens.append(clean_t)
            
            # 去重
            tokens = list(set(tokens))
            
            # Update cache
            self._last_token_mtime = mtime
            self._cached_tokens = tokens
            
            print(f"成功读取到 {len(tokens)} 个 Token")
            return tokens
        except Exception as e:
            print(f"读取Token失败: {e}")
            return []
    def clear_epic_login_data(self):
        """清除 Epic 账号登录缓存"""
        print("正在清除 Epic 账号记录...")
        
        # 1. 结束 Epic 进程
        # self.KillProcess("EpicGamesLauncher.exe")
        # self.KillProcess("EpicWebHelper.exe")
        # time.sleep(2)  # 等待进程完全释放文件
        
        # 2. 定位 LocalAppData 路径
        local_app_data = os.getenv('LOCALAPPDATA')
        if not local_app_data:
            print("无法获取 LOCALAPPDATA 环境变量")
            return

        epic_saved_path = os.path.join(local_app_data, "EpicGamesLauncher", "Saved")
        
        # 需要清理的目标文件夹列表 (主要是 webcache 存储登录态)
        targets = ["webcache", "webcache_4147", "webcache_4430", "Config"] 
        
        import shutil
        
        for item in targets:
            full_path = os.path.join(epic_saved_path, item)
            if os.path.exists(full_path):
                try:
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path, ignore_errors=True)
                    else:
                        os.remove(full_path)
                    print(f"已删除: {full_path}")
                except Exception as e:
                    print(f"删除失败 {full_path}: {e}")
            else:
                # 尝试模糊匹配 webcache_ 开头的文件夹
                if item == "webcache":
                     for fname in os.listdir(epic_saved_path):
                         if fname.startswith("webcache") or fname.lower() == "config":
                             fpath = os.path.join(epic_saved_path, fname)
                             try:
                                 shutil.rmtree(fpath, ignore_errors=True)
                                 print(f"已删除: {fpath}")
                             except Exception as e:
                                 print(f"删除失败 {fpath}: {e}")
        
        print("Epic 账号记录清理完成")

    def ocr_text(self, x1, y1, x2, y2, target_text="",timeout=3):
        """
        截图并调用本地 OCR 服务进行识别 (不保存图片文件)
        :param x1: 左上角 x
        :param y1: 左上角 y
        :param x2: 右下角 x
        :param y2: 右下角 y
        :param target_text: 可选，过滤目标文本
        :return: 识别结果列表或 None
        """
        try:
            w = x2 - x1
            h = y2 - y1
            if w <= 0 or h <= 0:
                print("无效的截图区域")
                return None
            
            # 使用 pyautogui 截图 (内存操作)
            # 注意: 如果窗口被遮挡或使用了特殊的绑定模式，pyautogui 可能截不到
            img = pyautogui.screenshot(region=(x1, y1, w, h))
            
            # 转 base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # 构造请求
            url = "http://127.0.0.1:5000/ocr"
            payload = {
                "image_base64": img_str,
                "target_text": target_text
            }
            
            # 发送请求
            try:
                response = requests.post(url, json=payload, timeout = timeout)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get("code") == 0:
                        return res_json.get("data")
                    else:
                        print(f"OCR 识别失败: {res_json.get('msg')}")
                        return None
                else:
                    print(f"OCR 服务请求失败: {response.status_code}")
                    return None
            except requests.exceptions.ConnectionError:
                 print("OCR 服务未启动或无法连接 (http://127.0.0.1:5000)")
                 return None
                
        except Exception as e:
            print(f"OCR 调用异常: {e}")
            return None

    def ocr_recognize(self, x1, y1, x2, y2, target_text="",timeout=3):
        data = self.ocr_text(x1, y1, x2, y2, target_text=target_text,timeout=timeout)
        if not data:
            return None
        def _rect_from_box(box):
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            return x_min, y_min, x_max - x_min, y_max - y_min
        out = []
        for item in data:
            box = item.get("box")
            text = item.get("text")
            conf = item.get("confidence")
            cx = sum(p[0] for p in box) / 4.0 + x1
            cy = sum(p[1] for p in box) / 4.0 + y1
            rx, ry, rw, rh = _rect_from_box(box)
            rx += x1
            ry += y1
            out.append({
                "text": text,
                "confidence": conf,
                "box": box,
                "center": [int(cx), int(cy)],
                "rect": [int(rx), int(ry), int(rw), int(rh)]
            })
        return out
