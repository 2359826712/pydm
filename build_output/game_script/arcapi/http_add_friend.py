import requests
import json
import logging
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class HttpFriendManager:
    """
    HTTP 接口封装：用于通过 API 添加好友
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

    def get_user_id_by_displayname(self, name: str, discriminator: str) -> Optional[int]:
        """
        通过用户名和 Tag 获取用户 ID (tenancyUserId)
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
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            # 检查响应状态码
            if response.status_code != 200:
                logger.error(f"查询用户失败: HTTP {response.status_code} - {response.text}")
                return None

            data = response.json()
            # logger.info(f"查询响应: {data}")
            
            # 解析返回数据
            # 示例返回: {"tenancyUserId": 8959208161866405348, ...}
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

    def request_friendship(self, target_tenancy_user_id: int) -> bool:
        """
        发送好友请求
        :param target_tenancy_user_id: 目标用户的 tenancyUserId
        :return: 是否成功
        """
        url = f"{self.BASE_URL}/shared/social/friends/request-friendship"
        payload = {
            "target_tenancy_user_id": target_tenancy_user_id
        }
        
        try:
            logger.info(f"正在发送好友请求给 ID: {target_tenancy_user_id}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("好友请求发送成功")
                return True
            else:
                logger.error(f"好友请求发送失败: HTTP {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"发送好友请求时发生异常: {e}")
            return False

# 便捷调用函数
def add_friend_by_http(name_with_tag: str, auth_token: str) -> bool:
    """
    通过 HTTP 接口添加好友的完整流程
    :param name_with_tag: 用户名#Tag (e.g., "Player#1234")
    :param auth_token: 认证 Token
    :return: 是否成功发送请求
    """
    if '#' not in name_with_tag:
        logger.error("用户名格式错误，应为 'Name#Tag'")
        return False
        
    name, discriminator = name_with_tag.split('#', 1)
    
    manager = HttpFriendManager(auth_token)
    
    # 1. 获取用户 ID
    user_id = manager.get_user_id_by_displayname(name, discriminator)
    if not user_id:
        return False
        
    # 2. 发送好友请求
    return manager.request_friendship(user_id)

if __name__ == "__main__":
    # 测试用例 (使用用户提供的示例 Token，注意 Token 可能已过期)
    test_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImI4MDMxYTE0ZjBmZmFiMzRlNzA3N2I5OTA2Nzg5YTkzOWI3OGRjNWEiLCJraWRfdmVyc2lvbiI6IjE3MCIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9waW9uZWVyLmVtYmFyay5uZXQiXSwiZXhwIjoxNzY2OTM1NDkxLCJleHQiOnsiYXBwX2lkIjoiMTgwODUwMCIsImNsaWVudF9pZCI6ImVtYmFyay1waW9uZWVyIiwiY29tcGFueSI6IiIsImVtYmFya191c2VyX2lkIjoiNjc0MzU2OTc3NjcxMDIwNzM1MCIsImV4dF9wcm92aWRlcl9pZCI6OCwidGVuYW5jeV9pZCI6IjYzNjg0ODU1MjQwMTQxNDk2OTQiLCJ0ZW5hbmN5X25hbWUiOiJwaW9uZWVyLWxpdmUiLCJ0cHVpZCI6Ijc2NTYxMTk4OTk1Mzg2NTc1In0sImlhdCI6MTc2Njg0OTA5MSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmVtYmFyay5uZXQvIiwianRpIjoiOTZkNzg5MTQtYzkyNy00MmQ2LTlmYTEtZDkwZDlhMTQ5MmNmIiwibmJmIjoxNzY2ODQ5MDkxLCJzY3AiOltdLCJzdWIiOiI2MDc0MzU2MzA2MzA3NjU4NTE2In0.q2Z3D5fcDoWmFJ2LvW993mC4ZZfIhljRILv3GvO8pIs_vY2XJbBn0TBFLE7B5gNwd-BkdWr5fuC1L8FwnzJjF1p344XB4zfBgItO9MPUKBT5-XYLMH4JxqlSW87_QvLQSMg54oAnyVzz2qErEBxFEasTuek8rrMATLOHpo5i5ek-Z1_4taOLkNu8PjhtI_pDfdVdRjp_oocNMiXperx7TCyth5_3f8tlAmC7JIZJONLV2r54bwKnIcAqs5ayf1EJ83dZdFMpBKdZdeVaE-jtKd0OV6kBuyC-RTWoyVTBtA__tZOt8IacBIv2sUYUohcy6RSRaCpbZivqb8Qvt3Osow"
    
    # 示例目标
    test_target = "MMOEXPsellitem18#0342"
    
    print("开始测试 HTTP 接口...")
    add_friend_by_http(test_target, test_token)
