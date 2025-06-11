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
            
            # スキーマファイルが存在する場合は読み込み（ロット管理対応版）
            schema_files = ["schema_enhanced.sql", "schema.sql"]
            
            for schema_file in schema_files:
                if os.path.exists(schema_file):
                    try:
                        with open(schema_file, "r", encoding="utf-8") as f:
                            schema = f.read()
                            # 複数のSQL文を実行
                            conn.executescript(schema)
                        break  # 最初に見つかったスキーマファイルを使用
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
        すべてのアイテム一覧を取得します（製造工程逆順でソート）
        
        Returns:
            List[Dict]: アイテム情報のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 製造工程の逆順（完成品→原糸）でソート
            process_order_sql = """
                CASE item_type
                    WHEN '完成品' THEN 1
                    WHEN '巻き取り糸' THEN 2
                    WHEN '後PS糸' THEN 3
                    WHEN '染色糸' THEN 4
                    WHEN '製紐糸' THEN 5
                    WHEN 'PS糸' THEN 6
                    WHEN '原糸' THEN 7
                    WHEN '成形品' THEN 8
                    WHEN '梱包資材' THEN 9
                    WHEN '芯糸' THEN 10
                    ELSE 11
                END
            """
            
            cursor = conn.execute(f"""
                SELECT * FROM items 
                ORDER BY {process_order_sql}, item_name
            """)
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                if item['additional_attributes']:
                    item['additional_attributes'] = json.loads(item['additional_attributes'])
                items.append(item)
            
            return items
    
    def get_all_items_by_type(self, item_type: str) -> List[Dict[str, Any]]:
        """
        指定されたタイプのアイテム一覧を取得します（製造工程順ソート統一）
        
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
        BOM構成をツリー形式で表示します
        
        Args:
            parent_item_id: 親アイテムID
            max_depth: 最大表示深度
        """
        def print_node(bom_data: Dict[str, Any], indent: int = 0):
            if not bom_data or not bom_data.get('item'):
                return
            
            item = bom_data['item']
            prefix = "  " * indent + "├─ " if indent > 0 else ""
            print(f"{prefix}{item['item_name']} ({item['item_id']}) - {item['item_type']}")
            
            for component in bom_data.get('components', []):
                print_node(component, indent + 1)
        
        bom_tree = self.get_multi_level_bom(parent_item_id, max_depth)
        if bom_tree:
            print("\n=== BOM Tree ===")
            print_node(bom_tree)
        else:
            print(f"アイテム '{parent_item_id}' が見つかりません。")

    # =============================================================================
    # ロット管理機能
    # =============================================================================
    
    def generate_lot_id(self, process_code: str, production_date: str = None) -> str:
        """
        ロットIDを自動生成します（YY-MM-工程コード-連番3桁形式）
        
        Args:
            process_code: 工程コード（P, W, B, S, C, T, E, F）
            production_date: 製造日（YYYY-MM-DD形式、未指定時は今日）
        
        Returns:
            str: 生成されたロットID
        """
        from datetime import datetime
        
        if production_date:
            date_obj = datetime.strptime(production_date, '%Y-%m-%d')
        else:
            date_obj = datetime.now()
        
        # YY-MM形式
        yy_mm = date_obj.strftime('%y%m')
        
        # 同じ年月・工程コードの最大連番を取得
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(CAST(SUBSTR(lot_id, -3) AS INTEGER)) as max_seq
                FROM lots 
                WHERE lot_id LIKE ? AND process_code = ?
            """, (f"{yy_mm}{process_code}%", process_code))
            
            result = cursor.fetchone()
            max_seq = result[0] if result[0] else 0
            
            # 次の連番
            next_seq = max_seq + 1
            
            # ロットID生成
            lot_id = f"{yy_mm}{process_code}{next_seq:03d}"
            return lot_id
    
    def create_lot(self, item_id: str, process_code: str, planned_quantity: float,
                   production_date: str = None, quality_grade: str = 'A', **kwargs) -> str:
        """
        新しいロットを作成します
        
        Args:
            item_id: アイテムID
            process_code: 工程コード
            planned_quantity: 計画数量
            production_date: 製造日（YYYY-MM-DD形式）
            quality_grade: 品質グレード
            **kwargs: その他のロット属性
        
        Returns:
            str: 作成されたロットID
        """
        from datetime import datetime
        
        # ロットID自動生成
        lot_id = self.generate_lot_id(process_code, production_date)
        
        # デフォルト値設定
        if not production_date:
            production_date = datetime.now().strftime('%Y-%m-%d')
        
        # アイテム情報取得
        item = self.get_item(item_id)
        if not item:
            raise ValueError(f"アイテムID '{item_id}' が見つかりません")
        
        # 工程情報取得
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM process_steps WHERE process_code = ?", (process_code,))
            process = cursor.fetchone()
            if not process:
                raise ValueError(f"工程コード '{process_code}' が見つかりません")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # ロット作成
                conn.execute("""
                    INSERT INTO lots (
                        lot_id, item_id, process_code, lot_name, production_date,
                        planned_quantity, actual_quantity, current_quantity,
                        unit_of_measure, accuracy_type, quality_grade, lot_status,
                        equipment_id, operator_id, location, measured_length,
                        measured_weight, measurement_notes, barcode_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lot_id, item_id, process_code,
                    kwargs.get('lot_name', f"{item['item_name']} {lot_id}"),
                    production_date, planned_quantity,
                    kwargs.get('actual_quantity', planned_quantity),
                    kwargs.get('current_quantity', planned_quantity),
                    item['unit_of_measure'],
                    process[4],  # accuracy_type from process_steps
                    quality_grade, 'active',
                    kwargs.get('equipment_id'), kwargs.get('operator_id'),
                    kwargs.get('location'), kwargs.get('measured_length'),
                    kwargs.get('measured_weight'), kwargs.get('measurement_notes'),
                    kwargs.get('barcode_data')
                ))
                
                # 初期入庫トランザクション作成（同一接続内で実行）
                conn.execute("""
                    INSERT INTO inventory_transactions (
                        lot_id, transaction_type, quantity_before, quantity_change, quantity_after,
                        location_from, location_to, related_lot_id, related_process,
                        reference_document, transaction_date, operator_id, equipment_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lot_id, 'RECEIPT', 0, planned_quantity, planned_quantity,
                    None, kwargs.get('location'),
                    None, None, None,
                    datetime.now().isoformat(),
                    kwargs.get('operator_id'), kwargs.get('equipment_id'),
                    f"ロット初期作成: {lot_id}"
                ))
                
                return lot_id
                
        except sqlite3.IntegrityError as e:
            raise ValueError(f"ロット作成エラー: {e}")
    
    def get_lot(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """
        指定されたロットの情報を取得します
        
        Args:
            lot_id: ロットID
        
        Returns:
            Dict: ロット情報、存在しない場合はNone
        """
        with sqlite3.connect(self.db_path) as conn:
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
    
    def add_lot_genealogy(self, parent_lot_id: str, child_lot_id: str, 
                         consumed_quantity: float, usage_type: str = 'Main Material',
                         **kwargs) -> bool:
        """
        ロット系統図（親子関係）を追加します
        
        Args:
            parent_lot_id: 親ロットID（投入される側）
            child_lot_id: 子ロットID（消費される側）
            consumed_quantity: 消費数量
            usage_type: 用途タイプ
            **kwargs: その他の属性
        
        Returns:
            bool: 追加に成功した場合True
        """
        from datetime import datetime
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 親ロットの工程コード取得
                cursor = conn.execute("SELECT process_code FROM lots WHERE lot_id = ?", (parent_lot_id,))
                parent_process = cursor.fetchone()
                if not parent_process:
                    raise ValueError(f"親ロット '{parent_lot_id}' が見つかりません")
                
                # 子ロットの現在数量取得
                cursor = conn.execute("SELECT current_quantity FROM lots WHERE lot_id = ?", (child_lot_id,))
                child_lot = cursor.fetchone()
                if not child_lot:
                    raise ValueError(f"子ロット '{child_lot_id}' が見つかりません")
                
                # 消費率計算
                consumption_rate = (consumed_quantity / child_lot[0] * 100) if child_lot[0] > 0 else 0
                
                # 系統図エントリ追加
                conn.execute("""
                    INSERT INTO lot_genealogy (
                        parent_lot_id, child_lot_id, consumed_quantity, consumption_rate,
                        process_code, consumption_date, usage_type, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    parent_lot_id, child_lot_id, consumed_quantity, consumption_rate,
                    parent_process[0], 
                    kwargs.get('consumption_date', datetime.now().isoformat()),
                    usage_type, kwargs.get('notes')
                ))
                
                # 子ロットの消費トランザクション記録
                current_qty = child_lot[0]
                new_qty = current_qty - consumed_quantity
                
                # 同一接続内でインベントリトランザクション記録
                conn.execute("""
                    INSERT INTO inventory_transactions (
                        lot_id, transaction_type, quantity_before, quantity_change, quantity_after,
                        location_from, location_to, related_lot_id, related_process,
                        reference_document, transaction_date, operator_id, equipment_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    child_lot_id, 'CONSUMPTION', current_qty, -consumed_quantity, new_qty,
                    None, None,
                    parent_lot_id, None, None,
                    kwargs.get('consumption_date', datetime.now().isoformat()),
                    None, None,
                    f"{usage_type}として{parent_lot_id}に投入"
                ))
                
                # 子ロットの現在数量を更新
                conn.execute("""
                    UPDATE lots SET current_quantity = ? WHERE lot_id = ?
                """, (new_qty, child_lot_id))
                
                return True
                
        except sqlite3.IntegrityError as e:
            print(f"系統図追加エラー: {e}")
            return False
    
    def get_lot_genealogy_tree(self, lot_id: str, direction: str = 'forward') -> Dict[str, Any]:
        """
        ロットの系統図を取得します
        
        Args:
            lot_id: 基点となるロットID
            direction: 'forward'（前方トレース）または 'backward'（後方トレース）
        
        Returns:
            Dict: 系統図データ
        """
        def build_tree(current_lot_id: str, visited: set, depth: int = 0) -> Dict[str, Any]:
            if current_lot_id in visited or depth > 10:
                return None
            
            visited.add(current_lot_id)
            lot_info = self.get_lot(current_lot_id)
            if not lot_info:
                return None
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if direction == 'forward':
                    # 前方トレース：この ロットが投入された先を探す
                    cursor = conn.execute("""
                        SELECT lg.*, l.lot_id as related_lot_id, l.item_name, l.process_name
                        FROM lot_genealogy lg
                        JOIN (
                            SELECT l.lot_id, i.item_name, p.process_name
                            FROM lots l
                            JOIN items i ON l.item_id = i.item_id
                            JOIN process_steps p ON l.process_code = p.process_code
                        ) l ON lg.parent_lot_id = l.lot_id
                        WHERE lg.child_lot_id = ?
                        ORDER BY lg.consumption_date
                    """, (current_lot_id,))
                    
                    children = []
                    for row in cursor.fetchall():
                        child_tree = build_tree(row['parent_lot_id'], visited.copy(), depth + 1)
                        if child_tree:
                            child_tree['genealogy_info'] = dict(row)
                            children.append(child_tree)
                
                else:  # backward
                    # 後方トレース：このロットに投入された原料を探す
                    cursor = conn.execute("""
                        SELECT lg.*, l.lot_id as related_lot_id, l.item_name, l.process_name
                        FROM lot_genealogy lg
                        JOIN (
                            SELECT l.lot_id, i.item_name, p.process_name
                            FROM lots l
                            JOIN items i ON l.item_id = i.item_id
                            JOIN process_steps p ON l.process_code = p.process_code
                        ) l ON lg.child_lot_id = l.lot_id
                        WHERE lg.parent_lot_id = ?
                        ORDER BY lg.consumption_date
                    """, (current_lot_id,))
                    
                    children = []
                    for row in cursor.fetchall():
                        child_tree = build_tree(row['child_lot_id'], visited.copy(), depth + 1)
                        if child_tree:
                            child_tree['genealogy_info'] = dict(row)
                            children.append(child_tree)
            
            return {
                'lot_info': lot_info,
                'children': children,
                'depth': depth
            }
        
        return build_tree(lot_id, set())
    
    def get_lots_by_item(self, item_id: str, status: str = None) -> List[Dict[str, Any]]:
        """
        指定されたアイテムのロット一覧を取得します
        
        Args:
            item_id: アイテムID
            status: ロット状態フィルタ（省略時は全て）
        
        Returns:
            List[Dict]: ロット情報のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if status:
                cursor = conn.execute("""
                    SELECT l.*, i.item_name, p.process_name, q.grade_name
                    FROM lots l
                    JOIN items i ON l.item_id = i.item_id
                    JOIN process_steps p ON l.process_code = p.process_code
                    JOIN quality_grades q ON l.quality_grade = q.grade_code
                    WHERE l.item_id = ? AND l.lot_status = ?
                    ORDER BY l.production_date DESC, l.lot_id
                """, (item_id, status))
            else:
                cursor = conn.execute("""
                    SELECT l.*, i.item_name, p.process_name, q.grade_name
                    FROM lots l
                    JOIN items i ON l.item_id = i.item_id
                    JOIN process_steps p ON l.process_code = p.process_code
                    JOIN quality_grades q ON l.quality_grade = q.grade_code
                    WHERE l.item_id = ?
                    ORDER BY l.production_date DESC, l.lot_id
                """, (item_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_lots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        全ロットの一覧を取得します
        
        Args:
            limit: 取得件数制限
        
        Returns:
            List[Dict]: ロット情報のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT l.*, i.item_name, i.item_type, p.process_name, q.grade_name
                FROM lots l
                JOIN items i ON l.item_id = i.item_id
                JOIN process_steps p ON l.process_code = p.process_code
                JOIN quality_grades q ON l.quality_grade = q.grade_code
                ORDER BY l.created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()] 