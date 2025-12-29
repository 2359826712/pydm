
from re import A
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))  # 添加上一级目录
from threading import local
import time 
import py_trees
import time
from arcapi import Arc_api, dm
from api_client import ApiClient
# from game_manager import ArcGameManager # 移除直接引用
arc_api = Arc_api()
client = ApiClient()
# game_manager = ArcGameManager() # 移除全局实例

import json
import logging
# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("节点")

class Start_Game(py_trees.behaviour.Behaviour):

    def __init__(self,  name="开始游戏"):
        super(Start_Game, self).__init__(name)
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="need_collect", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="in_game", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="create_collect", access=py_trees.common.Access.READ)#READ
        self.blackboard.register_key(key="create_collect", access=py_trees.common.Access.WRITE)#READ
        self.blackboard.register_key(key="init_dll", access=py_trees.common.Access.READ)#READ
        self.time = 0
        self.create_number  = 0
        self.first_add_friend  = False
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

    def update(self) -> py_trees.common.Status:
        token_file_path = os.path.join(script_dir, "token.txt")
        if not os.path.exists(token_file_path):
            token = arc_api.game_manager.get_jwt_token()
            if token:
                try:
                    with open(token_file_path, "w", encoding="utf-8") as f:
                        f.write(token)
                    print(f"Token 已写入: {token_file_path}")
                except Exception as e:
                    logger.error(f"写入 Token 文件失败: {e}")
        if not self.blackboard.create_collect:
            code, resp = client.create_new_game("arc_game")
            if code == 200:
                print("创建服务器数据表成功")
            else:
                print("创建服务器数据表失败")
                print("状态码：",code)
                if self.create_number >= 10 :
                    logger.error("多次创建服务器数据表失败")
                self.create_number = self.create_number + 1
                time.sleep(1)
                return bret.RUNNING
        self.create_number  = 0
        self.blackboard.create_collect = True
        if not self.first_add_friend and self.blackboard.init_dll and arc_api.select_mode() !="2":
            self.first_add_friend = True
            friend_list = arc_api.game_manager.get_friend_list()
            print(f"\n===== 好友列表（共 {len(friend_list)} 个） =====")
            
            has_new_friend = False
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
                print("好友列表无变化，跳过上报")
        close_pos = arc_api.FindPicE(0,0,1450,645,"close.bmp","000000",1.0,0)
        close_pos = close_pos.split("|")
        if int(close_pos[1]) > 0 :
            time.sleep(0.5)
            print("点击关闭")
            arc_api.mouse_click(472,558,0)
            return py_trees.common.Status.RUNNING
        ans_pos = arc_api.FindColorE(811,536,879,553,"b39347-000000|665632-000000",1.0,0)
        ans_pos = ans_pos.split("|")
        if int(ans_pos[1]) > 0:
            time.sleep(0.5)
            print("反馈页面")
            arc_api.mouse_click(739,545,0)
            return py_trees.common.Status.RUNNING
        pos2 = arc_api.FindColorE(916,523,986,539,"ffbc13-000000",1.0,0)
        pos2 = pos2.split("|")
        if int(pos2[1]) > 0:
            time.sleep(0.5)
            print("点击中间弹窗")
            arc_api.mouse_click(948,523,0)
            return py_trees.common.Status.RUNNING
        pos = arc_api.FindColorE(1256,711,1549,781,"ffbc13-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) > 0 :
            time.sleep(0.5)
            print("在开始页面")
            self.blackboard.in_game = False
        if self.blackboard.need_collect:
            print("需要收集")
            return py_trees.common.Status.FAILURE
        if self.blackboard.in_game:
            print("在游戏内")
            return py_trees.common.Status.SUCCESS
        if not self.blackboard.init_dll:
            print("初始化dll")
            return py_trees.common.Status.FAILURE
        
        
        friend_pos = arc_api.FindPic(0,0,1413,181,"friend.bmp","000000",1.0,0)
        if int(friend_pos[1]) > 0 :
            print("找到添加好友")
            near_pos = arc_api.FindColorE(685,117,758,152,"f9eedf-000000",1.0,0)
            near_pos = near_pos.split("|")
            if int(near_pos[0]) <= 0 :
                time.sleep(1.5)
                arc_api.mouse_click(722,136,0)
                return py_trees.common.Status.RUNNING
            time.sleep(0.5)
            print("点击esc")
            self.click_account = 0
            arc_api.click_keyworld("esc")
            time.sleep(1.5)
            return py_trees.common.Status.RUNNING
        continue_pos_pic = arc_api.FindPic(0,0,1541,911,"continue.bmp","000000",1.0,0)
        if int(continue_pos_pic[1]) > 0:
            time.sleep(0.5)
            print("继续页面")
            self.blackboard.need_collect = True
            return py_trees.common.Status.RUNNING
        pos = arc_api.FindColorE(1256,711,1549,781,"ffbc13-000000",1.0,0)
        pos = pos.split("|")
        if int(pos[0]) > 0 :
            time.sleep(0.5)
            print("点击开始")
            arc_api.mouse_click(1402,736,0)
            return py_trees.common.Status.RUNNING
        else:
            map_select = arc_api.FindColorE(432,442,593,600,"9c8b71-000000|94846c-000000",1.0,0)
            map_select = map_select.split("|")
            if int(map_select[1]) > 0:
                time.sleep(0.5)
                print("点击地图")
                arc_api.mouse_click(745,475,0)
                return py_trees.common.Status.RUNNING
        
        return py_trees.common.Status.SUCCESS
