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
            async with session.post(url, json=payload, headers=self.headers, timeout=10) as response:
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
            logger.error(f"查询用户时发生异常 ({name}#{discriminator}): {e}")
            return None

    async def delete_friendship(self, session: aiohttp.ClientSession, target_tenancy_user_id: int) -> bool:
        """
        删除好友关系
        :param session: aiohttp session
        :param target_tenancy_user_id: 目标用户的 tenancyUserId
        :return: 是否成功
        """
        url = f"{self.BASE_URL}/shared/social/friends/delete-friendship"
        payload = {
            "target_tenancy_user_id": target_tenancy_user_id
        }
        
        try:
            logger.info(f"正在删除好友关系 ID: {target_tenancy_user_id}")
            # 注意：虽然是删除操作，但根据用户提供的示例，使用的是 POST 请求
            async with session.post(url, json=payload, headers=self.headers, timeout=5) as response:
                if response.status == 200:
                    logger.info(f"删除好友成功")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"删除好友失败: HTTP {response.status} - {text}")
                    return False
            
        except Exception as e:
            logger.error(f"删除好友时发生异常: {e}")
            return False

    async def request_friendship(self, session: aiohttp.ClientSession, target_tenancy_user_id: int, retry: bool = True) -> int:
        """
        发送好友请求
        :param session: aiohttp session
        :param target_tenancy_user_id: 目标用户的 tenancyUserId
        :param retry: 是否在 409 冲突时尝试删除并重试
        :return: HTTP 状态码 (200=成功, 400=被拉黑, 409=冲突, 0=异常/其他错误)
        """
        url = f"{self.BASE_URL}/shared/social/friends/request-friendship"
        payload = {
            "target_tenancy_user_id": target_tenancy_user_id
        }
        
        try:
            logger.info(f"正在发送好友请求给 ID: {target_tenancy_user_id}")
            async with session.post(url, json=payload, headers=self.headers, timeout=5) as response:
                if response.status == 200:
                    logger.info(f"好友请求发送成功")
                    return 200
                elif response.status == 409:
                    if retry:
                        logger.warning(f"好友请求冲突 (HTTP 409)，尝试删除好友并重试: {target_tenancy_user_id}")
                        if await self.delete_friendship(session, target_tenancy_user_id):
                            logger.info(f"删除好友成功，正在重新发送请求: {target_tenancy_user_id}")
                            return await self.request_friendship(session, target_tenancy_user_id, retry=False)
                        else:
                            logger.error(f"删除好友失败，无法继续重试")
                            return 409
                    else:
                        logger.error(f"重试后仍然收到 409 冲突，放弃")
                        return 409
                elif response.status == 400:
                    logger.warning(f"好友请求失败: 被拉黑 (HTTP 400) - ID: {target_tenancy_user_id}")
                    return 400
                elif response.status == 404:
                    logger.warning(f"好友请求失败: 未知 (HTTP 404) - ID: {target_tenancy_user_id}")
                    return 404
                else:
                    text = await response.text()
                    logger.error(f"好友请求发送失败: HTTP {response.status} - {text}")
                    return response.status
            
        except Exception as e:
            logger.error(f"发送好友请求时发生异常: {e}")
            return 0

# 便捷调用函数 (Async)
async def add_friend_by_http_async(name_with_tag: str, auth_token: str, session: Optional[aiohttp.ClientSession] = None) -> int:
    """
    通过 HTTP 接口添加好友的完整流程 (Async)
    如果成功获取ID并发送请求，会调用 client.insert_data 上报数据
    :param name_with_tag: 用户名#Tag (e.g., "Player#1234")
    :param auth_token: 认证 Token
    :param session: 可选的 aiohttp session，如果提供则复用
    :return: HTTP 状态码
    """
    if '#' not in name_with_tag:
        logger.error(f"用户名格式错误，应为 'Name#Tag'")
        return 0
        
    name, discriminator = name_with_tag.split('#', 1)
    
    manager = HttpFriendManager(auth_token)
    
    # 内部辅助函数：执行核心逻辑
    async def _execute(sess: aiohttp.ClientSession) -> int:
        # 1. 获取用户 ID
        user_id = await manager.get_user_id_by_displayname(sess, name, discriminator)
        if not user_id:
            return 0
        
        # 插入数据到数据库 (User request: insert_data("arc_game", name_with_tag, str(user_id), "1", 50))
        try:
            client = ApiClient()
            # user_id is int, convert to str for database
            await client.update_data_async("arc_game", name_with_tag, str(user_id), "1", 50)
            logger.info(f"已上报好友数据: {name_with_tag}, ID: {user_id}")
        except Exception as e:
            logger.error(f"上报好友数据失败: {e}")

        # 2. 发送好友请求
        return await manager.request_friendship(sess, user_id)

    if session:
        return await _execute(session)
    else:
        async with aiohttp.ClientSession() as new_session:
            return await _execute(new_session)

async def add_friend_by_id_async(user_id: str, auth_token: str, session: Optional[aiohttp.ClientSession] = None) -> int:
    """
    通过 HTTP 接口添加好友的完整流程 (Async)
    直接使用 ID 发送请求
    :param user_id: 目标用户ID (str or int)
    :param auth_token: 认证 Token
    :param session: 可选的 aiohttp session，如果提供则复用
    :return: HTTP 状态码
    """
    manager = HttpFriendManager(auth_token)
    
    if session:
        return await manager.request_friendship(session, int(user_id))
    else:
        async with aiohttp.ClientSession() as new_session:
            return await manager.request_friendship(new_session, int(user_id))
