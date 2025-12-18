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
    'dist/main.py',
    '--name=game_script',
    '--onedir',
    '--distpath=' + dist_path,
    '--workpath=' + work_path,
    '--paths=dist',
    '--paths=dist/arcapi',  # 添加 dist/arcapi 到搜索路径，以便能找到 arcapi.py 作为模块
    '--clean',
    '--noconfirm',
    # '--windowed', # 如果不需要控制台窗口取消注释
])

# 复制资源文件
exe_dir = os.path.join(dist_path, 'game_script')

# 1. 复制 dm.dll
if os.path.exists("dm.dll"):
    shutil.copy("dm.dll", os.path.join(exe_dir, "dm.dll"))
    print("Copied dm.dll")
else:
    print("Warning: dm.dll not found in root")

# 2. 复制 pic 文件夹
pic_src = os.path.join("dist", "pic")
pic_dst = os.path.join(exe_dir, "pic")
if os.path.exists(pic_src):
    shutil.copytree(pic_src, pic_dst)
    print("Copied pic folder")
else:
    print("Warning: dist/pic not found")

print(f"Build complete. Executable is in {exe_dir}")
