import os
import sys
import traceback
import subprocess
import atexit
import time
try:
    import requests
except ImportError:
    # 如果没有 requests，为了避免崩溃，可以后续禁用 OCR 检查
    requests = None

# 获取当前运行目录（兼容 exe 和 py 运行方式）
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，使用 exe 所在目录
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行，使用脚本所在目录
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# 设置工作目录为当前目录
os.chdir(BASE_PATH)

def run_main_script():
    """纯粹的动态加载并运行 dist/main.py"""
    # 目标脚本路径：exe所在目录同级的 main.py
    script_path = os.path.join(BASE_PATH, "main.py")
    
    if not os.path.exists(script_path):
        print(f"错误: 找不到入口文件 {script_path}")
        print(f"请确保 main.py 文件夹位于: {BASE_PATH}")
        input("按回车键退出...")
        return

    # 将 main.py 所在目录加入 sys.path，这样其 import 能找到同级模块
    main_dir = os.path.dirname(script_path)
    if main_dir not in sys.path:
        sys.path.insert(0, main_dir)

    try:
        # 读取脚本内容
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 准备全局变量环境
        # 传递 __file__ 和 __name__ 让脚本感觉像是在直接运行
        global_vars = {
            '__file__': script_path,
            '__name__': '__main__',
            'BASE_PATH': BASE_PATH
        }
        
        # 动态执行代码
        exec(code, global_vars)
        
    except Exception:
        print("-" * 50)
        print("脚本运行发生异常:")
        traceback.print_exc()
        print("-" * 50)
        input("按回车键退出...")

if __name__ == "__main__":
    import multiprocessing
    is_main_process = multiprocessing.current_process().name == "MainProcess"
    if is_main_process:
        ocr_exe_path = os.path.join(BASE_PATH, "ocr_server.exe")
        alt_path = os.path.join(BASE_PATH, "ocr_server.exe")
        if os.path.exists(alt_path):
            ocr_exe_path = alt_path
        
        if os.path.exists(ocr_exe_path):
            print(f"正在启动 OCR 服务: {ocr_exe_path} ...")
            try:
                # 启动 OCR 服务，不显示窗口 (CREATE_NO_WINDOW=0x08000000)
                if os.name == 'nt':
                    process = subprocess.Popen([ocr_exe_path], creationflags=0x08000000)
                else:
                    process = subprocess.Popen([ocr_exe_path])
                
                # 注册退出时的清理函数
                def kill_ocr():
                    try:
                        print("关闭 OCR 服务...")
                        process.terminate()
                    except:
                        pass
                atexit.register(kill_ocr)
                
                # 健康检查
                if requests:
                    print("等待 OCR 服务启动...", end="", flush=True)
                    ocr_ready = False
                    for _ in range(10): # 尝试 10 次，每次 1 秒
                        try:
                            r = requests.get("http://127.0.0.1:5000/ping", timeout=1)
                            if r.status_code == 200:
                                ocr_ready = True
                                print(" 成功!")
                                break
                        except:
                            pass
                        print(".", end="", flush=True)
                        time.sleep(1)
                    
                    if not ocr_ready:
                        print("\n警告: OCR 服务启动超时，可能无法使用 OCR 功能。")
                else:
                    print("\n提示: 缺少 requests 库，跳过 OCR 服务健康检查。")
                    
            except Exception as e:
                print(f"\n启动 OCR 服务失败: {e}")
        else:
            print(f"警告: 未找到 {ocr_exe_path}，OCR 功能将不可用")
        
        run_main_script()
    else:
        # 子进程：不重复启动 OCR，也不重复执行主脚本
        pass
