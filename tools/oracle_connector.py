#!/usr/bin/env python3
"""
Oracle Database 連携モジュール
- リードオンリー接続でOracleから製品・原材料データを取得
- SQLiteへの選択的同期機能
- 同期ログ管理
"""

import cx_Oracle
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OracleConnector:
    """Oracle DB連携クラス（リードオンリー）"""
    
    def __init__(self, 
                 oracle_host: str = "hrk-ora-db.cvqkhcprwraj.ap-northeast-1.rds.amazonaws.com",
                 oracle_port: int = 1521,
                 oracle_service: str = "orcl",
                 oracle_user: str = "ygk_pcs",
                 oracle_password: str = "ygkpcs",
                 sqlite_path: str = "bom_database.db"):
        """
        Oracle連携クラスを初期化
        
        Args:
            oracle_*: Oracle DB接続パラメータ
            sqlite_path: SQLiteデータベースファイルパス
        """
        self.oracle_dsn = f"{oracle_host}:{oracle_port}/{oracle_service}"
        self.oracle_user = oracle_user
        self.oracle_password = oracle_password
        self.sqlite_path = sqlite_path
        
        # Oracle Instant Client初期化
        try:
            cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
        except Exception as e:
            if "has already been initialized" not in str(e):
                logger.warning(f"Oracle Client初期化警告: {e}")
    
    def get_oracle_connection(self) -> cx_Oracle.Connection:
        """Oracle DB接続を取得（リードオンリー）"""
        try:
            connection = cx_Oracle.connect(self.oracle_user, self.oracle_password, self.oracle_dsn)
            logger.info("Oracle DB接続成功")
            return connection
        except cx_Oracle.Error as e:
            logger.error(f"Oracle DB接続エラー: {e}")
            raise
    
    def get_sqlite_connection(self) -> sqlite3.Connection:
        """SQLite DB接続を取得"""
        try:
            connection = sqlite3.connect(self.sqlite_path)
            connection.row_factory = sqlite3.Row
            return connection
        except Exception as e:
            logger.error(f"SQLite DB接続エラー: {e}")
            raise
    
    def get_products_from_oracle(self, limit: Optional[int] = None, 
                                series_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Oracleから製品マスタを取得（SELECT文のみ）
        
        Args:
            limit: 取得件数制限
            series_filter: シリーズ名フィルター
        
        Returns:
            製品データのリスト
        """
        oracle_conn = self.get_oracle_connection()
        
        try:
            cursor = oracle_conn.cursor()
            
            # ベースクエリ
            query = """
                SELECT 
                    PRODUCT_CODE,
                    PRODUCT_NAME,
                    YARN_COMPOSITION,
                    SERIES_NAME,
                    LENGTH_M,
                    COLOR,
                    YARN_TYPE,
                    RAW_NUM,
                    PRODUCTION_NUM,
                    KNIT,
                    CORE_YARN_TYPE,
                    SPOOL_TYPE,
                    ORDERS_NUM,
                    ORDERS_POUND,
                    ORDERS_MM
                FROM PCS_PRODUCT_MST
                WHERE PRODUCT_CODE IS NOT NULL
                AND PRODUCT_NAME IS NOT NULL
            """
            
            params = {}
            
            # シリーズフィルター
            if series_filter:
                query += " AND SERIES_NAME LIKE :series_filter"
                params["series_filter"] = f"%{series_filter}%"
            
            # 件数制限
            if limit:
                query = f"SELECT * FROM ({query}) WHERE ROWNUM <= :limit"
                params["limit"] = limit
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # 辞書形式に変換
            products = []
            for row in rows:
                product = {
                    'oracle_product_code': row[0],
                    'item_name': row[1],
                    'yarn_composition': row[2],
                    'series_name': row[3],
                    'length_m': self._parse_number(row[4]),
                    'color': row[5],
                    'yarn_type': row[6],
                    'raw_num': row[7],
                    'production_num': row[8],
                    'knit_type': row[9],
                    'core_yarn_type': row[10],
                    'spool_type': row[11],
                    'orders_num': row[12],
                    'orders_pound': row[13],
                    'orders_mm': row[14]
                }
                products.append(product)
            
            logger.info(f"Oracle製品マスタ取得完了: {len(products)}件")
            return products
            
        finally:
            oracle_conn.close()
    
    def get_materials_from_oracle(self, category: str = 'all') -> List[Dict[str, Any]]:
        """
        Oracleから原材料マスタを取得（SELECT文のみ）
        
        Args:
            category: 'all', '原糸', 'PS糸', '木管糸'
        
        Returns:
            原材料データのリスト
        """
        oracle_conn = self.get_oracle_connection()
        
        try:
            cursor = oracle_conn.cursor()
            materials = []
            
            # 原糸マスタ
            if category in ['all', '原糸']:
                cursor.execute("""
                    SELECT 品目コード, 原糸種類, 原糸
                    FROM M_品目_原糸_仮
                    WHERE 品目コード IS NOT NULL
                """)
                
                for row in cursor.fetchall():
                    materials.append({
                        'oracle_item_code': row[0],
                        'material_category': '原糸',
                        'yarn_type': row[1],
                        'yarn_value': row[2],
                        'material_name': f"原糸 {row[1] or ''}"
                    })
            
            # PS糸マスタ
            if category in ['all', 'PS糸']:
                cursor.execute("""
                    SELECT 品目コード, 品目名, 原糸種類, PS, PS糸, SZ
                    FROM M_品目_PS糸_仮
                    WHERE 品目コード IS NOT NULL
                """)
                
                for row in cursor.fetchall():
                    materials.append({
                        'oracle_item_code': row[0],
                        'material_name': row[1],
                        'material_category': 'PS糸',
                        'yarn_type': row[2],
                        'ps_value': row[3],
                        'ps_yarn_value': row[4],
                        'twist_direction': row[5]
                    })
            
            # 木管糸マスタ
            if category in ['all', '木管糸']:
                cursor.execute("""
                    SELECT 品目コード, 品目名, 原糸種類, PS, PS糸, 巻きM, SZ
                    FROM M_品目_木管糸_仮
                    WHERE 品目コード IS NOT NULL
                """)
                
                for row in cursor.fetchall():
                    materials.append({
                        'oracle_item_code': row[0],
                        'material_name': row[1],
                        'material_category': '木管糸',
                        'yarn_type': row[2],
                        'ps_value': row[3],
                        'ps_yarn_value': row[4],
                        'winding_length': row[5],
                        'twist_direction': row[6]
                    })
            
            logger.info(f"Oracle原材料マスタ取得完了: {len(materials)}件 (カテゴリ: {category})")
            return materials
            
        finally:
            oracle_conn.close()
    
    def sync_products_to_sqlite(self, products: List[Dict[str, Any]], 
                               update_existing: bool = False) -> Tuple[int, int]:
        """
        製品データをSQLiteに同期
        
        Args:
            products: 製品データリスト
            update_existing: 既存データの更新を行うか
        
        Returns:
            (追加件数, 更新件数)
        """
        sqlite_conn = self.get_sqlite_connection()
        
        try:
            cursor = sqlite_conn.cursor()
            added_count = 0
            updated_count = 0
            
            for product in products:
                oracle_code = product['oracle_product_code']
                
                # 既存レコード確認
                cursor.execute(
                    "SELECT COUNT(*) FROM items WHERE oracle_product_code = ?",
                    (oracle_code,)
                )
                exists = cursor.fetchone()[0] > 0
                
                if exists and not update_existing:
                    continue
                
                # アイテムIDの生成
                item_id = f"ORACLE_{oracle_code}"
                
                # アイテムタイプの推定
                item_type = self._estimate_item_type(product)
                
                if exists:
                    # 更新
                    cursor.execute("""
                        UPDATE items SET
                            item_name = ?,
                            yarn_composition = ?,
                            series_name = ?,
                            length_m = ?,
                            color = ?,
                            knit_type = ?,
                            yarn_type = ?,
                            raw_num = ?,
                            production_num = ?,
                            core_yarn_type = ?,
                            spool_type = ?,
                            oracle_sync_status = 'synced',
                            oracle_last_sync = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE oracle_product_code = ?
                    """, (
                        product['item_name'],
                        product['yarn_composition'],
                        product['series_name'],
                        product['length_m'],
                        product['color'],
                        product['knit_type'],
                        product['yarn_type'],
                        product['raw_num'],
                        product['production_num'],
                        product['core_yarn_type'],
                        product['spool_type'],
                        oracle_code
                    ))
                    updated_count += 1
                else:
                    # 新規追加
                    cursor.execute("""
                        INSERT INTO items (
                            item_id,
                            oracle_product_code,
                            item_name,
                            item_type,
                            unit_of_measure,
                            yarn_composition,
                            series_name,
                            length_m,
                            color,
                            knit_type,
                            yarn_type,
                            raw_num,
                            production_num,
                            core_yarn_type,
                            spool_type,
                            oracle_sync_status,
                            oracle_last_sync
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'synced', CURRENT_TIMESTAMP)
                    """, (
                        item_id,
                        oracle_code,
                        product['item_name'],
                        item_type,
                        'M',  # デフォルト単位
                        product['yarn_composition'],
                        product['series_name'],
                        product['length_m'],
                        product['color'],
                        product['knit_type'],
                        product['yarn_type'],
                        product['raw_num'],
                        product['production_num'],
                        product['core_yarn_type'],
                        product['spool_type']
                    ))
                    added_count += 1
            
            sqlite_conn.commit()
            logger.info(f"SQLite同期完了: 追加{added_count}件, 更新{updated_count}件")
            return added_count, updated_count
            
        finally:
            sqlite_conn.close()
    
    def sync_materials_to_sqlite(self, materials: List[Dict[str, Any]]) -> int:
        """
        原材料データをSQLiteに同期
        
        Args:
            materials: 原材料データリスト
        
        Returns:
            追加件数
        """
        sqlite_conn = self.get_sqlite_connection()
        
        try:
            cursor = sqlite_conn.cursor()
            added_count = 0
            
            for material in materials:
                oracle_code = material['oracle_item_code']
                
                # 既存確認
                cursor.execute(
                    "SELECT COUNT(*) FROM raw_materials WHERE oracle_item_code = ?",
                    (oracle_code,)
                )
                
                if cursor.fetchone()[0] == 0:
                    # 新規追加
                    cursor.execute("""
                        INSERT INTO raw_materials (
                            oracle_item_code,
                            material_name,
                            material_category,
                            yarn_type,
                            ps_value,
                            ps_yarn_value,
                            twist_direction,
                            winding_length
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        oracle_code,
                        material.get('material_name'),
                        material.get('material_category'),
                        material.get('yarn_type'),
                        material.get('ps_value'),
                        material.get('ps_yarn_value'),
                        material.get('twist_direction'),
                        material.get('winding_length')
                    ))
                    added_count += 1
            
            sqlite_conn.commit()
            logger.info(f"原材料同期完了: 追加{added_count}件")
            return added_count
            
        finally:
            sqlite_conn.close()
    
    def log_sync_operation(self, sync_type: str, status: str, 
                          processed: int = 0, updated: int = 0, added: int = 0,
                          error_message: str = None):
        """同期操作をログに記録"""
        sqlite_conn = self.get_sqlite_connection()
        
        try:
            cursor = sqlite_conn.cursor()
            cursor.execute("""
                INSERT INTO oracle_sync_log (
                    sync_type, sync_status, records_processed, 
                    records_updated, records_added, error_message,
                    sync_started_at, sync_completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (sync_type, status, processed, updated, added, error_message))
            
            sqlite_conn.commit()
            
        finally:
            sqlite_conn.close()
    
    def _parse_number(self, value) -> Optional[int]:
        """文字列を数値に変換（Mなどの単位を除去）"""
        if not value:
            return None
        
        try:
            # 数字以外を除去
            numeric_str = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return int(float(numeric_str)) if numeric_str else None
        except:
            return None
    
    def _estimate_item_type(self, product: Dict[str, Any]) -> str:
        """製品データからアイテムタイプを推定"""
        name = (product.get('item_name') or '').upper()
        series = (product.get('series_name') or '').upper()
        
        if 'ABSORBER' in name or 'ABSORBER' in series:
            return '完成品'
        elif 'BRAID' in name or 'BRAID' in series:
            return '製紐糸'
        else:
            return '完成品'  # デフォルト 