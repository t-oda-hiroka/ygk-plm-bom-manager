#!/usr/bin/env python3
"""
Oracle DB直接参照BOM管理システム
リードオンリーモードでOracle実データを参照
"""

import cx_Oracle
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


class OracleBOMManager:
    """Oracle DB直接参照BOM管理クラス（リードオンリー）"""
    
    def __init__(self, oracle_config=None, fallback_db_path="bom_database_dev.db"):
        """
        Oracle DB直接参照BOM管理システムを初期化
        
        Args:
            oracle_config: Oracle接続設定辞書
            fallback_db_path: フォールバック用SQLiteデータベースパス
        """
        self.fallback_db_path = fallback_db_path
        self.db_path = fallback_db_path  # 互換性のため
        self.oracle_config = oracle_config or {
            'host': 'hrk-ora-db.cvqkhcprwraj.ap-northeast-1.rds.amazonaws.com',
            'port': 1521,
            'service_name': 'orcl',
            'username': 'ygk_pcs',
            'password': 'ygkpcs'
        }
        
        # Oracle接続テスト
        self.oracle_available = self._test_oracle_connection()
        
        print(f"🌐 Oracle DB接続: {'✅ 利用可能' if self.oracle_available else '❌ 使用不可 (フォールバックモード)'}")
    
    def _test_oracle_connection(self) -> bool:
        """Oracle DB接続テスト"""
        try:
            # Oracle Instant Clientライブラリパスを明示的に指定
            try:
                cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
            except Exception as e:
                if "has already been initialized" not in str(e):
                    print(f"⚠️  Oracle Client初期化警告: {e}")
            
            dsn = f"{self.oracle_config['host']}:{self.oracle_config['port']}/{self.oracle_config['service_name']}"
            connection = cx_Oracle.connect(
                self.oracle_config['username'], 
                self.oracle_config['password'], 
                dsn
            )
            connection.close()
            return True
        except Exception as e:
            print(f"Oracle接続テスト失敗: {e}")
            return False
    
    def _get_oracle_connection(self):
        """Oracle DB接続を取得"""
        if not self.oracle_available:
            raise Exception("Oracle DB接続が利用できません")
        
        dsn = f"{self.oracle_config['host']}:{self.oracle_config['port']}/{self.oracle_config['service_name']}"
        return cx_Oracle.connect(
            self.oracle_config['username'], 
            self.oracle_config['password'], 
            dsn
        )
    
    def get_oracle_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Oracle PCS_PRODUCT_MST から製品情報を取得"""
        if not self.oracle_available:
            return self._get_fallback_items_by_type('完成品')
        
        try:
            connection = self._get_oracle_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
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
                    SPOOL_TYPE
                FROM (
                    SELECT * FROM PCS_PRODUCT_MST 
                    WHERE PRODUCT_CODE IS NOT NULL
                    AND PRODUCT_NAME IS NOT NULL
                    ORDER BY PRODUCT_CODE
                ) WHERE ROWNUM <= :limit
            """, {'limit': limit})
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'item_id': row[0],  # PRODUCT_CODE
                    'item_name': row[1],  # PRODUCT_NAME
                    'item_type': '完成品',  # Oracle製品は完成品として扱う
                    'unit_of_measure': 'M',
                    'yarn_composition': row[2],
                    'series_name': row[3],
                    'length_m': row[4],
                    'color': row[5],
                    'yarn_type': row[6],
                    'raw_num': row[7],
                    'production_num': row[8],
                    'knit_type': row[9],
                    'core_yarn_type': row[10],
                    'spool_type': row[11],
                    'oracle_product_code': row[0],  # Oracle連携フラグ
                    'source': 'oracle_direct',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                products.append(product)
            
            cursor.close()
            connection.close()
            
            print(f"🌐 Oracle PCS_PRODUCT_MST から {len(products)}件の製品を取得")
            return products
            
        except Exception as e:
            print(f"Oracle製品取得エラー: {e}")
            return self._get_fallback_items_by_type('完成品')
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """全アイテム一覧を取得（Oracle + フォールバック）"""
        items = []
        
        # Oracle製品を取得
        oracle_products = self.get_oracle_products()
        items.extend(oracle_products)
        
        # フォールバック（ローカルDB）のアイテムも追加
        fallback_items = self._get_fallback_items()
        
        # Oracle以外のアイテムタイプ（梱包資材、成形品等）を追加
        for item in fallback_items:
            if item['item_type'] not in ['完成品'] or not self.oracle_available:
                items.append(item)
        
        print(f"📊 総アイテム数: {len(items)}件 (Oracle: {len(oracle_products)}件)")
        
        return items
    
    def get_all_items_by_type(self, item_type: str) -> List[Dict[str, Any]]:
        """指定されたタイプのアイテム一覧を取得"""
        if item_type == '完成品' and self.oracle_available:
            return self.get_oracle_products()
        else:
            return self._get_fallback_items_by_type(item_type)
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """指定アイテムの詳細を取得"""
        # まずOracleから検索
        if self.oracle_available:
            try:
                connection = self._get_oracle_connection()
                cursor = connection.cursor()
                
                # 製品マスタから検索
                cursor.execute("""
                    SELECT 
                        PRODUCT_CODE, PRODUCT_NAME, YARN_COMPOSITION,
                        SERIES_NAME, LENGTH_M, COLOR, YARN_TYPE,
                        RAW_NUM, PRODUCTION_NUM, KNIT, CORE_YARN_TYPE, SPOOL_TYPE
                    FROM PCS_PRODUCT_MST
                    WHERE PRODUCT_CODE = :item_id
                """, {'item_id': item_id})
                
                row = cursor.fetchone()
                if row:
                    cursor.close()
                    connection.close()
                    return {
                        'item_id': row[0],
                        'item_name': row[1],
                        'item_type': '完成品',
                        'unit_of_measure': 'M',
                        'yarn_composition': row[2],
                        'series_name': row[3],
                        'length_m': row[4],
                        'color': row[5],
                        'yarn_type': row[6],
                        'raw_num': row[7],
                        'production_num': row[8],
                        'knit_type': row[9],
                        'core_yarn_type': row[10],
                        'spool_type': row[11],
                        'oracle_product_code': row[0],
                        'source': 'oracle_direct'
                    }
                
                cursor.close()
                connection.close()
                
            except Exception as e:
                print(f"Oracle個別アイテム取得エラー: {e}")
        
        # フォールバックでローカルDBから検索
        return self._get_fallback_item(item_id)
    
    def get_direct_components(self, parent_item_id: str) -> List[Dict[str, Any]]:
        """直下の構成部品一覧を取得（Oracle推定 + フォールバック）"""
        # フォールバックBOM
        fallback_bom = self._get_fallback_components(parent_item_id)
        
        # フォールバックがあればそれを使用
        if fallback_bom:
            return fallback_bom
        
        # Oracle推定BOM（フォールバックがない場合）
        return self._generate_oracle_bom_structure(parent_item_id)
    
    def get_multi_level_bom(self, parent_item_id: str, max_depth: int = 10) -> Dict[str, Any]:
        """
        多段階BOMを展開して取得します
        
        Args:
            parent_item_id: 親アイテムID
            max_depth: 最大展開深度
        
        Returns:
            Dict: 多段階BOM構造
        """
        def expand_bom(item_id: str, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {"item": self.get_item(item_id), "components": []}
            
            item = self.get_item(item_id)
            if not item:
                return None
            
            components = []
            direct_components = self.get_direct_components(item_id)
            
            for component in direct_components:
                component_bom = expand_bom(component['item_id'], current_depth + 1)
                if component_bom:
                    component_data = {
                        "quantity": component['quantity'],
                        "usage_type": component['usage_type'],
                        "item": component_bom['item'],
                        "components": component_bom['components']
                    }
                    components.append(component_data)
            
            return {
                "item": item,
                "components": components
            }
        
        return expand_bom(parent_item_id)
    
    def get_lots_by_item(self, item_id: str, status: str = None) -> List[Dict[str, Any]]:
        """アイテムに関連するロット一覧を取得（フォールバック）"""
        return self._get_fallback_lots_by_item(item_id, status)
    
    def get_all_lots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """全ロット一覧を取得（フォールバック）"""
        return self._get_fallback_all_lots(limit)
    
    def get_lot(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """指定されたロットの情報を取得（フォールバック）"""
        return self._get_fallback_lot(lot_id)
    
    def get_lot_genealogy_tree(self, lot_id: str, direction: str = 'forward') -> Dict[str, Any]:
        """ロット系統図ツリーを取得（フォールバック）"""
        return self._get_fallback_lot_genealogy_tree(lot_id, direction)
    
    def add_lot_genealogy(self, *args, **kwargs) -> bool:
        """リードオンリーモード: ロット系統図追加は無効"""
        print("⚠️  リードオンリーモード: データ変更はできません")
        return False

    # フォールバック機能（ローカルDB参照）
    def _get_fallback_items(self) -> List[Dict[str, Any]]:
        """フォールバック: ローカルDBからアイテム一覧を取得"""
        try:
            with sqlite3.connect(self.fallback_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM items ORDER BY item_type, item_name")
                items = []
                for row in cursor.fetchall():
                    item = dict(row)
                    if item['additional_attributes']:
                        try:
                            item['additional_attributes'] = json.loads(item['additional_attributes'])
                        except:
                            pass
                    item['source'] = 'fallback_db'
                    items.append(item)
                return items
        except Exception as e:
            print(f"フォールバックアイテム取得エラー: {e}")
            return []
    
    def _get_fallback_items_by_type(self, item_type: str) -> List[Dict[str, Any]]:
        """フォールバック: ローカルDBからタイプ別アイテムを取得"""
        try:
            with sqlite3.connect(self.fallback_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM items WHERE item_type = ? ORDER BY item_name", (item_type,))
                items = []
                for row in cursor.fetchall():
                    item = dict(row)
                    if item['additional_attributes']:
                        try:
                            item['additional_attributes'] = json.loads(item['additional_attributes'])
                        except:
                            pass
                    item['source'] = 'fallback_db'
                    items.append(item)
                return items
        except Exception as e:
            print(f"フォールバックタイプ別アイテム取得エラー: {e}")
            return []
    
    def _get_fallback_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """フォールバック: ローカルDBから個別アイテムを取得"""
        try:
            with sqlite3.connect(self.fallback_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
                row = cursor.fetchone()
                if row:
                    item = dict(row)
                    if item['additional_attributes']:
                        try:
                            item['additional_attributes'] = json.loads(item['additional_attributes'])
                        except:
                            pass
                    item['source'] = 'fallback_db'
                    return item
                return None
        except Exception as e:
            print(f"フォールバック個別アイテム取得エラー: {e}")
            return None
    
    def _get_fallback_components(self, parent_item_id: str) -> List[Dict[str, Any]]:
        """フォールバック: ローカルDBからBOM構成を取得"""
        try:
            with sqlite3.connect(self.fallback_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT 
                        bc.quantity,
                        bc.usage_type,
                        i.*
                    FROM bom_components bc
                    JOIN items i ON bc.component_item_id = i.item_id
                    WHERE bc.parent_item_id = ?
                    ORDER BY bc.usage_type, i.item_name
                """, (parent_item_id,))
                
                components = []
                for row in cursor.fetchall():
                    component = dict(row)
                    if component['additional_attributes']:
                        try:
                            component['additional_attributes'] = json.loads(component['additional_attributes'])
                        except:
                            pass
                    component['source'] = 'fallback_db'
                    components.append(component)
                
                return components
        except Exception as e:
            print(f"フォールバックBOM構成取得エラー: {e}")
            return []
    
    def _get_fallback_lots_by_item(self, item_id: str, status: str = None) -> List[Dict[str, Any]]:
        """フォールバック: ローカルDBからロット一覧を取得"""
        try:
            with sqlite3.connect(self.fallback_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                sql = """
                    SELECT 
                        l.*,
                        i.item_name,
                        i.unit_of_measure,
                        i.item_type,
                        ps.process_name,
                        qg.grade_name
                    FROM lots l
                    JOIN items i ON l.item_id = i.item_id
                    JOIN process_steps ps ON l.process_code = ps.process_code
                    LEFT JOIN quality_grades qg ON l.quality_grade = qg.grade_code
                    WHERE l.item_id = ?
                """
                params = [item_id]
                
                if status:
                    sql += " AND l.lot_status = ?"
                    params.append(status)
                
                sql += " ORDER BY l.production_date DESC, l.lot_id DESC"
                
                cursor = conn.execute(sql, params)
                lots = [dict(row) for row in cursor.fetchall()]
                
                return lots
        except Exception as e:
            print(f"フォールバックロット取得エラー: {e}")
            return []
    
    def _get_fallback_all_lots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """フォールバック: ローカルDBから全ロット一覧を取得"""
        try:
            with sqlite3.connect(self.fallback_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT 
                        l.*,
                        i.item_name,
                        i.item_type,
                        ps.process_name,
                        qg.grade_name
                    FROM lots l
                    JOIN items i ON l.item_id = i.item_id
                    JOIN process_steps ps ON l.process_code = ps.process_code
                    LEFT JOIN quality_grades qg ON l.quality_grade = qg.grade_code
                    ORDER BY l.production_date DESC, l.lot_id DESC
                    LIMIT ?
                """, (limit,))
                
                lots = [dict(row) for row in cursor.fetchall()]
                return lots
        except Exception as e:
            print(f"フォールバック全ロット取得エラー: {e}")
            return []
    
    def _get_fallback_lot(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """フォールバック: ローカルDBからロット詳細を取得"""
        try:
            with sqlite3.connect(self.fallback_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT l.*, i.item_name, i.item_type, 
                           p.process_name, p.process_level,
                           q.grade_name, q.processing_rule
                    FROM lots l
                    JOIN items i ON l.item_id = i.item_id
                    JOIN process_steps p ON l.process_code = p.process_code
                    JOIN quality_grades q ON l.quality_grade = q.grade_code
                    WHERE l.lot_id = ?
                """, (lot_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"フォールバックロット詳細取得エラー: {e}")
            return None
    
    def _get_fallback_lot_genealogy_tree(self, lot_id: str, direction: str = 'forward') -> Dict[str, Any]:
        """フォールバック: ローカルDBからロット系統図ツリーを取得"""
        try:
            def build_tree(current_lot_id: str, visited: set, depth: int = 0) -> Dict[str, Any]:
                if current_lot_id in visited or depth >= 10:  # 無限ループ回避と深度制限
                    return None
                
                visited.add(current_lot_id)
                
                with sqlite3.connect(self.fallback_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    # 現在のロット情報取得
                    cursor = conn.execute("""
                        SELECT l.*, i.item_name, p.process_name, q.grade_name
                        FROM lots l
                        JOIN items i ON l.item_id = i.item_id
                        JOIN process_steps p ON l.process_code = p.process_code
                        LEFT JOIN quality_grades q ON l.quality_grade = q.grade_code
                        WHERE l.lot_id = ?
                    """, (current_lot_id,))
                    
                    current_lot = cursor.fetchone()
                    if not current_lot:
                        return None
                    
                    lot_data = dict(current_lot)
                    
                    # 関連ロット取得
                    if direction == 'forward':
                        # 子ロット（このロットが親になっているもの）
                        cursor = conn.execute("""
                            SELECT lg.*, cl.*, ci.item_name as child_item_name, 
                                   cp.process_name as child_process_name
                            FROM lot_genealogy lg
                            JOIN lots cl ON lg.child_lot_id = cl.lot_id
                            JOIN items ci ON cl.item_id = ci.item_id
                            JOIN process_steps cp ON cl.process_code = cp.process_code
                            WHERE lg.parent_lot_id = ?
                            ORDER BY lg.created_at
                        """, (current_lot_id,))
                        
                        related_lots = cursor.fetchall()
                        children = []
                        
                        for related in related_lots:
                            child_tree = build_tree(related['child_lot_id'], visited.copy(), depth + 1)
                            if child_tree:
                                children.append(child_tree)
                        
                        lot_data['children'] = children
                    
                    else:  # backward
                        # 親ロット（このロットが子になっているもの）
                        cursor = conn.execute("""
                            SELECT lg.*, pl.*, pi.item_name as parent_item_name,
                                   pp.process_name as parent_process_name
                            FROM lot_genealogy lg
                            JOIN lots pl ON lg.parent_lot_id = pl.lot_id
                            JOIN items pi ON pl.item_id = pi.item_id
                            JOIN process_steps pp ON pl.process_code = pp.process_code
                            WHERE lg.child_lot_id = ?
                            ORDER BY lg.created_at
                        """, (current_lot_id,))
                        
                        related_lots = cursor.fetchall()
                        parents = []
                        
                        for related in related_lots:
                            parent_tree = build_tree(related['parent_lot_id'], visited.copy(), depth + 1)
                            if parent_tree:
                                parents.append(parent_tree)
                        
                        lot_data['parents'] = parents
                    
                    return lot_data
            
            return build_tree(lot_id, set())
            
        except Exception as e:
            print(f"フォールバックロット系統図取得エラー: {e}")
            return {}
    
    # リードオンリーメソッド（変更操作は無効化）
    def add_item(self, *args, **kwargs) -> bool:
        """リードオンリーモード: アイテム追加は無効"""
        print("⚠️  リードオンリーモード: データ変更はできません")
        return False
    
    def add_bom_component(self, *args, **kwargs) -> bool:
        """リードオンリーモード: BOM追加は無効"""
        print("⚠️  リードオンリーモード: データ変更はできません")
        return False
    
    def create_lot(self, *args, **kwargs) -> str:
        """リードオンリーモード: ロット作成は無効"""
        print("⚠️  リードオンリーモード: データ変更はできません")
        return None

    def _generate_oracle_bom_structure(self, item_id: str) -> List[Dict[str, Any]]:
        """Oracle実データに基づくBOM構成を生成（推定）"""
        item = self.get_item(item_id)
        if not item:
            print(f"🔗 Oracle推定BOM {item_id}: アイテム情報なし")
            return []
        
        bom_components = []
        
        if item['item_type'] == '完成品' and item.get('source') == 'oracle_direct':
            # Oracle完成品の場合、実データパターンに基づく推定BOM
            item_name = item.get('item_name', '')
            
            # PEライン（ブレイデッド）の場合
            if 'PE' in item_name or 'ブレイデッド' in item_name or 'VARIVAS' in item_name:
                # PE原糸
                pe_raw = {
                    'item_id': 'PE-UHMW-001',
                    'item_name': 'PE超高分子量原糸',
                    'item_type': '原糸',
                    'unit_of_measure': 'KG',
                    'quantity': round(float(item.get('length_m', 150)) * 0.001, 3),  # 長さから重量推定
                    'usage_type': 'Main Material',
                    'source': 'oracle_estimated'
                }
                bom_components.append(pe_raw)
                
                # 染料（5色マーキングの場合）
                if '5色' in item_name or 'マーキング' in item_name:
                    for i, color in enumerate(['青', '緑', '赤', '黄', '白'], 1):
                        dye = {
                            'item_id': f'DYE-{color[:2].upper()}-001',
                            'item_name': f'釣り糸用染料 {color}',
                            'item_type': '補助材料',
                            'unit_of_measure': 'ML',
                            'quantity': 5.0,
                            'usage_type': 'Dyeing Material',
                            'source': 'oracle_estimated'
                        }
                        bom_components.append(dye)
                
                # スプール
                spool_size = "150" if "150m" in item_name else "200"
                spool = {
                    'item_id': f'PKG-SPOOL-{spool_size}',
                    'item_name': f'スプール {spool_size}m用',
                    'item_type': '成形品',
                    'unit_of_measure': '個',
                    'quantity': 1.0,
                    'usage_type': 'Container',
                    'source': 'oracle_estimated'
                }
                bom_components.append(spool)
                
                # ラベル
                label = {
                    'item_id': 'PKG-LABEL-BRAID',
                    'item_name': 'PEライン用ラベル',
                    'item_type': '梱包資材',
                    'unit_of_measure': '個',
                    'quantity': 1.0,
                    'usage_type': 'Packaging',
                    'source': 'oracle_estimated'
                }
                bom_components.append(label)
            
            # ナイロンライン・フロロカーボンライン共通処理
            elif 'ナイロン' in item_name or 'フロロ' in item_name or 'NY' in item_name or 'FC' in item_name:
                # 原糸（ナイロンまたはフロロカーボン）
                raw_material = 'NY6-RAW-001' if 'ナイロン' in item_name or 'NY' in item_name else 'FC-PVDF-001'
                raw_name = 'ナイロン6原糸' if 'ナイロン' in item_name else 'フロロカーボン原糸'
                
                raw = {
                    'item_id': raw_material,
                    'item_name': raw_name,
                    'item_type': '原糸',
                    'unit_of_measure': 'KG',
                    'quantity': round(float(item.get('length_m', 150)) * 0.0008, 3),
                    'usage_type': 'Main Material',
                    'source': 'oracle_estimated'
                }
                bom_components.append(raw)
                
                # 染料
                if '透明' not in item_name:
                    dye = {
                        'item_id': 'DYE-CLR-001',
                        'item_name': '釣り糸用染料 透明',
                        'item_type': '補助材料',
                        'unit_of_measure': 'ML',
                        'quantity': 3.0,
                        'usage_type': 'Dyeing Material',
                        'source': 'oracle_estimated'
                    }
                    bom_components.append(dye)
                
                # スプール
                spool_size = "150" if "150m" in item_name else "200"
                spool = {
                    'item_id': f'PKG-SPOOL-{spool_size}',
                    'item_name': f'スプール {spool_size}m用',
                    'item_type': '成形品',
                    'unit_of_measure': '個',
                    'quantity': 1.0,
                    'usage_type': 'Container',
                    'source': 'oracle_estimated'
                }
                bom_components.append(spool)
            
            # 汎用梱包材料（全製品共通）
            if not bom_components:  # 他のパターンにマッチしなかった場合
                # 基本的な梱包材料を追加
                basic_package = {
                    'item_id': 'PKG-BASIC-001',
                    'item_name': '基本梱包材料セット',
                    'item_type': '梱包資材',
                    'unit_of_measure': '個',
                    'quantity': 1.0,
                    'usage_type': 'Packaging',
                    'source': 'oracle_estimated'
                }
                bom_components.append(basic_package)
        
        print(f"🔗 Oracle推定BOM {item_id}: {len(bom_components)}件生成")
        return bom_components


# 互換性のための関数
def create_oracle_bom_manager() -> OracleBOMManager:
    """Oracle BOM管理システムのインスタンスを作成"""
    return OracleBOMManager()


if __name__ == "__main__":
    # テスト実行
    print("🌐 Oracle BOM管理システム テスト開始")
    print("=" * 50)
    
    oracle_bom = create_oracle_bom_manager()
    
    # Oracle製品取得テスト
    products = oracle_bom.get_oracle_products(limit=5)
    print(f"\n📦 Oracle製品サンプル: {len(products)}件")
    for product in products[:3]:
        print(f"  • {product['item_id']}: {product['item_name']}")
    
    # 全アイテム取得テスト
    all_items = oracle_bom.get_all_items()
    print(f"\n📊 総アイテム数: {len(all_items)}件")
    
    print("\n✅ Oracle BOM管理システム テスト完了") 