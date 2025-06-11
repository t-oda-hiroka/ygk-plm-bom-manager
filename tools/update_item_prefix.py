#!/usr/bin/env python3
"""
アイテムIDプレフィックス更新スクリプト
ORACLE_ → XBRAID_ に変更
"""

import sqlite3
from datetime import datetime

def update_item_prefix():
    """アイテムIDのプレフィックスをORACLE_からXBRAID_に変更"""
    
    print("=" * 80)
    print("🔄 アイテムIDプレフィックス更新")
    print("=" * 80)
    print(f"更新開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        sqlite_conn = sqlite3.connect("bom_database_enhanced.db")
        cursor = sqlite_conn.cursor()
        
        # 現在のORACLE_プレフィックスのアイテムを確認
        print("📋 現在のORACLE_プレフィックスアイテム:")
        cursor.execute("""
            SELECT item_id, item_name, item_type
            FROM items 
            WHERE item_id LIKE 'ORACLE_%'
            ORDER BY item_type, item_name
        """)
        
        oracle_items = cursor.fetchall()
        
        if not oracle_items:
            print("   ORACLE_プレフィックスのアイテムが見つかりませんでした。")
            return True
        
        print(f"   対象アイテム数: {len(oracle_items)}件")
        for item in oracle_items:
            old_id = item[0]
            new_id = old_id.replace('ORACLE_', 'XBRAID_')
            print(f"   {old_id} → {new_id} ({item[2]}: {item[1]})")
        
        print(f"\n🔧 アイテムID更新中...")
        
        # 外部キー制約を一時的に無効化
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # トランザクション開始
        sqlite_conn.execute("BEGIN TRANSACTION")
        
        # 1. itemsテーブルのitem_id更新
        for item in oracle_items:
            old_id = item[0]
            new_id = old_id.replace('ORACLE_', 'XBRAID_')
            
            cursor.execute("""
                UPDATE items 
                SET item_id = ?, updated_at = datetime('now')
                WHERE item_id = ?
            """, (new_id, old_id))
        
        print(f"   ✓ itemsテーブル: {len(oracle_items)}件更新")
        
        # 2. bom_componentsテーブルのparent_item_id更新
        cursor.execute("""
            UPDATE bom_components 
            SET parent_item_id = REPLACE(parent_item_id, 'ORACLE_', 'XBRAID_'),
                updated_at = datetime('now')
            WHERE parent_item_id LIKE 'ORACLE_%'
        """)
        
        parent_updates = cursor.rowcount
        print(f"   ✓ BOM親アイテム: {parent_updates}件更新")
        
        # 3. bom_componentsテーブルのcomponent_item_id更新
        cursor.execute("""
            UPDATE bom_components 
            SET component_item_id = REPLACE(component_item_id, 'ORACLE_', 'XBRAID_'),
                updated_at = datetime('now')
            WHERE component_item_id LIKE 'ORACLE_%'
        """)
        
        component_updates = cursor.rowcount
        print(f"   ✓ BOM構成部品: {component_updates}件更新")
        
        # コミット
        sqlite_conn.commit()
        
        # 外部キー制約を再有効化
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 更新結果の確認
        print(f"\n📊 更新結果確認:")
        
        # 新しいXBRAID_プレフィックスのアイテム確認
        cursor.execute("""
            SELECT item_id, item_name, item_type
            FROM items 
            WHERE item_id LIKE 'XBRAID_%'
            ORDER BY item_type, item_name
        """)
        
        xbraid_items = cursor.fetchall()
        print(f"   XBRAID_プレフィックス: {len(xbraid_items)}件")
        
        # 残存ORACLE_プレフィックス確認
        cursor.execute("""
            SELECT COUNT(*) 
            FROM items 
            WHERE item_id LIKE 'ORACLE_%'
        """)
        
        remaining_oracle = cursor.fetchone()[0]
        print(f"   残存ORACLE_プレフィックス: {remaining_oracle}件")
        
        # BOM構造の整合性確認
        cursor.execute("""
            SELECT COUNT(*) 
            FROM bom_components b
            LEFT JOIN items p ON b.parent_item_id = p.item_id
            LEFT JOIN items c ON b.component_item_id = c.item_id
            WHERE p.item_id IS NULL OR c.item_id IS NULL
        """)
        
        broken_bom = cursor.fetchone()[0]
        print(f"   BOM構造整合性: {broken_bom}件の問題")
        
        if remaining_oracle == 0 and broken_bom == 0:
            print("\n✅ すべて正常に更新されました！")
        else:
            print(f"\n⚠️  注意: 残存ORACLE_項目({remaining_oracle})または BOM問題({broken_bom})があります")
        
        # 更新後のアイテム一覧サンプル表示
        print(f"\n📝 更新後のXBRAID_アイテム（最初の5件）:")
        for i, item in enumerate(xbraid_items[:5]):
            print(f"   {i+1}. {item[0]} ({item[2]}: {item[1]})")
        
        if len(xbraid_items) > 5:
            print(f"   ... 他 {len(xbraid_items)-5}件")
        
        sqlite_conn.close()
        
        print(f"\n" + "=" * 80)
        print("✅ アイテムIDプレフィックス更新完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        try:
            sqlite_conn.rollback()
            sqlite_conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    success = update_item_prefix()
    if success:
        print("\n🎉 プレフィックス更新が正常に完了しました!")
        print("   アプリケーションでXBRAID_プレフィックスのアイテムを確認できます: http://localhost:5002")
    else:
        print("\n�� プレフィックス更新に失敗しました") 