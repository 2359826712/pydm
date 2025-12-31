import os
import shutil
import PyInstaller.__main__
import time
import stat
#
def kill_process_by_name(name):
    print(f"Attempting to kill process: {name}")
    try:
        os.system(f'taskkill /f /im {name}.exe >nul 2>&1')
    except Exception as e:
        print(f"Warning: Failed to kill process {name}: {e}")
#
def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)
#
def safe_rmtree(path, retries=5, delay=1.0):
    if not os.path.exists(path):
        return
    print(f"Cleaning up {path}...")
    for i in range(retries):
        try:
            shutil.rmtree(path, onerror=remove_readonly)
            return
        except OSError as e:
            if i == retries - 1:
                try:
                    trash_name = f"{path}_trash_{int(time.time())}"
                    print(f"Deletion failed, attempting to rename to {trash_name}...")
                    os.rename(path, trash_name)
                    return
                except OSError as rename_error:
                    print(f"Rename also failed: {rename_error}")
                    raise e
            print(f"Cleanup failed ({e}), retrying in {delay}s...")
            time.sleep(delay)
#
def build():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_dir, 'dist')
    output_dir = os.path.join(project_dir, 'build_output')
    exe_dir = os.path.join(output_dir, 'game_script')
    loader_path = os.path.join(src_dir, 'loader.py')
    need_build = True
    kill_process_by_name("game_script")
    kill_process_by_name("ocr_server")
    time.sleep(1)
    if need_build:
        try:
            safe_rmtree(output_dir)
        except Exception as e:
            print(f"Could not clean output directory {output_dir}: {e}")
            timestamp = int(time.time())
            output_dir = os.path.join(project_dir, f'build_output_{timestamp}')
            print(f"Switching to new output directory: {output_dir}")
            if os.path.exists(output_dir):
                safe_rmtree(output_dir)
        # 清理临时构建目录，避免文件被占用
        work_dir = os.path.join(project_dir, 'build_work')
        spec_dir = os.path.join(project_dir, 'build_spec')
        try:
            safe_rmtree(work_dir)
        except Exception as e:
            print(f"Warning: could not clean work dir {work_dir}: {e}")
        try:
            safe_rmtree(spec_dir)
        except Exception as e:
            print(f"Warning: could not clean spec dir {spec_dir}: {e}")
        args = [
            loader_path,
            '--name=game_script',
            '--onedir',
            '--noconfirm',
            '--distpath', output_dir,
            '--workpath', work_dir,
            '--specpath', spec_dir,
            '--exclude-module=action',
            '--exclude-module=arcapi',
            '--hidden-import=win32com.client',
            '--hidden-import=win32gui',
            '--hidden-import=keyboard',
            '--hidden-import=py_trees',
            '--hidden-import=functools',
            '--hidden-import=traceback',
            '--hidden-import=win32process',
            '--hidden-import=pythoncom',
            '--hidden-import=requests',
            '--hidden-import=pyautogui',
            '--hidden-import=pyperclip',
            '--hidden-import=concurrent.futures',
            '--hidden-import=aiohttp',
            '--hidden-import=asyncio',
            '--hidden-import=sqlite3',
            '--hidden-import=calendar',
            '--hidden-import=multiprocessing',
            '--hidden-import=threading',
            '--hidden-import=ctypes',
            '--hidden-import=configparser',
            '--hidden-import=pathlib',
            '--hidden-import=base64',
            '--hidden-import=io',
            '--hidden-import=json',
            '--hidden-import=datetime',
            '--hidden-import=re',
            '--hidden-import=typing',
            '--hidden-import=logging',
            '--clean',
            '--noconfirm',
        ]
        print("Running PyInstaller...")
        PyInstaller.__main__.run(args)
    else:
        print("Skip packaging: dist/loader.py unchanged")
    print("Copying external resources...")
    #
    # 确保输出根目录存在（即使跳过打包也复制资源）
    if not os.path.exists(exe_dir):
        os.makedirs(exe_dir, exist_ok=True)
    #
    dirs_to_copy = ['action', 'arcapi', 'pic','python_server']
    for d in dirs_to_copy:
        src = os.path.join(src_dir, d)
        dst = os.path.join(exe_dir, d)
        if os.path.exists(src):
            if os.path.exists(dst):
                safe_rmtree(dst)
            shutil.copytree(src, dst)
            print(f"Copied {d}")
            pycache = os.path.join(dst, '__pycache__')
            if os.path.exists(pycache):
                safe_rmtree(pycache)
    #
    files_to_copy = []
    for f in os.listdir(src_dir):
        if f.endswith('.dll') or f.endswith('.txt') or f == 'ocr_server.exe':
            files_to_copy.append(f)
    # 主入口脚本复制到可执行同级目录
    main_src = os.path.join(src_dir, 'main.py')
    if os.path.exists(main_src):
        files_to_copy.append('main.py')
    #
    if os.path.exists(os.path.join(project_dir, 'dm.dll')):
        shutil.copy2(os.path.join(project_dir, 'dm.dll'), os.path.join(exe_dir, 'dm.dll'))
        print("Copied dm.dll from project root")
    #
    for f in files_to_copy:
        src = os.path.join(src_dir, f)
        dst = os.path.join(exe_dir, f)
        shutil.copy2(src, dst)
        print(f"Copied {f}")
    #
    print("Build complete. Output in:", exe_dir)
#
if __name__ == "__main__":
    build()
