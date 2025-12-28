import ctypes
import os
import sys
import threading
from typing import List, Optional, Dict
import logging

# 配置日志（便于调试和问题定位）
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --------------------------
# 对应 C++ 端的结构体定义
# --------------------------
class FriendInfo(ctypes.Structure):
    """对应 C++ 端的 FriendInfo 结构体"""
    _fields_ = [
        ("id_utf8", ctypes.c_char * 64),       # 好友ID（UTF-8）
        ("name_utf8", ctypes.c_char * 128),    # 好友名称（UTF-8，格式：前缀#后缀）
        ("friend_ptr", ctypes.c_uint64),       # 原始指针（调试用）
        ("unique_id", ctypes.c_uint64)         # 唯一标识（去重用）
    ]

class FriendListResult(ctypes.Structure):
    """对应 C++ 端的 FriendListResult 结构体"""
    _fields_ = [
        ("count", ctypes.c_int),               # 有效好友数量
        ("data", ctypes.POINTER(FriendInfo)),  # 好友数据数组指针
        ("buffer_size", ctypes.c_uint64)       # 缓冲区总大小
    ]

# --------------------------
# 游戏管理核心类
# --------------------------
class ArcGameManager:
    """
    封装 arc.dll 的游戏管理类（移除驱动加载逻辑）
    核心功能：
    1. 加载/卸载 DLL
    2. 调用 GameCore_TraverseFriendList 获取好友列表
    3. 自动管理 C++ 端分配的内存，避免内存泄漏
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ArcGameManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, dll_path: Optional[str] = None):
        """
        初始化管理器
        :param dll_path: arc.dll 的路径，不传则自动搜索常见路径
        """
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.dll: Optional[ctypes.CDLL] = None
        self._dll_path: str = ""
        self._is_loaded: bool = False

        # 初始化 DLL 路径
        if not dll_path:
            self._dll_path = self._search_dll_path()
        else:
            self._dll_path = os.path.abspath(dll_path)

        # 加载 DLL 并设置函数签名
        self._load_dll()
        self._setup_functions()
        self.load_driver()
        
        self._initialized = True

    def _search_dll_path(self) -> str:
        """自动搜索 arc.dll 的常见路径"""
        search_paths = [
            # 当前目录
            "arc.dll",
            # 编译输出目录
            os.path.join("x64", "Debug", "arc.dll"),
            os.path.join("x64", "Release", "arc.dll"),
            # 脚本所在目录的子目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "arc.dll"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "arc.dll"), # Added parent directory search
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "x64", "Debug", "arc.dll"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "x64", "Release", "arc.dll"),
            # 你提供的示例路径
            "E:\\project\\arc\\Release\\arc.dll"
        ]

        for path in search_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                logger.info(f"自动找到 DLL: {abs_path}")
                return abs_path

        raise FileNotFoundError("未找到 arc.dll，请指定正确的 DLL 路径")

    def _load_dll(self) -> None:
        """加载 arc.dll"""
        try:
            if not os.path.exists(self._dll_path):
                raise FileNotFoundError(f"DLL 文件不存在: {self._dll_path}")

            # 尝试添加 DLL 目录到搜索路径 (Python 3.8+ Windows)
            if hasattr(os, 'add_dll_directory'):
                dll_dir = os.path.dirname(self._dll_path)
                try:
                    os.add_dll_directory(dll_dir)
                    logger.info(f"已添加 DLL 搜索目录: {dll_dir}")
                except Exception as e:
                    logger.warning(f"无法添加 DLL 搜索目录 {dll_dir}: {e}")
                
                # 如果是打包环境，还需要添加 _internal 目录(包含VC运行库等依赖)
                if getattr(sys, 'frozen', False):
                    # 获取 exe 所在目录
                    exe_dir = os.path.dirname(sys.executable)
                    
                    # 尝试添加 _internal (PyInstaller 6+)
                    internal_dir = os.path.join(exe_dir, '_internal')
                    if os.path.exists(internal_dir):
                        try:
                            os.add_dll_directory(internal_dir)
                            logger.info(f"已添加依赖搜索目录: {internal_dir}")
                        except Exception:
                            pass
                    
                    # 尝试添加 exe 目录本身
                    if exe_dir != dll_dir:
                        try:
                            os.add_dll_directory(exe_dir)
                        except Exception:
                            pass

            # 使用 kernel32.LoadLibraryW 绕过 PyInstaller 的 hook
            # PyInstaller 会 hook ctypes.cdll.LoadLibrary 并尝试在内部路径查找，导致外部 DLL 加载失败
            try:
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                h_module = kernel32.LoadLibraryW(self._dll_path)
                if not h_module:
                    err = ctypes.get_last_error()
                    raise OSError(f"WinAPI LoadLibraryW failed with error code: {err}")
                
                # 使用句柄创建 CDLL 对象
                self.dll = ctypes.CDLL(self._dll_path, handle=h_module)
            except Exception as load_err:
                logger.warning(f"kernel32.LoadLibraryW 方式加载失败 ({load_err})，尝试直接加载...")
                # 回退到普通加载方式
                self.dll = ctypes.cdll.LoadLibrary(self._dll_path)

            self._is_loaded = True
            logger.info(f"成功加载 DLL: {self._dll_path}")

        except Exception as e:
            logger.error(f"加载 DLL 失败: {e}")
            raise

    def _setup_functions(self) -> None:
        """设置 DLL 导出函数的签名（关键：保证参数/返回值类型匹配）"""
        if not self.dll:
            raise RuntimeError("DLL 未加载，无法设置函数签名")

        # 1. GameCore_TraverseFriendList: void* __stdcall GameCore_TraverseFriendList()
        try:
            self.dll.GameCore_TraverseFriendList.argtypes = []
            self.dll.GameCore_TraverseFriendList.restype = ctypes.POINTER(FriendListResult)
            logger.info("设置 GameCore_TraverseFriendList 函数签名成功")
        except AttributeError:
            logger.error("DLL 中未找到 GameCore_TraverseFriendList 函数")
            raise

        # 2. GameCore_FreeFriendListResult: void __stdcall GameCore_FreeFriendListResult(FriendListResult* result)
        try:
            self.dll.GameCore_FreeFriendListResult.argtypes = [ctypes.POINTER(FriendListResult)]
            self.dll.GameCore_FreeFriendListResult.restype = None
            logger.info("设置 GameCore_FreeFriendListResult 函数签名成功")
        except AttributeError:
            logger.error("DLL 中未找到 GameCore_FreeFriendListResult 函数")
            raise

        # 3. GameCore_AddFriend: bool __stdcall GameCore_AddFriend(const char* name, const char* id)
        try:
            self.dll.GameCore_AddFriend.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            self.dll.GameCore_AddFriend.restype = ctypes.c_bool
            logger.info("设置 GameCore_AddFriend 函数签名成功")
        except AttributeError:
            logger.error("DLL 中未找到 GameCore_AddFriend 函数")
            raise

        # 4. GameCore_InitGameData: void __stdcall GameCore_InitGameData()
        try:
            self.dll.GameCore_InitGameData.argtypes = []
            self.dll.GameCore_InitGameData.restype = None
            logger.info("设置 GameCore_InitGameData 函数签名成功")
        except AttributeError:
            logger.warning("DLL 中未找到 GameCore_InitGameData 函数 (如果是旧版 DLL 可忽略)")

        # 5. GameCore_CleanupGameData: void __stdcall GameCore_CleanupGameData()
        try:
            self.dll.GameCore_CleanupGameData.argtypes = []
            self.dll.GameCore_CleanupGameData.restype = None
            logger.info("设置 GameCore_CleanupGameData 函数签名成功")
        except AttributeError:
            logger.warning("DLL 中未找到 GameCore_CleanupGameData 函数 (如果是旧版 DLL 可忽略)")

        # 6. GameCore_LoadDriver: bool __stdcall GameCore_LoadDriver()
        try:
            self.dll.GameCore_LoadDriver.argtypes = []
            self.dll.GameCore_LoadDriver.restype = ctypes.c_bool
            logger.info("设置 GameCore_LoadDriver 函数签名成功")
        except AttributeError:
            logger.warning("DLL 中未找到 GameCore_LoadDriver 函数")

    def get_friend_list(self) -> List[Dict[str, any]]:
        """
        核心接口：调用 GameCore_TraverseFriendList 获取好友列表
        :return: 解析后的好友列表（字典格式，便于使用）
                 字典字段：id, name, friend_ptr, unique_id
        """
        if not self._is_loaded:
            raise RuntimeError("DLL 未加载，无法获取好友列表")

        friends = []
        result_ptr = None

        try:
            # 1. 调用 C++ 函数获取结果指针
            logger.info("开始调用 GameCore_TraverseFriendList 获取好友列表...")
            result_ptr = self.dll.GameCore_TraverseFriendList()

            if not result_ptr:
                logger.warning("调用 GameCore_TraverseFriendList 返回空指针")
                return friends

            # 2. 解析结果结构体
            result = result_ptr.contents
            logger.info(f"获取到 {result.count} 个好友，缓冲区大小: {result.buffer_size} bytes")

            if result.count <= 0 or not result.data:
                logger.info("未找到有效好友数据")
                return friends

            # 3. 遍历好友数据并解析
            for i in range(result.count):
                friend_info = result.data[i]
                
                # 解码 UTF-8 字符串（处理空值和截断）
                friend_id = friend_info.id_utf8.decode("utf-8", errors="replace").rstrip("\x00")
                friend_name = friend_info.name_utf8.decode("utf-8", errors="replace").rstrip("\x00")

                # 封装为字典（便于使用）
                friend_dict = {
                    "id": friend_id,
                    "name": friend_name,
                    "friend_ptr": hex(friend_info.friend_ptr),  # 转16进制字符串
                    "unique_id": hex(friend_info.unique_id)    # 转16进制字符串
                }
                friends.append(friend_dict)
                logger.debug(f"解析好友 [{i}]: {friend_dict}")

            return friends

        except Exception as e:
            logger.error(f"解析好友列表异常: {e}")
            return friends

        finally:
            # 4. 必须释放 C++ 端分配的内存（避免内存泄漏）
            if result_ptr:
                logger.info("释放好友列表内存...")
                self.dll.GameCore_FreeFriendListResult(result_ptr)

    def add_friend(self, name: str, friend_id: str) -> bool:
        """
        调用 GameCore_AddFriend 添加好友
        :param name: 好友名称
        :param friend_id: 好友ID
        :return: 添加是否成功
        """
        if not self._is_loaded:
            raise RuntimeError("DLL 未加载，无法添加好友")

        try:
            # 确保传入的是 UTF-8 编码的字节串
            name_bytes = name.encode("utf-8")
            id_bytes = friend_id.encode("utf-8")

            logger.info(f"正在添加好友: Name={name}, ID={friend_id}")
            result = self.dll.GameCore_AddFriend(name_bytes, id_bytes)
            
            if result:
                logger.info("添加好友成功")
            else:
                logger.warning("添加好友失败")
            
            return result

        except Exception as e:
            logger.error(f"添加好友异常: {e}")
            return False

    def init_game_data(self) -> None:
        """初始化游戏数据"""
        if not self._is_loaded:
            raise RuntimeError("DLL 未加载")
        
        try:
            if hasattr(self.dll, 'GameCore_InitGameData'):
                self.dll.GameCore_InitGameData()
                logger.info("已调用 GameCore_InitGameData")
            else:
                logger.warning("GameCore_InitGameData 不存在，跳过初始化")
        except Exception as e:
            logger.error(f"初始化游戏数据异常: {e}")

    def cleanup_game_data(self) -> None:
        """清理游戏数据"""
        if not self._is_loaded:
            return

        try:
            if hasattr(self.dll, 'GameCore_CleanupGameData'):
                self.dll.GameCore_CleanupGameData()
                logger.info("已调用 GameCore_CleanupGameData")
        except Exception as e:
            logger.error(f"清理游戏数据异常: {e}")

    def load_driver(self) -> bool:
        """
        调用 GameCore_LoadDriver 加载驱动
        :return: 加载是否成功
        """
        if not self._is_loaded:
            raise RuntimeError("DLL 未加载")
        
        try:
            if hasattr(self.dll, 'GameCore_LoadDriver'):
                logger.info("开始加载驱动...")
                result = self.dll.GameCore_LoadDriver()
                if result:
                    logger.info("驱动加载成功")
                else:
                    logger.error("驱动加载失败")
                return result
            else:
                logger.error("GameCore_LoadDriver 不存在")
                return False
        except Exception as e:
            logger.error(f"加载驱动异常: {e}")
            return False

    def close(self) -> None:
        """释放资源"""
        self.cleanup_game_data()

    def __del__(self):
        """析构函数：确保资源释放"""

# --------------------------
# 上下文管理器（可选，更优雅的资源管理）
# --------------------------
class ArcGameManagerContext:
    def __init__(self, dll_path: Optional[str] = None):
        self.dll_path = dll_path
        self.manager: Optional[ArcGameManager] = None

    def __enter__(self) -> ArcGameManager:
        self.manager = ArcGameManager(self.dll_path)
        return self.manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.manager:
            self.manager.close()
        if exc_val:
            logger.error(f"GameManager 上下文异常: {exc_val}")
        return False

# --------------------------
# 测试示例
# --------------------------
if __name__ == "__main__":
    # 方式1：普通调用
    # try:
    #     # 初始化管理器（自动搜索 DLL）
    #     gm = ArcGameManager()
    #     # 获取好友列表
    #     friend_list = gm.get_friend_list()
    #     # 打印结果
    #     print(f"\n===== 好友列表（共 {len(friend_list)} 个） =====")
    #     for idx, friend in enumerate(friend_list):
    #         print(f"[{idx+1}] ID: {friend['id']} | 名称: {friend['name']} | 唯一标识: {friend['unique_id']}")
    #     # 清理资源
    #     gm.close()
    # except Exception as e:
    #     logger.error(f"测试失败: {e}")

    # 方式2：上下文管理器（推荐，自动管理资源）
    try:
        with ArcGameManagerContext() as gm:
            gm.init_game_data()
            friend_list = gm.get_friend_list()
            print(f"\n===== 好友列表（共 {len(friend_list)} 个） =====")
            for idx, friend in enumerate(friend_list):
                print(f"[{idx+1}] ID: {friend['id']} | 名称: {friend['name']} | 唯一标识: {friend['unique_id']}")

            #死循环 每一秒打印打印当前时间
            import time
            while True:
                print(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                time.sleep(1)
    except FileNotFoundError as e:
        logger.error(f"DLL 加载失败: {e}")
    except Exception as e:
        logger.error(f"程序异常: {e}")