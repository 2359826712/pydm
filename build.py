import PyInstaller.__main__
import shutil
import os

# 定义输出目录
dist_path = "build_exe"
work_path = "build_temp"

# 清理旧构建
if os.path.exists(dist_path):
    shutil.rmtree(dist_path)
if os.path.exists(work_path):
    shutil.rmtree(work_path)

# 运行 PyInstaller
PyInstaller.__main__.run([
    'loader.py',  # 入口改为 loader.py
    '--name=game_script',
    '--onedir',
    '--distpath=' + dist_path,
    '--workpath=' + work_path,
    '--paths=dist',
    '--paths=dist/arcapi',
    '--clean',
    '--noconfirm',
    '--hidden-import=win32com',
    '--hidden-import=win32com.client',
    '--hidden-import=pythoncom',
    '--hidden-import=py_trees',  # 添加 py_trees
    '--hidden-import=arcapi',    # 添加 arcapi
    '--hidden-import=keyboard',  # 添加 keyboard
    '--hidden-import=threading', # 添加 threading
    # '--windowed', # 如果不需要控制台窗口取消注释
])

# 复制资源文件
exe_dir = os.path.join(dist_path, 'game_script')

# 0. 复制 dist 目录下的源码到 exe 目录（除了 arcapi 和 action，它们在 loader 中动态加载，但也需要源码存在）
# 实际上 loader.py 是为了加载 main.py，而 main.py 依赖其他模块。
# 如果我们使用 loader 模式，通常是为了热更新或动态修改脚本。
# 所以我们需要把 dist 目录下的所有 python 源码复制到 exe 目录中。

dist_src = "dist"
if os.path.exists(dist_src):
    # 复制 dist 目录下的内容到 exe_dir/dist (或者直接放在 exe_dir 下，取决于 loader 怎么找)
    # 看 loader.py 的逻辑： script_path = os.path.join(BASE_PATH, "main.py")
    # 这意味着 main.py 应该在 exe 同级目录下。
    # 而原来的结构是 dist/main.py。
    
    # 让我们把 dist 目录下的内容直接复制到 exe_dir 下
    for item in os.listdir(dist_src):
        s = os.path.join(dist_src, item)
        d = os.path.join(exe_dir, item)
        if os.path.isdir(s):
            # 如果是 pic 文件夹，下面会有专门的处理逻辑（虽然重复了，但 shutil.copytree 默认不能覆盖）
            # 我们先跳过 pic，或者使用 dirs_exist_ok=True (Python 3.8+)
            if item == "pic":
                continue
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print("Copied source files from dist to exe dir")
else:
    print("Warning: dist folder not found")

# 1. 复制 dm.dll

# 1. 复制 dm.dll
if os.path.exists("dm.dll"):
    shutil.copy("dm.dll", os.path.join(exe_dir, "dm.dll"))
    print("Copied dm.dll")
else:
    print("Warning: dm.dll not found in root")

# 2. 复制 pic 文件夹
# 上面已经复制了 dist 下的所有内容，如果 pic 在 dist 下，那么这里可能已经复制过了。
# 但为了保险起见（且上面的逻辑跳过了 pic），这里保留。
pic_src = os.path.join("dist", "pic")
pic_dst = os.path.join(exe_dir, "pic")
if os.path.exists(pic_src):
    if os.path.exists(pic_dst):
        shutil.rmtree(pic_dst) # 确保覆盖
    shutil.copytree(pic_src, pic_dst)
    print("Copied pic folder")
else:
    print("Warning: dist/pic not found")

print(f"Build complete. Executable is in {exe_dir}")
