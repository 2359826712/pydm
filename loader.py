import os
import sys
import traceback

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
    """纯粹的动态加载并运行 main.py"""
    script_path = os.path.join(BASE_PATH, "main.py")
    
    if not os.path.exists(script_path):
        print(f"错误: 找不到入口文件 {script_path}")
        input("按回车键退出...")
        return

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
    run_main_script()
