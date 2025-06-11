#!/usr/bin/env python3
"""
高度な多層BOM構造作成スクリプト
完成品 → 製紐糸 → 原糸 の3層構造や、副資材を含む構造を作成
"""

import sqlite3
from datetime import datetime

def create_advanced_multi_layer_bom():
    """高度な多層BOM構造を作成"""
    
    print("=" * 80)
    print("🏗️ 高度な多層BOM構造作成")
    print("=" * 80)
    print(f"作成開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        sqlite_conn = sqlite3.connect("bom_database_enhanced.db")
        cursor = sqlite_conn.cursor()
        
        # 副資材アイテムを追加
        print("📦 副資材アイテムを追加中...")
        
        auxiliary_items = [
            {
                'item_id': 'AUX_001',
                'item_name': 'スプールS (50m用)',
                'item_type': '成形品',
                'unit_of_measure': '個',
                'material_type': 'プラスチック'
            },
            {
                'item_id': 'AUX_002', 
                'item_name': 'スプールM (100m用)',
                'item_type': '成形品',
                'unit_of_measure': '個',
                'material_type': 'プラスチック'
            },
            {
                'item_id': 'AUX_003',
                'item_name': 'スプールL (300m用)', 
                'item_type': '成形品',
                'unit_of_measure': '個',
                'material_type': 'プラスチック'
            },
            {
                'item_id': 'AUX_004',
                'item_name': 'パッケージフィルム',
                'item_type': '梱包資材',
                'unit_of_measure': '枚',
                'material_type': 'フィルム'
            },
            {
                'item_id': 'AUX_005',
                'item_name': '商品ラベル',
                'item_type': '梱包資材', 
                'unit_of_measure': '枚',
                'material_type': '紙'
            },
            {
                'item_id': 'AUX_006',
                'item_name': '芯糸 (ナイロン)',
                'item_type': '芯糸',
                'unit_of_measure': 'M',
                'material_type': 'ナイロン',
                'yarn_composition': 'ナイロン',
                'denier': 210
            }
        ]
        
        for item in auxiliary_items:
            cursor.execute("""
                INSERT OR IGNORE INTO items 
                (item_id, item_name, item_type, unit_of_measure, material_type, 
                 yarn_composition, denier, oracle_sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'manual')
            """, (
                item['item_id'], item['item_name'], item['item_type'], 
                item['unit_of_measure'], item['material_type'],
                item.get('yarn_composition'), item.get('denier')
            ))
            print(f"  ✓ {item['item_name']} ({item['item_type']})")
        
        sqlite_conn.commit()
        
        # 高度なBOM構造を作成
        print("\n🎯 高度なBOM構造作成中...")
        
        # 完成品に副資材を追加
        cursor.execute("""
            SELECT item_id, item_name, length_m 
            FROM items 
            WHERE item_type = '完成品' 
            AND oracle_product_code IS NOT NULL
        """)
        finished_products = cursor.fetchall()
        
        for product in finished_products:
            product_id = product[0]
            product_name = product[1]
            length = product[2] or 30  # デフォルト30m
            
            # 長さに応じたスプールを選択
            if length <= 50:
                spool_id = 'AUX_001'  # スプールS
            elif length <= 100:
                spool_id = 'AUX_002'  # スプールM
            else:
                spool_id = 'AUX_003'  # スプールL
            
            # 副資材BOMを追加
            auxiliary_bom = [
                (spool_id, 1.0, 'Container'),
                ('AUX_004', 1.0, 'Packaging'),  # パッケージフィルム
                ('AUX_005', 1.0, 'Packaging'),  # ラベル
            ]
            
            for aux_id, quantity, usage in auxiliary_bom:
                cursor.execute("""
                    INSERT OR IGNORE INTO bom_components 
                    (parent_item_id, component_item_id, quantity, usage_type)
                    VALUES (?, ?, ?, ?)
                """, (product_id, aux_id, quantity, usage))
            
            print(f"  ✓ {product_name} に副資材を追加")
        
        # 製紐糸に芯糸を追加
        cursor.execute("""
            SELECT item_id, item_name, knit_type 
            FROM items 
            WHERE item_type = '製紐糸' 
            AND oracle_product_code IS NOT NULL
        """)
        braid_products = cursor.fetchall()
        
        for braid in braid_products:
            braid_id = braid[0]
            braid_name = braid[1]
            knit_type = braid[2]
            
            # X8編み製品には芯糸を追加
            if knit_type and 'X8' in knit_type:
                cursor.execute("""
                    INSERT OR IGNORE INTO bom_components 
                    (parent_item_id, component_item_id, quantity, usage_type)
                    VALUES (?, ?, ?, ?)
                """, (braid_id, 'AUX_006', 1.0, 'Core Thread'))
                
                print(f"  ✓ {braid_name} に芯糸を追加")
        
        sqlite_conn.commit()
        
        # 多層BOM構造の確認
        print("\n📊 多層BOM構造の確認:")
        print("-" * 60)
        
        # 完成品から全階層のBOMを取得
        cursor.execute("""
            WITH RECURSIVE bom_tree(parent_id, parent_name, child_id, child_name, 
                                   quantity, usage_type, level, path) AS (
                -- ルートレベル：完成品
                SELECT 
                    b.parent_item_id,
                    p.item_name,
                    b.component_item_id,
                    c.item_name,
                    b.quantity,
                    b.usage_type,
                    0 as level,
                    p.item_name as path
                FROM bom_components b
                JOIN items p ON b.parent_item_id = p.item_id
                JOIN items c ON b.component_item_id = c.item_id
                WHERE p.item_type = '完成品'
                
                UNION ALL
                
                -- 再帰レベル：子の子を取得
                SELECT 
                    b.parent_item_id,
                    p.item_name,
                    b.component_item_id,
                    c.item_name,
                    b.quantity,
                    b.usage_type,
                    bt.level + 1,
                    bt.path || ' → ' || p.item_name
                FROM bom_components b
                JOIN items p ON b.parent_item_id = p.item_id
                JOIN items c ON b.component_item_id = c.item_id
                JOIN bom_tree bt ON bt.child_id = b.parent_item_id
                WHERE bt.level < 3  -- 最大3階層まで
            )
            SELECT * FROM bom_tree 
            ORDER BY path, level, child_name
        """)
        
        multi_layer_bom = cursor.fetchall()
        
        current_path = None
        for bom_item in multi_layer_bom:
            parent_id = bom_item[0]
            parent_name = bom_item[1]
            child_id = bom_item[2]
            child_name = bom_item[3]
            quantity = bom_item[4]
            usage_type = bom_item[5]
            level = bom_item[6]
            path = bom_item[7]
            
            if path != current_path:
                print(f"\n🌳 {path}")
                current_path = path
            
            indent = "  " * (level + 1)
            print(f"{indent}├─ {child_name} × {quantity} ({usage_type})")
        
        # 統計情報
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bom,
                COUNT(DISTINCT parent_item_id) as parent_count,
                COUNT(DISTINCT component_item_id) as component_count
            FROM bom_components
        """)
        stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT usage_type, COUNT(*) 
            FROM bom_components 
            GROUP BY usage_type 
            ORDER BY COUNT(*) DESC
        """)
        usage_stats = cursor.fetchall()
        
        print(f"\n📈 BOM構造統計:")
        print(f"   • 総BOM関係数: {stats[0]}")
        print(f"   • 親アイテム数: {stats[1]}")
        print(f"   • 構成部品数: {stats[2]}")
        print(f"\n   用途別内訳:")
        for usage, count in usage_stats:
            print(f"     - {usage}: {count}件")
        
        sqlite_conn.close()
        
        print("\n" + "=" * 80)
        print("✅ 高度な多層BOM構造作成完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = create_advanced_multi_layer_bom()
    if success:
        print("\n🎉 高度なBOM構造が正常に作成されました!")
        print("   より詳細なBOMツリーをアプリケーションで確認できます: http://localhost:5002")
        print("   📋 副資材、芯糸を含む完全なBOM構造が利用可能です")
    else:
        print("\n💥 高度なBOM構造作成に失敗しました") 