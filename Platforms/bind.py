import sqlite3
from config import sqlite_db_path
from logs import logger

def get_info(group_id, source):
    logger.debug(f"获取 group_id={group_id}, source={source} 的信息")
    conn = sqlite3.connect(sqlite_db_path)
    c = conn.cursor()
    if source == "QQ":
        c.execute("""
        SELECT id, QQ_group_id, YH_group_id, MCToken, YH_user_id, QQ_user_id, sync_YHQQ_mode, sync_QQYH_mode, sync_YHMC_mode, sync_QQMC_mode 
        FROM bindings 
        WHERE QQ_group_id=?
        """, (group_id,))
    elif source == "云湖":
        c.execute("""
        SELECT id, QQ_group_id, YH_group_id, MCToken, YH_user_id, QQ_user_id, sync_YHQQ_mode, sync_QQYH_mode, sync_YHMC_mode, sync_QQMC_mode 
        FROM bindings 
        WHERE YH_group_id=?
        """, (group_id,))
    elif source == "MC":
        c.execute("""
        SELECT id, QQ_group_id, YH_group_id, MCToken, YH_user_id, QQ_user_id, sync_YHQQ_mode, sync_QQYH_mode, sync_YHMC_mode, sync_QQMC_mode 
        FROM bindings 
        WHERE MCToken=?
        """, (group_id,))
    else:
        logger.warning(f"未知来源: {source}")
        conn.close()
        return []
    
    results = c.fetchall()
    conn.close()
    
    formatted_results = []
    for result in results:
        formatted_result = {
            "id": result[0],
            "QQ_group_id": result[1],
            "YH_group_id": result[2],
            "MCToken": result[3],
            "YH_user_id": result[4],
            "QQ_user_id": result[5],
            "sync_YHQQ_mode": result[6],
            "sync_QQYH_mode": result[7],
            "sync_YHMC_mode": result[8],
            "sync_QQMC_mode": result[9]
        }
        formatted_results.append(formatted_result)
    
    logger.debug(f"找到 {len(formatted_results)} 条结果")
    return formatted_results if formatted_results else []

