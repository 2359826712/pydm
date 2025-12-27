import win32com.client
import os
import sys
import struct
import win32gui
import win32process
import time

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
        
        if not os.path.exists(dll_path):
             # 最后的兜底
             dll_path = r"c:\Users\lsx\Desktop\pydm\dm.dll"
        
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
        ret = dm.RegEx("aa3284965360fb57d3f81ef4ce8379669bd756f91f5" , "" , "121.204.249.29|121.204.253.161|125.77.165.62|125.77.165.131")
        if ret != -1:
            print("注册成功")
        else:
            print("注册失败")
        dm.SetSimMode(0)
        dm.SetMouseDelay("normal",30)
        dm.SetKeypadDelay("normal",30)
        dm.SetMouseSpeed(6)
        a =dm.SetShowErrorMsg(0)
        print(a)
        print(1111111111111111111111)
        # 设置 pic 目录
        if getattr(sys, 'frozen', False):
             # exe 模式：在 exe 同级目录下找 pic 文件夹
             pic_dir = os.path.join(os.path.dirname(sys.executable), "pic")
        else:
             # 源码模式
             script_dir = os.path.dirname(os.path.abspath(__file__))
             pic_dir = os.path.abspath(os.path.join(script_dir, "..", "pic"))
        self.pic_dir = pic_dir
        dm.SetKeypadDelay("normal",30)
    def FindWindow(self,clas="",title=""):
        return dm.FindWindow(clas,title )
    def FindWindowByProcess(self,process_name,clas="",title=""):
        return dm.FindWindowByProcess(process_name,clas,title)
    def BindWindow(self,hwnd,display="normal",mouse="normal",keypad="normal",mode=0):
        try:
            return dm.BindWindow(hwnd,display,mouse,keypad,mode)
        except Exception as e:
            print(f"BindWindow error: {e}")
            return 0

    def UnBindWindow(self):
        print("解绑窗口")
        try:
            return dm.UnBindWindow()
        except Exception as e:
            print(f"UnBindWindow error: {e}")
            return 0
            
    def GetWindowState(self,hwd,flag):
        try:
            ret = dm.GetWindowState(hwd,flag)
            return ret
        except Exception as e:
            print(f"GetWindowState error: {e}")
            return 0
            
    def GetWindowRect(self,hwd):
        try:
            ret = dm.GetWindowRect(hwd)
            return ret
        except Exception as e:
            print(f"GetWindowRect error: {e}")
            return (0,0,0,0)

    def SetWindowSize(self,hwnd,width,height):
        ret = dm.SetWindowSize(hwnd,width,height)
        return ret
    def SetClientSize(self,hwnd,width,height):
        ret = dm.SetClientSize(hwnd,width,height)
        return ret
    def MoveWindow(self,hwd,x,y):
        return dm.MoveWindow(hwd,x,y) 

    def SetWindowState(self,hwnd,flag):
        ret = dm.SetWindowState(hwnd,flag)
        return ret  
    def mouse_click(self,x,y,state):
        try:
            mouse_mov = dm.MoveTo(x,y)
            if mouse_mov == 1:
                if state == 0:
                    dm.LeftClick()
                elif state == 1:
                    dm.RightClick()
        except Exception as e:
            print(f"mouse_click error: {e}")
            # 如果点击失败（通常是因为窗口丢失），尝试清理环境
            self.KillProcess("WerFault.exe")

    def FindColorE(self,x1, y1, x2, y2, color, sim, dir):
        return dm.FindColorE(x1, y1, x2, y2, color, sim, dir)
    
    def FindMultiColorE(self,x1, y1, x2, y2,first_color,offset_color,sim, dir):
        return dm.FindMultiColorE(x1, y1, x2, y2,first_color,offset_color,sim, dir)

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
            "backspace": 8,
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
    def WheelDown(self):
        return dm.WheelDown()

    def KillProcess(self, process_name):
        """强制结束指定进程"""
        os.system(f'taskkill /f /im {process_name}')

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