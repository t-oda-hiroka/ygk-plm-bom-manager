#!/usr/bin/env python3
"""
ロット系統図デバッグテスト
"""

from oracle_bom_manager import OracleBOMManager
import json

def test_lot_genealogy():
    print("🔍 ロット系統図デバッグテスト開始")
    print("=" * 50)
    
    # Oracle BOM Manager初期化
    bom_manager = OracleBOMManager()
    
    # テスト対象ロット
    test_lot_id = "2505P001"
    
    print(f"\n📋 テストロット: {test_lot_id}")
    
    # 1. ロット基本情報取得
    print("\n1. ロット基本情報取得")
    lot_info = bom_manager.get_lot(test_lot_id)
    if lot_info:
        print(f"✅ ロット情報取得成功:")
        print(f"   - ロットID: {lot_info['lot_id']}")
        print(f"   - アイテム名: {lot_info['item_name']}")
        print(f"   - 工程: {lot_info['process_name']}")
    else:
        print("❌ ロット情報取得失敗")
        return
    
    # 2. Forward系統図取得テスト
    print("\n2. Forward系統図取得テスト")
    forward_tree = bom_manager.get_lot_genealogy_tree(test_lot_id, 'forward')
    print(f"Forward結果タイプ: {type(forward_tree)}")
    print(f"Forward結果内容: {forward_tree}")
    
    if forward_tree and isinstance(forward_tree, dict):
        print("✅ Forward系統図取得成功")
        print(f"   - 現在ロット: {forward_tree.get('lot_id', 'N/A')}")
        children = forward_tree.get('children', [])
        print(f"   - 子ロット数: {len(children)}")
        for child in children:
            print(f"     └ {child.get('lot_id', 'N/A')}: {child.get('item_name', 'N/A')}")
    else:
        print("❌ Forward系統図が空またはエラー")
    
    # 3. Backward系統図取得テスト
    print("\n3. Backward系統図取得テスト")
    backward_tree = bom_manager.get_lot_genealogy_tree(test_lot_id, 'backward')
    print(f"Backward結果タイプ: {type(backward_tree)}")
    print(f"Backward結果内容: {backward_tree}")
    
    if backward_tree and isinstance(backward_tree, dict):
        print("✅ Backward系統図取得成功")
        print(f"   - 現在ロット: {backward_tree.get('lot_id', 'N/A')}")
        parents = backward_tree.get('parents', [])
        print(f"   - 親ロット数: {len(parents)}")
        for parent in parents:
            print(f"     └ {parent.get('lot_id', 'N/A')}: {parent.get('item_name', 'N/A')}")
    else:
        print("❌ Backward系統図が空またはエラー")
    
    # 4. データベース直接確認
    print("\n4. データベース系統図データ直接確認")
    import sqlite3
    
    try:
        with sqlite3.connect(bom_manager.fallback_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 親子関係確認
            cursor = conn.execute("""
                SELECT parent_lot_id, child_lot_id, consumed_quantity, usage_type
                FROM lot_genealogy 
                WHERE parent_lot_id = ? OR child_lot_id = ?
                ORDER BY created_at
            """, (test_lot_id, test_lot_id))
            
            genealogy_data = cursor.fetchall()
            print(f"データベース系統図レコード数: {len(genealogy_data)}")
            
            for record in genealogy_data:
                print(f"   - 親: {record['parent_lot_id']} → 子: {record['child_lot_id']} (数量: {record['consumed_quantity']})")
                
    except Exception as e:
        print(f"❌ データベース確認エラー: {e}")
    
    print("\n✅ ロット系統図デバッグテスト完了")

if __name__ == "__main__":
    test_lot_genealogy() 