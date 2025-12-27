import ctypes
import os
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
    def __init__(self, dll_path: Optional[str] = None):
        """
        初始化管理器
        :param dll_path: arc.dll 的路径，不传则自动搜索常见路径
        """
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

    def close(self) -> None:
        """清理资源（卸载 DLL）"""
        if self.dll:
            # 注意：ctypes 会自动管理 DLL 卸载，这里主要是标记状态
            self._is_loaded = False
            logger.info("已清理 GameManager 资源")

    def __del__(self):
        """析构函数：确保资源释放"""
        self.close()

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
            friend_list = gm.get_friend_list()
            print(f"\n===== 好友列表（共 {len(friend_list)} 个） =====")
            for idx, friend in enumerate(friend_list):
                print(f"[{idx+1}] ID: {friend['id']} | 名称: {friend['name']} | 唯一标识: {friend['unique_id']}")
    except FileNotFoundError as e:
        logger.error(f"DLL 加载失败: {e}")
    except Exception as e:
        logger.error(f"程序异常: {e}")