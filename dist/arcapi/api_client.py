import json
import asyncio
import aiohttp
from typing import Tuple, Dict, Any, Optional

class ApiClient:
    def __init__(self, server_url: str = "http://192.168.20.81:9096"):
        self.server_url = server_url.rstrip("/")

    def _build_url(self, endpoint: str) -> str:
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return self.server_url + endpoint

    async def _send_post_request_async(self, endpoint: str, data: dict) -> Tuple[int, Dict[str, Any]]:
        url = self._build_url(endpoint)
        headers = {"Content-Type": "application/json"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, timeout=10) as response:
                    text = await response.text()
                    status_code = response.status
                    
                    try:
                        parsed = json.loads(text) if text else {}
                    except json.JSONDecodeError as e:
                        parsed = {"raw_text": text, "parse_error": str(e)}
                        
                    return status_code, parsed
                    
        except asyncio.TimeoutError:
            return 408, {"error": "Request timed out"}
        except Exception as e:
            return 0, {"error": str(e)}

    # 保留同步接口用于兼容旧代码，但底层调用异步方法
    def send_post_request(self, endpoint: str, data: dict) -> Tuple[int, Dict[str, Any]]:
        try:
            return asyncio.run(self._send_post_request_async(endpoint, data))
        except RuntimeError:
            # 如果已经在事件循环中（例如在 run_in_executor 中），则创建一个新循环或直接报错是不行的
            # 但由于我们主要在 invite.py 中改为全异步，这里的同步 fallback 主要是给 start_game.py 等遗留同步代码用的
            # 它们不在循环中，所以 asyncio.run 是安全的。
            # 如果真的在已有循环中调用了同步方法，会抛出 RuntimeError。
            # 为了完全兼容，我们可以用 urllib 实现一个真正的同步版本作为 fallback
            pass
        
        # Fallback to synchronous urllib implementation
        import urllib.request
        import urllib.error
        
        url = self._build_url(endpoint)
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                status_code = resp.status
        except urllib.error.HTTPError as e:
            try:
                text = e.read().decode("utf-8", errors="replace")
            except Exception:
                text = ""
            status_code = e.code
        except urllib.error.URLError:
            text = ""
            status_code = 0
        except Exception:
            text = ""
            status_code = 0

        try:
            parsed = json.loads(text) if text != "" else {}
            return status_code, parsed
        except Exception as parse_error:
            return status_code, {"raw_text": text, "parse_error": str(parse_error)}

    async def create_new_game_async(self, game_name: str) -> Tuple[int, Dict[str, Any]]:
        data = {"game_name": game_name}
        return await self._send_post_request_async("/createNewGame", data)

    async def insert_data_async(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        data = {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone,
            "rating": rating,
        }
        return await self._send_post_request_async("/insert", data)

    async def query_data_async(self, game_name: str, online_duration: Optional[int] = 1, talk_channel: Optional[int] = 0, cnt: Optional[int] = 100) -> Tuple[int, Dict[str, Any]]:
        data = {
            "game_name": game_name,
            "online_duration": online_duration or 1,
            "talk_channel": talk_channel or 0,
            "cnt": cnt or 100,
        }
        return await self._send_post_request_async("/query", data)

    async def clear_talk_channel_async(self, game_name: str, talk_channel: int) -> Tuple[int, Dict[str, Any]]:
        data = {"game_name": game_name, "talk_channel": talk_channel}
        return await self._send_post_request_async("/clearTalkChannel", data)

    async def update_data_async(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        data = {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone or "1",
            "rating": rating or 50,
        }
        return await self._send_post_request_async("/update", data)

    # Synchronous wrappers
    def create_new_game(self, game_name: str) -> Tuple[int, Dict[str, Any]]:
        return self.send_post_request("/createNewGame", {"game_name": game_name})

    def insert_data(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return self.send_post_request("/insert", {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone,
            "rating": rating,
        })

    def query_data(self, game_name: str, online_duration: Optional[int] = 1, talk_channel: Optional[int] = 0, cnt: Optional[int] = 100) -> Tuple[int, Dict[str, Any]]:
        return self.send_post_request("/query", {
            "game_name": game_name,
            "online_duration": online_duration or 1,
            "talk_channel": talk_channel or 0,
            "cnt": cnt or 100,
        })

    def clear_talk_channel(self, game_name: str, talk_channel: int) -> Tuple[int, Dict[str, Any]]:
        return self.send_post_request("/clearTalkChannel", {"game_name": game_name, "talk_channel": talk_channel})

    def update_data(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return self.send_post_request("/update", {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone or "1",
            "rating": rating or 50,
        })
