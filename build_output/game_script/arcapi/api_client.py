import json
import urllib.request
import urllib.error


class ApiClient:
    def __init__(self, server_url: str = "http://192.168.20.81:9096"):
        self.server_url = server_url.rstrip("/")

    def _build_url(self, endpoint: str) -> str:
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return self.server_url + endpoint

    def send_post_request(self, endpoint: str, data: dict) -> tuple[int, dict]:
        url = self._build_url(endpoint)
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            try:
                text = e.read().decode("utf-8", errors="replace")
            except Exception:
                text = ""
        except urllib.error.URLError:
            text = ""

        status_code = 200 if text != "" else 0

        try:
            parsed = json.loads(text) if text != "" else {}
            return status_code, parsed
        except Exception as parse_error:
            return status_code, {"raw_text": text, "parse_error": str(parse_error)}

    def create_new_game(self, game_name: str) -> tuple[int, dict]:
        data = {"game_name": game_name}
        return self.send_post_request("/createNewGame", data)

    def insert_data(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> tuple[int, dict]:
        data = {
            "game_name": game_name,
            "account": account,
            "b_zone": b_zone,
            "s_zone": s_zone,
            "rating": rating,
        }
        return self.send_post_request("/insert", data)

    def query_data(self, game_name: str, online_duration: int | None = 1, talk_channel: int | None = 0, cnt: int | None = 100) -> tuple[int, dict]:
        data = {
            "game_name": game_name,
            "online_duration": online_duration or 1,
            "talk_channel": talk_channel or 0,
            "cnt": cnt or 100,
        }
        return self.send_post_request("/query", data)

    def clear_talk_channel(self, game_name: str, talk_channel: int) -> tuple[int, dict]:
        data = {"game_name": game_name, "talk_channel": talk_channel}
        return self.send_post_request("/clearTalkChannel", data)
