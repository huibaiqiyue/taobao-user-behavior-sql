#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from sqlalchemy import create_engine, text
import time
import os

# ==================== 配置 ====================
PARQUET_PATH = r'D:\数据分析项目\2\sql\data\UserBehavior_5M_sampled.parquet'
DB_NAME = 'e-commerce'
TABLE_NAME = 'user_behavior'
CHUNK_SIZE = 100000  # 每批插入的行数

# MySQL 连接信息（使用127.0.0.1强制TCP）
MYSQL_USER = 'root'
MYSQL_PASSWORD = '1a2b3c4d5eqaz'
MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
# ==============================================

# 1. 创建连接（先连接到默认的mysql数据库，以便创建新库）
def get_root_engine():
    url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/mysql?charset=utf8mb4"
    return create_engine(url, echo=False)

# 2. 创建目标数据库（如果不存在）
def create_database(engine):
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
        conn.commit()
    print(f"数据库 `{DB_NAME}` 已创建/已存在。")

# 3. 读取Parquet数据（分块）
def read_parquet_in_chunks(file_path, chunksize):
    """使用pandas分块读取parquet（需要pyarrow）"""
    # 注意：pd.read_parquet不支持chunksize参数，需手动分块
    # 先读取整个文件（500万行内存占用不大，约几百MB，可以一次性读）
    # 但为了更稳健，我们一次性读入再分块写入，或者使用迭代器方式。
    # 这里我们一次性读入，因为5M行不算太大。
    df = pd.read_parquet(file_path)
    total = len(df)
    print(f"成功读取 {total:,} 行数据")
    # 分块生成器
    for start in range(0, total, chunksize):
        yield df.iloc[start:start+chunksize]

# 4. 创建表（如果不存在）
def create_table(engine):
    # 定义表结构，与DataFrame列匹配
    # 注意：datetime列在MySQL中为DATETIME类型，date为DATE，其他数字类型
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
        user_id INT NOT NULL,
        item_id INT NOT NULL,
        category_id INT NOT NULL,
        behavior_type TINYINT NOT NULL,
        timestamp BIGINT NOT NULL,
        datetime DATETIME NOT NULL,
        date DATE NOT NULL,
        hour TINYINT NOT NULL,
        weekday TINYINT NOT NULL,
        INDEX idx_user (user_id),
        INDEX idx_item (item_id),
        INDEX idx_category (category_id),
        INDEX idx_behavior (behavior_type),
        INDEX idx_datetime (datetime)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    with engine.connect() as conn:
        conn.execute(text(create_sql))
        conn.commit()
    print(f"表 `{TABLE_NAME}` 已创建/已存在。")

# 5. 插入数据（分块）
def insert_data(engine, df_chunk):
    """将数据块插入表中"""
    df_chunk.to_sql(
        name=TABLE_NAME,
        con=engine,
        if_exists='append',  # 追加数据
        index=False,
        chunksize=CHUNK_SIZE,
        method='multi'       # 使用多行插入加速
    )

# 主流程
def main():
    # 检查Parquet文件是否存在
    if not os.path.exists(PARQUET_PATH):
        print(f"错误：文件 {PARQUET_PATH} 不存在")
        return

    # 1. 连接MySQL（默认数据库mysql）
    root_engine = get_root_engine()
    print("连接MySQL成功")

    # 2. 创建目标数据库（如果不存在）
    create_database(root_engine)

    # 3. 连接到目标数据库
    target_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{DB_NAME}?charset=utf8mb4"
    target_engine = create_engine(target_url, echo=False)
    print(f"已连接到数据库 `{DB_NAME}`")

    # 4. 删除旧表（如果存在），确保全新导入
    with target_engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS `{TABLE_NAME}`"))
        conn.commit()
        print(f"已删除旧表 `{TABLE_NAME}`（如果存在）")

    # 5. 创建新表
    create_table(target_engine)

    # 6. 读取Parquet并分块插入
    print("开始读取Parquet并插入数据...")
    start_time = time.time()
    total_inserted = 0

    for i, chunk in enumerate(read_parquet_in_chunks(PARQUET_PATH, CHUNK_SIZE)):
        insert_data(target_engine, chunk)
        total_inserted += len(chunk)
        print(f"已插入 {total_inserted:,} 行")

    elapsed = time.time() - start_time
    print(f"数据导入完成！共插入 {total_inserted:,} 行，耗时 {elapsed:.2f} 秒")

    # 7. 验证行数
    with target_engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM `{TABLE_NAME}`"))
        count = result.scalar()
        print(f"表中总行数: {count:,}")

    print("全部完成！")

if __name__ == "__main__":
    main()