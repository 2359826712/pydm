
from re import A
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))  # 添加上一级目录
from threading import local, Thread
import time 
import py_trees
import time
from arcapi import Arc_api, dm
from api_client import ApiClient
arc_api = Arc_api()
client = ApiClient()


import json
import asyncio
import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

class Collect(py_trees.behaviour.Behaviour):

    def __init__(self,  name="收集好友id"):
        super(Collect, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="create_collect", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="create_collect", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="init_dll", access=py_trees.common.Access.READ)#READ
        self.time = 0
        self.cache_file = os.path.join(script_dir, "friend_cache.json")
        self.local_friends = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"读取缓存失败: {e}")
        return set()

    def _save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(list(self.local_friends), f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def _upload_new_friends_async(self, names):
        if not names:
            return
        async def _run():
            lc = ApiClient()
            tasks = [lc.insert_data_async("arc_game", n, "1", "1", 50) for n in names]
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception:
                pass
        try:
            loop = asyncio.get_running_loop()
            for n in names:
                asyncio.create_task(ApiClient().insert_data_async("arc_game", n, "1", "1", 50))
        except RuntimeError:
            Thread(target=lambda: asyncio.run(_run()), daemon=True).start()

    def update(self) -> py_trees.common.Status:
        self.blackboard.in_game = False
        pos = arc_api.FindColorE(26,787,266,869,"54c8e9-000000|ffffff-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[1]) > 0:
            print("在游戏中")
            time.sleep(0.5)
            self.blackboard.need_collect = False
            self.blackboard.in_game = True
            time.sleep(1)
            return py_trees.common.Status.RUNNING
        continue_pos_pic = arc_api.FindPic(1480,875,1541,911,"continue.bmp","000000",1.0,0)
        if int(continue_pos_pic[1]) > 0:
            time.sleep(0.5)
            print("点击继续")
            arc_api.mouse_click(1501,860,0)
            return py_trees.common.Status.RUNNING
        continue_pos = arc_api.FindColorE(1480,875,1541,911,"f9eedf-000000|646264-000000",1.0,0)
        continue_pos = continue_pos.split("|")
        if int(continue_pos[1]) > 0:
            time.sleep(0.5)
            print("点击继续")
            arc_api.mouse_click(1501,860,0)
            return py_trees.common.Status.RUNNING
        pos = arc_api.FindColorE(1317,124,1391,148,"ffbc13-000000|090c19-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) <= 0 :
            self.blackboard.need_collect = False
            has_new_friend = False
            friend_list = arc_api.game_manager.get_friend_list()
            for idx, friend in enumerate(friend_list):
                friend_name = friend['name']
                if friend_name not in self.local_friends:
                    print(f"上报新好友: {friend_name}")
                    client.insert_data("arc_game", friend_name, "1", "1", 50)
                    self.local_friends.add(friend_name)
                    has_new_friend = True
            
            if has_new_friend:
                self._save_cache()
                print("已更新好友缓存")
        else:
            arc_api.click_keyworld("esc")
        return py_trees.common.Status.RUNNING
