import os
import shutil
import PyInstaller.__main__
import time
import stat
# import psutil

def kill_process_by_name(name):
    print(f"Attempting to kill process: {name}")
    try:
        # 使用 Windows 自带的 taskkill 命令，不依赖 psutil
        os.system(f'taskkill /f /im {name}.exe >nul 2>&1')
    except Exception as e:
        print(f"Warning: Failed to kill process {name}: {e}")

def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)

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
                # If deletion fails, try to rename it to a trash folder
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

def build():
    # Kill existing instances
    kill_process_by_name("game_script")
    time.sleep(1) # Wait for release

    # Define paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_dir, 'dist')
    output_dir = os.path.join(project_dir, 'build_output')
    
    # Clean previous build
    try:
        safe_rmtree(output_dir)
    except Exception as e:
        print(f"Could not clean output directory {output_dir}: {e}")
        # Use a new directory
        timestamp = int(time.time())
        output_dir = os.path.join(project_dir, f'build_output_{timestamp}')
        print(f"Switching to new output directory: {output_dir}")
        if os.path.exists(output_dir):
             safe_rmtree(output_dir)
        
    # PyInstaller arguments
    # We exclude 'action' and 'arcapi' to keep them as external source files
    args = [
        os.path.join(src_dir, 'main.py'),
        '--name=game_script',
        '--onedir',
        '--noconfirm',
        '--distpath', output_dir,
        '--workpath', os.path.join(project_dir, 'build_work'),
        '--specpath', os.path.join(project_dir, 'build_spec'),
        '--exclude-module=action',
        '--exclude-module=arcapi',
        '--hidden-import=win32com.client',
        '--hidden-import=win32gui',
        '--hidden-import=win32process',
        '--hidden-import=pythoncom',
        '--hidden-import=requests',
        '--hidden-import=concurrent.futures',
        '--hidden-import=aiohttp',
        '--hidden-import=asyncio',
    ]
    
    print("Running PyInstaller...")
    PyInstaller.__main__.run(args)
    
    # Post-build copy
    exe_dir = os.path.join(output_dir, 'game_script')
    
    print("Copying external resources...")
    
    # Copy directories
    dirs_to_copy = ['action', 'arcapi', 'pic']
    for d in dirs_to_copy:
        src = os.path.join(src_dir, d)
        dst = os.path.join(exe_dir, d)
        if os.path.exists(src):
            # For action and arcapi, we want to copy the python source files
            # For pic, we copy images
            if os.path.exists(dst):
                safe_rmtree(dst)
            shutil.copytree(src, dst)
            print(f"Copied {d}")
            
            # Clean __pycache__ from destination
            pycache = os.path.join(dst, '__pycache__')
            if os.path.exists(pycache):
                safe_rmtree(pycache)

    # Copy files
    files_to_copy = []
    for f in os.listdir(src_dir):
        if f.endswith('.dll') or f.endswith('.txt'):
            files_to_copy.append(f)
            
    # Check for dm.dll in project root
    if os.path.exists(os.path.join(project_dir, 'dm.dll')):
         shutil.copy2(os.path.join(project_dir, 'dm.dll'), os.path.join(exe_dir, 'dm.dll'))
         print("Copied dm.dll from project root")

    for f in files_to_copy:
        src = os.path.join(src_dir, f)
        dst = os.path.join(exe_dir, f)
        shutil.copy2(src, dst)
        print(f"Copied {f}")

    print("Build complete. Output in:", exe_dir)

if __name__ == "__main__":
    build()
