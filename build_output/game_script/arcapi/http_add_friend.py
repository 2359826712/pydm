import aiohttp
import asyncio
import logging
import os
import sys
from typing import Optional, Dict, Any

# 添加上一级目录以导入 api_client
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)
from api_client import ApiClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class HttpFriendManager:
    """
    HTTP 接口封装：用于通过 API 添加好友 (Async version)
    """
    BASE_URL = "https://api-gateway.europe.es-pio.net/v1"

    def __init__(self, auth_token: str):
        """
        初始化管理器
        :param auth_token: 认证 Token (Bearer Token)
        """
        # 自动处理 Bearer 前缀
        if not auth_token.startswith("Bearer "):
            self.auth_token = f"Bearer {auth_token}"
        else:
            self.auth_token = auth_token

        self.headers = {
            "Accept": "application/json",
            "Authorization": self.auth_token,
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }

    async def get_user_id_by_displayname(self, session: aiohttp.ClientSession, name: str, discriminator: str) -> Optional[int]:
        """
        通过用户名和 Tag 获取用户 ID (tenancyUserId)
        :param session: aiohttp session
        :param name: 用户名 (e.g., "MMOEXPsellitem18")
        :param discriminator: 标识符 (e.g., "0342")
        :return: tenancyUserId (int) 或 None
        """
        url = f"{self.BASE_URL}/shared/profile/by-displayname"
        payload = {
            "name": name,
            "discriminator": discriminator
        }
        
        try:
            logger.info(f"正在查询用户: {name}#{discriminator}")
            async with session.post(url, json=payload, headers=self.headers, timeout=5) as response:
                # 检查响应状态码
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"查询用户失败: HTTP {response.status} - {text}")
                    return None

                data = await response.json()
                
                # 解析返回数据
                tenancy_user_id = data.get("tenancyUserId")
                if tenancy_user_id:
                    logger.info(f"成功获取用户ID: {tenancy_user_id}")
                    return int(tenancy_user_id)
                else:
                    logger.error("响应中未找到 tenancyUserId")
                    return None
                
        except Exception as e:
            logger.error(f"查询用户时发生异常: {e}")
            return None

    async def request_friendship(self, session: aiohttp.ClientSession, target_tenancy_user_id: int) -> bool:
        """
        发送好友请求
        :param session: aiohttp session
        :param target_tenancy_user_id: 目标用户的 tenancyUserId
        :return: 是否成功
        """
        url = f"{self.BASE_URL}/shared/social/friends/request-friendship"
        payload = {
            "target_tenancy_user_id": target_tenancy_user_id
        }
        
        try:
            logger.info(f"正在发送好友请求给 ID: {target_tenancy_user_id}")
            async with session.post(url, json=payload, headers=self.headers, timeout=5) as response:
                if response.status == 200:
                    logger.info("好友请求发送成功")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"好友请求发送失败: HTTP {response.status} - {text}")
                    return False
            
        except Exception as e:
            logger.error(f"发送好友请求时发生异常: {e}")
            return False

# 便捷调用函数 (Async)
async def add_friend_by_http_async(name_with_tag: str, auth_token: str) -> bool:
    """
    通过 HTTP 接口添加好友的完整流程 (Async)
    如果成功获取ID并发送请求，会调用 client.insert_data 上报数据
    :param name_with_tag: 用户名#Tag (e.g., "Player#1234")
    :param auth_token: 认证 Token
    :return: 是否成功发送请求
    """
    if '#' not in name_with_tag:
        logger.error("用户名格式错误，应为 'Name#Tag'")
        return False
        
    name, discriminator = name_with_tag.split('#', 1)
    
    manager = HttpFriendManager(auth_token)
    
    async with aiohttp.ClientSession() as session:
        # 1. 获取用户 ID
        user_id = await manager.get_user_id_by_displayname(session, name, discriminator)
        if not user_id:
            return False
        
        # 插入数据到数据库 (User request: insert_data("arc_game", name_with_tag, str(user_id), "1", 50))
        try:
            client = ApiClient()
            # user_id is int, convert to str for database
            client.insert_data("arc_game", name_with_tag, str(user_id), "1", 50)
            logger.info(f"已上报好友数据: {name_with_tag}, ID: {user_id}")
        except Exception as e:
            logger.error(f"上报好友数据失败: {e}")

        # 2. 发送好友请求
        return await manager.request_friendship(session, user_id)

