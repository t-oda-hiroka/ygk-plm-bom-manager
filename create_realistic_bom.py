#!/usr/bin/env python3
"""
現実的なBOM構造作成スクリプト
Oracle分析結果に基づいて釣り糸製造のBOM構造を構築
"""

import sqlite3
import cx_Oracle
from datetime import datetime

# 接続パラメータ
HOST = "hrk-ora-db.cvqkhcprwraj.ap-northeast-1.rds.amazonaws.com"
PORT = 1521
SERVICE_NAME = "orcl"
USERNAME = "ygk_pcs"
PASSWORD = "ygkpcs"

def create_realistic_bom_structures():
    """現実的なBOM構造を作成"""
    
    print("=" * 80)
    print("🎯 現実的なBOM構造作成")
    print("=" * 80)
    print(f"作成開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        # SQLite接続
        sqlite_conn = sqlite3.connect("bom_database_enhanced.db")
        cursor = sqlite_conn.cursor()
        
        # 現在のアイテム一覧を取得
        cursor.execute("""
            SELECT item_id, item_name, item_type, yarn_composition, knit_type, 
                   series_name, oracle_product_code
            FROM items 
            WHERE oracle_product_code IS NOT NULL
            ORDER BY item_type, item_name
        """)
        
        items = cursor.fetchall()
        
        # アイテムを種類別に分類
        items_by_type = {}
        for item in items:
            item_type = item[2]
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append(item)
        
        print("📦 登録済みアイテム:")
        for item_type, type_items in items_by_type.items():
            print(f"  {item_type}: {len(type_items)}件")
        print()
        
        # BOM構造パターンを定義
        bom_structures = []
        
        # 1. 完成品 → 製紐糸 + 副資材のBOM構造
        if '完成品' in items_by_type and '製紐糸' in items_by_type:
            print("🎣 完成品BOM構造を作成中...")
            
            for finished_product in items_by_type['完成品']:
                # 同じシリーズの製紐糸を探す
                compatible_braid = None
                for braid in items_by_type['製紐糸']:
                    # X-BRAID系統なら互換性があると判断
                    if 'X-BRAID' in braid[5] and 'X-BRAID' in finished_product[5]:
                        compatible_braid = braid
                        break
                
                if compatible_braid:
                    # 完成品のBOM構造を作成
                    bom_structures.append({
                        'parent_id': finished_product[0],
                        'parent_name': finished_product[1],
                        'children': [
                                                         {
                                 'item_id': compatible_braid[0],
                                 'item_name': compatible_braid[1],
                                 'quantity': 1.0,
                                 'usage_description': 'Main Material'
                             }
                        ]
                    })
                    
                    print(f"  ✓ {finished_product[1]} → {compatible_braid[1]}")
        
        # 2. 製紐糸 → 原糸のBOM構造（X8編みなら8本の原糸を使用）
        if '製紐糸' in items_by_type and '原糸' in items_by_type:
            print("\n🧵 製紐糸BOM構造を作成中...")
            
            for braid in items_by_type['製紐糸']:
                knit_type = braid[4]  # knit_type
                
                # 編み方から原糸の本数を決定
                yarn_count = 4  # デフォルト
                if knit_type and 'X8' in knit_type:
                    yarn_count = 8
                elif knit_type and 'X4' in knit_type:
                    yarn_count = 4
                elif knit_type and 'X9' in knit_type:
                    yarn_count = 9
                elif knit_type and 'X16' in knit_type:
                    yarn_count = 16
                
                # PE原糸を選択
                pe_yarn = None
                for yarn in items_by_type['原糸']:
                    if 'PE' in yarn[3]:  # yarn_composition
                        pe_yarn = yarn
                        break
                
                if pe_yarn:
                    # 製紐糸のBOM構造を作成
                    bom_structures.append({
                        'parent_id': braid[0],
                        'parent_name': braid[1],
                        'children': [
                                                         {
                                 'item_id': pe_yarn[0],
                                 'item_name': pe_yarn[1],
                                 'quantity': float(yarn_count),
                                 'usage_description': 'Main Braid Thread'
                             }
                        ]
                    })
                    
                    print(f"  ✓ {braid[1]} → {pe_yarn[1]} × {yarn_count}")
        
        # 3. PS糸 → 原糸 + PS加工のBOM構造
        if 'PS糸' in items_by_type and '原糸' in items_by_type:
            print("\n🎨 PS糸BOM構造を作成中...")
            
            for ps_yarn in items_by_type['PS糸']:
                # 基本原糸を選択
                base_yarn = None
                for yarn in items_by_type['原糸']:
                    if 'PE' in yarn[3]:  # yarn_composition
                        base_yarn = yarn
                        break
                
                if base_yarn:
                    # PS糸のBOM構造を作成
                    bom_structures.append({
                        'parent_id': ps_yarn[0],
                        'parent_name': ps_yarn[1],
                        'children': [
                                                     {
                             'item_id': base_yarn[0],
                             'item_name': base_yarn[1],
                             'quantity': 1.0,
                             'usage_description': 'Main Material'
                         }
                        ]
                    })
                    
                    print(f"  ✓ {ps_yarn[1]} → {base_yarn[1]}")
        
        # BOM構造をデータベースに保存
        print(f"\n💾 BOM構造をデータベースに保存中... ({len(bom_structures)}件)")
        
        for bom in bom_structures:
            for child in bom['children']:
                cursor.execute("""
                    INSERT OR REPLACE INTO bom_components 
                    (parent_item_id, component_item_id, quantity, usage_type)
                    VALUES (?, ?, ?, ?)
                """, (
                    bom['parent_id'],
                    child['item_id'],
                    child['quantity'],
                    child['usage_description']
                ))
        
        sqlite_conn.commit()
        
        # 作成されたBOM構造の確認
        print("\n📋 作成されたBOM構造:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT 
                p.item_name as parent_name,
                c.item_name as child_name,
                b.quantity,
                b.usage_type,
                p.item_type as parent_type,
                c.item_type as child_type
            FROM bom_components b
            JOIN items p ON b.parent_item_id = p.item_id
            JOIN items c ON b.component_item_id = c.item_id
            ORDER BY p.item_type, p.item_name, c.item_name
        """)
        
        bom_list = cursor.fetchall()
        
        current_parent = None
        for bom_item in bom_list:
            parent_name = bom_item[0]
            child_name = bom_item[1]
            quantity = bom_item[2]
            usage = bom_item[3]
            parent_type = bom_item[4]
            child_type = bom_item[5]
            
            if parent_name != current_parent:
                print(f"\n📦 {parent_name} ({parent_type})")
                current_parent = parent_name
            
            print(f"   ├─ {child_name} ({child_type}) × {quantity}")
            print(f"   │   用途: {usage}")
        
        # 統計情報
        cursor.execute("SELECT COUNT(*) FROM bom_components")
        total_bom_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT parent_item_id) as parent_count,
                   COUNT(DISTINCT component_item_id) as child_count
            FROM bom_components
        """)
        stats = cursor.fetchone()
        
        print(f"\n📊 BOM構造統計:")
        print(f"   • 総BOM関係数: {total_bom_count}")
        print(f"   • 親アイテム数: {stats[0]}")
        print(f"   • 子アイテム数: {stats[1]}")
        
        sqlite_conn.close()
        
        print("\n" + "=" * 80)
        print("✅ 現実的なBOM構造作成完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = create_realistic_bom_structures()
    if success:
        print("\n🎉 BOM構造が正常に作成されました!")
        print("   アプリケーションでBOMツリーを確認できます: http://localhost:5002")
    else:
        print("\n�� BOM構造作成に失敗しました") 