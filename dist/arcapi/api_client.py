import json
import asyncio
import sqlite3
import os
import threading
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional
script_dir = os.path.dirname(os.path.abspath(__file__))
class ApiClient:
    def __init__(self, local_db_dir: str = script_dir):
        """
        初始化 ApiClient。
        
        :param local_db_dir: 本地数据库文件的存储目录路径。默认为当前目录。
                             每个游戏的数据库将作为单独的 .db 文件存储在此目录下。
                             例如：如果 local_db_dir="data"，则 game1 的数据库路径为 "data/game1.db"。
        """
        self.local_db_dir = local_db_dir
        
        # Local mode resources
        self._locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
        self._conns: Dict[str, sqlite3.Connection] = {}
        self._conn_lock = threading.Lock()
        
        if not os.path.exists(self.local_db_dir):
            os.makedirs(self.local_db_dir, exist_ok=True)

    # --- Local DB Helper Methods ---
    def _get_lock(self, game_name: str) -> threading.Lock:
        with self._global_lock:
            if game_name not in self._locks:
                self._locks[game_name] = threading.Lock()
            return self._locks[game_name]

    def _get_connection(self, game_name: str) -> sqlite3.Connection:
        with self._conn_lock:
            if game_name not in self._conns:
                db_path = os.path.join(self.local_db_dir, f"{game_name}.db")
                conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                
                # Pragma for performance
                pragmas = [
                    "PRAGMA journal_mode=WAL;",
                    "PRAGMA synchronous=NORMAL;",
                    "PRAGMA busy_timeout=5000;",
                    "PRAGMA cache_size=-64000;",
                    "PRAGMA foreign_keys=ON;"
                ]
                for p in pragmas:
                    conn.execute(p)
                
                self._conns[game_name] = conn
            return self._conns[game_name]

    def _get_time_str(self, dt: Optional[datetime] = None) -> str:
        if dt is None:
            dt = datetime.now()
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _get_talk_channel_field(self, channel: int) -> str:
        if 1 <= channel <= 6:
            return f"last_talk_time{channel}"
        raise ValueError(f"喊话通道{channel}暂无")

    def _local_response(self, func, *args):
        try:
            res = func(*args)
            return 200, res if res else {"message": "success"}
        except Exception as e:
            return 400, {"error": str(e)}

    # --- Local DB Implementations ---
    def _create_new_game_local(self, game_name: str):
        lock = self._get_lock(game_name)
        with lock:
            conn = self._get_connection(game_name)
            cursor = conn.cursor()
            
            table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{game_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                online_time TEXT,
                game_name TEXT,
                account TEXT,
                b_zone TEXT,
                s_zone TEXT,
                rating INTEGER,
                last_talk_time1 TEXT DEFAULT '2000-01-01 00:00:00',
                last_talk_time2 TEXT DEFAULT '2000-01-01 00:00:00',
                last_talk_time3 TEXT DEFAULT '2000-01-01 00:00:00',
                last_talk_time4 TEXT DEFAULT '2000-01-01 00:00:00',
                last_talk_time5 TEXT DEFAULT '2000-01-01 00:00:00',
                last_talk_time6 TEXT DEFAULT '2000-01-01 00:00:00'
            );
            """
            
            indices_sql = [
                f'CREATE INDEX IF NOT EXISTS "idx_{game_name}_account" ON "{game_name}" (account);',
                f'CREATE INDEX IF NOT EXISTS "idx_{game_name}_zone" ON "{game_name}" (b_zone, s_zone);',
                f'CREATE INDEX IF NOT EXISTS "idx_{game_name}_online_time" ON "{game_name}" (online_time);'
            ]
            
            try:
                cursor.execute(table_sql)
                for idx in indices_sql:
                    cursor.execute(idx)
                conn.commit()
                return {"message": "create new game table success"}
            except Exception:
                conn.rollback()
                raise

    def _insert_local(self, game_name, account, b_zone, s_zone, rating):
        lock = self._get_lock(game_name)
        with lock:
            conn = self._get_connection(game_name)
            try:
                cursor = conn.cursor()
                cursor.execute(f'SELECT id FROM "{game_name}" WHERE account = ?', (account,))
                row = cursor.fetchone()
                now_str = self._get_time_str()
                
                if row:
                    cursor.execute(f'''
                        UPDATE "{game_name}" 
                        SET b_zone = ?, s_zone = ?, rating = ?, online_time = ?
                        WHERE account = ?
                    ''', (b_zone, s_zone, rating, now_str, account))
                else:
                    cursor.execute(f'''
                        INSERT INTO "{game_name}" (game_name, account, b_zone, s_zone, rating, online_time, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (game_name, account, b_zone, s_zone, rating, now_str, now_str))
                conn.commit()
                return {"message": "insert success"}
            except Exception:
                conn.rollback()
                raise

    def _update_local(self, game_name, account, b_zone, s_zone, rating):
        lock = self._get_lock(game_name)
        with lock:
            conn = self._get_connection(game_name)
            try:
                now_str = self._get_time_str()
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE "{game_name}" 
                    SET b_zone = ?, s_zone = ?, rating = ?, online_time = ?
                    WHERE account = ?
                ''', (b_zone, s_zone, rating, now_str, account))
                conn.commit()
                return {"message": "update success"}
            except Exception:
                conn.rollback()
                raise

    def _query_local(self, game_name, online_duration, talk_channel, cnt):
        if online_duration == 0:
            raise ValueError("在线时长不能为0")

        lock = self._get_lock(game_name)
        with lock:
            conn = self._get_connection(game_name)
            try:
                cursor = conn.cursor()
                query_sql = f'SELECT * FROM "{game_name}" WHERE 1=1'
                params = []
                
                if online_duration and online_duration > 0:
                    target_time = datetime.now() - timedelta(minutes=online_duration)
                    target_time_str = self._get_time_str(target_time)
                    query_sql += " AND online_time > ?"
                    params.append(target_time_str)
                
                talk_field = None
                if talk_channel and talk_channel > 0:
                    talk_field = self._get_talk_channel_field(talk_channel)
                    target_time = datetime.now() - timedelta(minutes=online_duration or 1)
                    target_time_str = self._get_time_str(target_time)
                    query_sql += f" AND {talk_field} < ?"
                    params.append(target_time_str)
                
                cnt_val = cnt if cnt and cnt > 0 else 100
                query_sql += " LIMIT ?"
                params.append(cnt_val)
                
                cursor.execute(query_sql, params)
                rows = cursor.fetchall()
                
                results = []
                ids_to_update = []
                for row in rows:
                    results.append(dict(row))
                    ids_to_update.append(row['id'])
                
                if talk_field and ids_to_update:
                    now_str = self._get_time_str()
                    placeholders = ','.join(['?'] * len(ids_to_update))
                    update_sql = f'UPDATE "{game_name}" SET {talk_field} = ? WHERE id IN ({placeholders})'
                    update_params = [now_str] + ids_to_update
                    cursor.execute(update_sql, update_params)
                    conn.commit()
                    
                return {"message": "query success", "data": results}
            except Exception:
                conn.rollback()
                raise

    def _clear_talk_channel_local(self, game_name, talk_channel):
        lock = self._get_lock(game_name)
        with lock:
            conn = self._get_connection(game_name)
            try:
                talk_field = self._get_talk_channel_field(talk_channel)
                cursor = conn.cursor()
                cursor.execute(f'UPDATE "{game_name}" SET {talk_field} = ?', ('2000-01-01 00:00:00',))
                conn.commit()
                return {"message": "clear talk time channel success"}
            except Exception:
                conn.rollback()
                raise

    # --- Public Methods ---

    async def create_new_game_async(self, game_name: str) -> Tuple[int, Dict[str, Any]]:
        return await asyncio.to_thread(self._local_response, self._create_new_game_local, game_name)

    async def insert_data_async(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return await asyncio.to_thread(self._local_response, self._insert_local, game_name, account, b_zone, s_zone, rating)

    async def query_data_async(self, game_name: str, online_duration: Optional[int] = 1, talk_channel: Optional[int] = 0, cnt: Optional[int] = 100) -> Tuple[int, Dict[str, Any]]:
        return await asyncio.to_thread(self._local_response, self._query_local, game_name, online_duration, talk_channel, cnt)

    async def clear_talk_channel_async(self, game_name: str, talk_channel: int) -> Tuple[int, Dict[str, Any]]:
        return await asyncio.to_thread(self._local_response, self._clear_talk_channel_local, game_name, talk_channel)

    async def update_data_async(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return await asyncio.to_thread(self._local_response, self._update_local, game_name, account, b_zone, s_zone, rating)

    # Synchronous wrappers
    def create_new_game(self, game_name: str) -> Tuple[int, Dict[str, Any]]:
        return self._local_response(self._create_new_game_local, game_name)

    def insert_data(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return self._local_response(self._insert_local, game_name, account, b_zone, s_zone, rating)

    def query_data(self, game_name: str, online_duration: Optional[int] = 1, talk_channel: Optional[int] = 0, cnt: Optional[int] = 100) -> Tuple[int, Dict[str, Any]]:
        return self._local_response(self._query_local, game_name, online_duration, talk_channel, cnt)

    def clear_talk_channel(self, game_name: str, talk_channel: int) -> Tuple[int, Dict[str, Any]]:
        return self._local_response(self._clear_talk_channel_local, game_name, talk_channel)

    def update_data(self, game_name: str, account: str, b_zone: str, s_zone: str, rating: int) -> Tuple[int, Dict[str, Any]]:
        return self._local_response(self._update_local, game_name, account, b_zone, s_zone, rating)