async def add_friend_by_id_async(user_id: str, auth_token: str) -> bool:
    """
    通过 HTTP 接口添加好友的完整流程 (Async)
    直接使用 ID 发送请求
    :param user_id: 目标用户ID (str or int)
    :param auth_token: 认证 Token
    :return: 是否成功发送请求
    """
    manager = HttpFriendManager(auth_token)
    
    async with aiohttp.ClientSession() as session:
        return await manager.request_friendship(session, int(user_id))

# 兼容同步调用 (但不建议在高性能场景使用，每次都会创建 loop)
def add_friend_by_http(name_with_tag: str, auth_token: str) -> bool:
    try:
        return asyncio.run(add_friend_by_http_async(name_with_tag, auth_token))
    except Exception as e:
        logger.error(f"同步调用异步函数失败: {e}")
        return False

if __name__ == "__main__":
    # 测试用例 (使用用户提供的示例 Token，注意 Token 可能已过期)
    test_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImI4MDMxYTE0ZjBmZmFiMzRlNzA3N2I5OTA2Nzg5YTkzOWI3OGRjNWEiLCJraWRfdmVyc2lvbiI6IjE3MCIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9waW9uZWVyLmVtYmFyay5uZXQiXSwiZXhwIjoxNzY2OTM1NDkxLCJleHQiOnsiYXBwX2lkIjoiMTgwODUwMCIsImNsaWVudF9pZCI6ImVtYmFyay1waW9uZWVyIiwiY29tcGFueSI6IiIsImVtYmFya191c2VyX2lkIjoiNjc0MzU2OTc3NjcxMDIwNzM1MCIsImV4dF9wcm92aWRlcl9pZCI6OCwidGVuYW5jeV9pZCI6IjYzNjg0ODU1MjQwMTQxNDk2OTQiLCJ0ZW5hbmN5X25hbWUiOiJwaW9uZWVyLWxpdmUiLCJ0cHVpZCI6Ijc2NTYxMTk4OTk1Mzg2NTc1In0sImlhdCI6MTc2Njg0OTA5MSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmVtYmFyay5uZXQvIiwianRpIjoiOTZkNzg5MTQtYzkyNy00MmQ2LTlmYTEtZDkwZDlhMTQ5MmNmIiwibmJmIjoxNzY2ODQ5MDkxLCJzY3AiOltdLCJzdWIiOiI2MDc0MzU2MzA2MzA3NjU4NTE2In0.q2Z3D5fcDoWmFJ2LvW993mC4ZZfIhljRILv3GvO8pIs_vY2XJbBn0TBFLE7B5gNwd-BkdWr5fuC1L8FwnzJjF1p344XB4zfBgItO9MPUKBT5-XYLMH4JxqlSW87_QvLQSMg54oAnyVzz2qErEBxFEasTuek8rrMATLOHpo5i5ek-Z1_4taOLkNu8PjhtI_pDfdVdRjp_oocNMiXperx7TCyth5_3f8tlAmC7JIZJONLV2r54bwKnIcAqs5ayf1EJ83dZdFMpBKdZdeVaE-jtKd0OV6kBuyC-RTWoyVTBtA__tZOt8IacBIv2sUYUohcy6RSRaCpbZivqb8Qvt3Osow"
    
    # 示例目标
    test_target = "MMOEXPsellitem18#0342"
    
    print("开始测试 HTTP 接口...")
    add_friend_by_http(test_target, test_token)
