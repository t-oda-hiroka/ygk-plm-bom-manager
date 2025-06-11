"""
釣り糸製造BOM管理システム

このモジュールは釣り糸の製造プロセスにおけるBOM（部品表）を管理するためのクラスを提供します。
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class BOMManager:
    """BOM管理システムのメインクラス"""
    
    def __init__(self, db_path: str = "bom_database.db"):
        """
        BOMManagerを初期化します
        
        Args:
            db_path: SQLiteデータベースファイルのパス
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースを初期化し、スキーマを作成します"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")  # 外部キー制約を有効化
            
            # スキーマファイルが存在する場合は読み込み
            if os.path.exists("schema.sql"):
                try:
                    with open("schema.sql", "r", encoding="utf-8") as f:
                        schema = f.read()
                        # 複数のSQL文を実行
                        conn.executescript(schema)
                except sqlite3.OperationalError as e:
                    # テーブルやインデックスが既に存在する場合は無視
                    if "already exists" not in str(e):
                        raise e
    
    def add_item(self, item_id: str, item_name: str, item_type: str, 
                 unit_of_measure: str, **attributes) -> bool:
        """
        新しいアイテムを追加します
        
        Args:
            item_id: アイテムID
            item_name: アイテム名
            item_type: アイテムタイプ
            unit_of_measure: 数量単位
            **attributes: その他の属性（material_type, denier, ps_ratio等）
        
        Returns:
            bool: 追加に成功した場合True
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # 標準属性を取得
                material_type = attributes.get('material_type')
                denier = attributes.get('denier')
                ps_ratio = attributes.get('ps_ratio')
                braid_structure = attributes.get('braid_structure')
                has_core = attributes.get('has_core')
                color = attributes.get('color')
                length_m = attributes.get('length_m')
                twist_type = attributes.get('twist_type')
                
                # 追加属性をJSONで保存
                additional_attrs = {k: v for k, v in attributes.items() 
                                  if k not in ['material_type', 'denier', 'ps_ratio', 
                                             'braid_structure', 'has_core', 'color', 
                                             'length_m', 'twist_type']}
                additional_json = json.dumps(additional_attrs, ensure_ascii=False) if additional_attrs else None
                
                conn.execute("""
                    INSERT INTO items (
                        item_id, item_name, item_type, unit_of_measure,
                        material_type, denier, ps_ratio, braid_structure,
                        has_core, color, length_m, twist_type, additional_attributes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (item_id, item_name, item_type, unit_of_measure,
                      material_type, denier, ps_ratio, braid_structure,
                      has_core, color, length_m, twist_type, additional_json))
                
                return True
        except sqlite3.IntegrityError as e:
            print(f"アイテム追加エラー: {e}")
            return False
    
    def add_bom_component(self, parent_item_id: str, component_item_id: str, 
                         quantity: float, usage_type: str) -> bool:
        """
        BOM構成を追加します
        
        Args:
            parent_item_id: 親アイテムID
            component_item_id: 構成部品アイテムID
            quantity: 数量
            usage_type: 用途タイプ
        
        Returns:
            bool: 追加に成功した場合True
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                conn.execute("""
                    INSERT INTO bom_components (parent_item_id, component_item_id, quantity, usage_type)
                    VALUES (?, ?, ?, ?)
                """, (parent_item_id, component_item_id, quantity, usage_type))
                
                return True
        except sqlite3.IntegrityError as e:
            print(f"BOM構成追加エラー: {e}")
            return False
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        指定されたアイテムの情報を取得します
        
        Args:
            item_id: アイテムID
        
        Returns:
            Dict: アイテム情報、存在しない場合はNone
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
            row = cursor.fetchone()
            
            if row:
                item = dict(row)
                # JSON属性を解析
                if item['additional_attributes']:
                    item['additional_attributes'] = json.loads(item['additional_attributes'])
                return item
            return None
    
    def get_direct_components(self, parent_item_id: str) -> List[Dict[str, Any]]:
        """
        指定されたアイテムの直下の構成部品一覧を取得します
        
        Args:
            parent_item_id: 親アイテムID
        
        Returns:
            List[Dict]: 構成部品情報のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
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
                # JSON属性を解析
                if component['additional_attributes']:
                    component['additional_attributes'] = json.loads(component['additional_attributes'])
                components.append(component)
            
            return components
    
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
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        すべてのアイテム一覧を取得します
        
        Returns:
            List[Dict]: アイテム情報のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM items ORDER BY item_type, item_name")
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                if item['additional_attributes']:
                    item['additional_attributes'] = json.loads(item['additional_attributes'])
                items.append(item)
            
            return items
    
    def get_all_items_by_type(self, item_type: str) -> List[Dict[str, Any]]:
        """
        指定されたタイプのアイテム一覧を取得します
        
        Args:
            item_type: アイテムタイプ
        
        Returns:
            List[Dict]: アイテム情報のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM items WHERE item_type = ? ORDER BY item_name", 
                (item_type,)
            )
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                if item['additional_attributes']:
                    item['additional_attributes'] = json.loads(item['additional_attributes'])
                items.append(item)
            
            return items
    
    def print_bom_tree(self, parent_item_id: str, max_depth: int = 10):
        """
        BOM構造をツリー形式で表示します
        
        Args:
            parent_item_id: 親アイテムID
            max_depth: 最大表示深度
        """
        def print_node(bom_data: Dict[str, Any], indent: int = 0):
            if not bom_data or not bom_data.get('item'):
                return
            
            item = bom_data['item']
            prefix = "  " * indent + "├─ " if indent > 0 else ""
            
            print(f"{prefix}{item['item_name']} ({item['item_id']}) [{item['item_type']}]")
            
            for component in bom_data.get('components', []):
                quantity = component['quantity']
                usage_type = component['usage_type']
                unit = component['item']['unit_of_measure']
                print(f"{'  ' * (indent + 1)}└─ {quantity} {unit} ({usage_type})")
                print_node(component, indent + 2)
        
        bom_tree = self.get_multi_level_bom(parent_item_id, max_depth)
        if bom_tree:
            print(f"\n=== BOM構造: {bom_tree['item']['item_name']} ===")
            print_node(bom_tree)
        else:
            print(f"アイテム '{parent_item_id}' が見つかりません。") 