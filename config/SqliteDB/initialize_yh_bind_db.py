import sqlite3
import os

sqlite_db_path = "config/SqliteDB/bind.db"

def initialize_database():
    if not os.path.exists(sqlite_db_path):
        print(f"数据库文件 {sqlite_db_path} 不存在，正在创建...")
        os.makedirs(os.path.dirname(sqlite_db_path), exist_ok=True)
        open(sqlite_db_path, 'a').close()
    
    conn = sqlite3.connect(sqlite_db_path)
    c = conn.cursor()
    
    # 表结构
    c.execute('''
    CREATE TABLE IF NOT EXISTS bindings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        QQ_group_id TEXT,
        YH_group_id TEXT,
        MCToken TEXT,
        YH_user_id TEXT,
        QQ_user_id TEXT,
        sync_YHQQ_mode BOOLEAN,
        sync_QQYH_mode BOOLEAN,
        sync_YHMC_mode BOOLEAN,
        sync_QQMC_mode BOOLEAN
    )
    ''')
    
    # QQ_user 表
    c.execute('''
    CREATE TABLE IF NOT EXISTS QQ_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        QQ_user_id TEXT UNIQUE,
        token TEXT
    )
    ''')
    
    # YH_user 表
    c.execute('''
    CREATE TABLE IF NOT EXISTS YH_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        YH_user_id TEXT UNIQUE,
        token TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"数据库初始化完成。")


if __name__ == "__main__":
    initialize_database()