def bind_QQYH_group(QQ_group_id, YH_group_id, YH_user_id, QQ_user_id, sync_YHQQ_mode=True, sync_QQYH_mode=True, sync_YHMC_mode=None, sync_QQMC_mode=None):
    try:
        logger.debug(f"尝试绑定 QQ_group_id={QQ_group_id}, YH_group_id={YH_group_id}")
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        
        if not (QQ_group_id.isdigit() and YH_group_id.isdigit()):
            logger.warning("群组ID不是数字")
            return "NotDigit"
        
        c.execute("SELECT COUNT(*) FROM bindings WHERE QQ_group_id=? AND YH_group_id=?", (QQ_group_id, YH_group_id))
        if c.fetchone()[0] > 0:
            logger.warning("重复绑定")
            return "Repeat"

        c.execute("""
        INSERT INTO bindings (QQ_group_id, YH_group_id, YH_user_id, QQ_user_id, sync_YHQQ_mode, sync_QQYH_mode, sync_YHMC_mode, sync_QQMC_mode) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (QQ_group_id, YH_group_id, YH_user_id, QQ_user_id, sync_YHQQ_mode, sync_QQYH_mode, sync_YHMC_mode, sync_QQMC_mode))
        
        conn.commit()
        conn.close()
        logger.debug("绑定成功")
        return "Success"
    except sqlite3.Error as e:
        logger.error(f"SQLite 错误: {e}")
        return "Failed"

def unbind_QQYH_group(QQ_group_id, YH_group_id):
    try:
        logger.debug(f"尝试解除绑定 QQ_group_id={QQ_group_id}, YH_group_id={YH_group_id}")
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        
        if not (QQ_group_id.isdigit() and YH_group_id.isdigit()):
            logger.warning("群组ID不是数字")
            return "NotDigit"
        
        # 检查绑定是否存在
        c.execute("SELECT * FROM bindings WHERE QQ_group_id=? AND YH_group_id=?", (QQ_group_id, YH_group_id))
        binding = c.fetchone()
        
        if binding is None:
            logger.warning("未找到绑定")
            return "BindingNotFound"
        
        # 删除绑定
        c.execute("DELETE FROM bindings WHERE QQ_group_id=? AND YH_group_id=?", (QQ_group_id, YH_group_id))
        conn.commit()
        conn.close()
        logger.debug("解除绑定成功")
        return "Success"
    except sqlite3.Error as e:
        logger.error(f"SQLite 错误: {e}")
        return "Failed"
    
def unbind_YH_allGroup(YH_group_id):
    try:
        logger.debug(f"尝试解除所有 YH_group_id={YH_group_id} 的绑定")
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        
        if not YH_group_id.isdigit():
            logger.warning("群组ID不是数字")
            return "NotDigit"
        
        c.execute("DELETE FROM bindings WHERE YH_group_id=?", (YH_group_id,))
        conn.commit()
        conn.close()
        logger.debug("解除绑定成功")
        return "Success"
    except sqlite3.Error as e:
        logger.error(f"SQLite 错误: {e}")
        return "Failed"

def bind_YHMC(YH_group, MCToken):
    try:
        logger.debug(f"尝试绑定 YH_group={YH_group}, MCToken={MCToken}")
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        
        if YH_group is None or MCToken is None:
            logger.warning("YH_group 或 MCToken 为空")
            return "None"

        # 检查是否已存在相同的 YH_group_id
        c.execute("""
        SELECT * FROM bindings 
        WHERE YH_group_id = ?
        """, (YH_group,))
        existing_record = c.fetchone()

        if existing_record:
            # 更新已存在的记录
            c.execute("""
            UPDATE bindings 
            SET MCToken = ?, sync_YHMC_mode = ?
            WHERE YH_group_id = ?
            """, (MCToken, True, YH_group))
            conn.commit()
            conn.close()
            logger.debug("更新绑定成功")
            return "Updated"
        else:
            # 插入新记录
            c.execute("""
            INSERT INTO bindings (YH_group_id, MCToken, sync_YHMC_mode) 
            VALUES (?, ?, ?)
            """, (YH_group, MCToken, True))
            conn.commit()
            conn.close()
            logger.debug("绑定成功")
            return "Success"
    except sqlite3.Error as e:
        logger.error(f"SQLite 错误: {e}")
        return "Failed"

def bind_QQMC(QQ_group, MCToken):
    try:
        logger.debug(f"尝试绑定 QQ_group={QQ_group}, MCToken={MCToken}")
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        
        if QQ_group is None or MCToken is None:
            logger.warning("QQ_group 或 MCToken 为空")
            return "None"

        # 检查是否已存在相同的 QQ_group_id
        c.execute("""
        SELECT * FROM bindings 
        WHERE QQ_group_id = ?
        """, (QQ_group,))
        existing_record = c.fetchone()

        if existing_record:
            # 更新已存在的记录
            c.execute("""
            UPDATE bindings 
            SET MCToken = ?, sync_QQMC_mode = ?
            WHERE QQ_group_id = ?
            """, (MCToken, True, QQ_group))
            conn.commit()
            conn.close()
            logger.debug("更新绑定成功")
            return "Updated"
        else:
            # 插入新记录
            c.execute("""
            INSERT INTO bindings (QQ_group_id, MCToken, sync_QQMC_mode) 
            VALUES (?, ?, ?)
            """, (QQ_group, MCToken, True))
            conn.commit()
            conn.close()
            logger.debug("绑定成功")
            return "Success"
    except sqlite3.Error as e:
        logger.error(f"SQLite 错误: {e}")
        return "Failed"

def unbind_user_allgroups(YH_user_id):
    try:
        logger.debug(f"尝试解除所有 YH_user_id={YH_user_id} 的绑定")
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM bindings WHERE YH_user_id=?", (YH_user_id,))
        count = c.fetchone()[0]
        if count == 0:
            logger.warning("用户未绑定任何群组")
            conn.close()
            return "NotBind"
        c.execute("DELETE FROM bindings WHERE YH_user_id=?", (YH_user_id,))
        conn.commit()
        conn.close()
        logger.debug("解除绑定成功")
        return "Success"
    except sqlite3.Error as e:
        logger.error(f"SQLite 错误: {e}")
        return "Failed"

def set_sync(sync_YHQQ_mode=None, sync_QQYH_mode=None, sync_YHMC_mode=None, sync_QQMC_mode=None, YH_group_id=None, QQ_group_id=None, MCToken=None):
    try:
        logger.debug(f"尝试设置同步模式")
        conn = sqlite3.connect(sqlite_db_path)
        c = conn.cursor()
        
        # 检查是否有有效的同步模式参数
        if sync_YHQQ_mode is None and sync_QQYH_mode is None and sync_YHMC_mode is None and sync_QQMC_mode is None:
            logger.warning("没有有效的同步模式参数")
            conn.close()
            return "NoSyncMode"
        
        # 构建 WHERE 子句
        where_clause = []
        where_params = []
        if YH_group_id is not None:
            where_clause.append("YH_group_id=?")
            where_params.append(YH_group_id)
        if QQ_group_id is not None:
            where_clause.append("QQ_group_id=?")
            where_params.append(QQ_group_id)
        if MCToken is not None:
            where_clause.append("MCToken=?")
            where_params.append(MCToken)
        
        # 如果没有有效的 WHERE 条件，返回错误
        if not where_clause:
            logger.warning("没有有效的群组或令牌条件")
            conn.close()
            return "NoGroupOrToken"
        
        # 检查绑定是否存在
        check_query = "SELECT * FROM bindings WHERE " + " AND ".join(where_clause)
        c.execute(check_query, where_params)
        binding = c.fetchone()
        
        if binding is None:
            logger.warning("未找到绑定")
            conn.close()
            return "BindingNotFound"
        
        # 构建更新语句
        update_query = "UPDATE bindings SET "
        update_params = []
        if sync_YHQQ_mode is not None:
            update_query += "sync_YHQQ_mode=?, "
            update_params.append(sync_YHQQ_mode)
        if sync_QQYH_mode is not None:
            update_query += "sync_QQYH_mode=?, "
            update_params.append(sync_QQYH_mode)
        if sync_YHMC_mode is not None:
            update_query += "sync_YHMC_mode=?, "
            update_params.append(sync_YHMC_mode)
        if sync_QQMC_mode is not None:
            update_query += "sync_QQMC_mode=?, "
            update_params.append(sync_QQMC_mode)
        
        # 去掉最后的逗号和空格
        update_query = update_query.rstrip(", ")
        
        # 构建完整的 SQL 语句
        update_query += " WHERE " + " AND ".join(where_clause)
        update_params.extend(where_params)
        
        # 执行更新操作
        c.execute(update_query, update_params)
        conn.commit()
        conn.close()
        logger.debug("设置同步模式成功")
        return "Success"
    except sqlite3.Error as e:
        logger.error(f"SQLite 错误: {e}")
        return "Failed"

def get_sync_mode(QQ_group_id=None, YH_group_id=None, MCToken=None):
    logger.debug(f"尝试获取同步模式")
    conn = sqlite3.connect(sqlite_db_path)
    c = conn.cursor()
    
    # 构建查询语句
    query = "SELECT sync_YHQQ_mode, sync_QQYH_mode, sync_YHMC_mode, sync_QQMC_mode FROM bindings WHERE "
    params = []
    
    if QQ_group_id is not None:
        query += "QQ_group_id=? "
        params.append(QQ_group_id)
    if YH_group_id is not None:
        if params:
            query += "AND "
        query += "YH_group_id=? "
        params.append(YH_group_id)
    if MCToken is not None:
        if params:
            query += "AND "
        query += "MCToken=? "
        params.append(MCToken)
    
    # 如果没有有效的 WHERE 条件，返回错误
    if not params:
        logger.warning("没有有效的群组或令牌条件")
        conn.close()
        return None
    
    c.execute(query, params)
    result = c.fetchone()
    conn.close()
    
    if result:
        sync_modes = {
            "sync_YHQQ_mode": result[0],
            "sync_QQYH_mode": result[1],
            "sync_YHMC_mode": result[2],
            "sync_QQMC_mode": result[3]
        }
        logger.debug(f"获取到同步模式: {sync_modes}")
        return " ".join([f"{key}={value}" for key, value in sync_modes.items() if value is not None])
    else:
        logger.warning("未找到同步模式")
        return None