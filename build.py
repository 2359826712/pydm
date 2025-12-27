import os
import shutil
import PyInstaller.__main__

def build():
    # Define paths
    project_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_dir, 'dist')
    output_dir = os.path.join(project_dir, 'build_output')
    
    # Clean previous build
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
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
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"Copied {d}")
            
            # Clean __pycache__ from destination
            pycache = os.path.join(dst, '__pycache__')
            if os.path.exists(pycache):
                shutil.rmtree(pycache)

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
