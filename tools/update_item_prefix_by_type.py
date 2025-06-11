#!/usr/bin/env python3
"""
アイテムタイプ別プレフィックス更新スクリプト
各アイテムタイプに応じた意味のあるプレフィックスに変更
"""

import sqlite3
import re
from datetime import datetime

def update_item_prefix_by_type():
    """アイテムタイプに応じたプレフィックスに変更"""
    
    print("=" * 80)
    print("🎯 アイテムタイプ別プレフィックス更新")
    print("=" * 80)
    print(f"更新開始時刻: {datetime.now()}")
    print("-" * 80)
    
    # タイプ別プレフィックス定義
    type_prefixes = {
        '完成品': 'PRODUCT_',
        '製紐糸': 'BRAID_',
        'PS糸': 'PS_',
        '原糸': 'YARN_',
        '芯糸': 'CORE_',
        '成形品': 'FORM_',
        '梱包資材': 'PACK_',
        '染色糸': 'DYE_',
        '後PS糸': 'POST_',
        '巻き取り糸': 'WIND_'
    }
    
    print("📋 プレフィックス変更マッピング:")
    for item_type, prefix in type_prefixes.items():
        print(f"   {item_type} → {prefix}")
    print()
    
    try:
        sqlite_conn = sqlite3.connect("bom_database_enhanced.db")
        cursor = sqlite_conn.cursor()
        
        # 現在のアイテム状況を確認
        cursor.execute("""
            SELECT item_id, item_name, item_type
            FROM items 
            ORDER BY item_type, item_name
        """)
        
        all_items = cursor.fetchall()
        
        print(f"📊 対象アイテム数: {len(all_items)}件")
        print("-" * 60)
        
        # 外部キー制約を一時的に無効化
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # トランザクション開始
        sqlite_conn.execute("BEGIN TRANSACTION")
        
        updated_items = {}
        skipped_items = []
        
        for item in all_items:
            old_id = item[0]
            item_name = item[1]
            item_type = item[2]
            
            # 新しいプレフィックスを決定
            if item_type in type_prefixes:
                new_prefix = type_prefixes[item_type]
                
                # 既存のプレフィックスを除去して、コアIDを抽出
                core_id = old_id
                for old_prefix in ['XBRAID_', 'MATERIAL_', 'AUX_', 'ORACLE_']:
                    if core_id.startswith(old_prefix):
                        core_id = core_id[len(old_prefix):]
                        break
                
                new_id = new_prefix + core_id
                
                # IDが変更される場合のみ処理
                if old_id != new_id:
                    # 重複チェック
                    cursor.execute("SELECT COUNT(*) FROM items WHERE item_id = ?", (new_id,))
                    if cursor.fetchone()[0] > 0:
                        # 重複する場合は連番を追加
                        counter = 1
                        while True:
                            numbered_id = f"{new_id}_{counter:03d}"
                            cursor.execute("SELECT COUNT(*) FROM items WHERE item_id = ?", (numbered_id,))
                            if cursor.fetchone()[0] == 0:
                                new_id = numbered_id
                                break
                            counter += 1
                    
                    updated_items[old_id] = {
                        'new_id': new_id,
                        'item_name': item_name,
                        'item_type': item_type
                    }
                else:
                    skipped_items.append(old_id)
            else:
                print(f"⚠️  未対応タイプ: {item_type} ({old_id})")
                skipped_items.append(old_id)
        
        print(f"🔧 更新対象: {len(updated_items)}件")
        print(f"⏭️  スキップ: {len(skipped_items)}件")
        print()
        
        # 1. itemsテーブルのitem_id更新
        for old_id, info in updated_items.items():
            cursor.execute("""
                UPDATE items 
                SET item_id = ?, updated_at = datetime('now')
                WHERE item_id = ?
            """, (info['new_id'], old_id))
            
            print(f"  ✓ {old_id} → {info['new_id']} ({info['item_type']}: {info['item_name'][:30]}...)")
        
        print(f"\n   📦 itemsテーブル: {len(updated_items)}件更新")
        
        # 2. bom_componentsテーブルのparent_item_id更新
        parent_updates = 0
        for old_id, info in updated_items.items():
            cursor.execute("""
                UPDATE bom_components 
                SET parent_item_id = ?, updated_at = datetime('now')
                WHERE parent_item_id = ?
            """, (info['new_id'], old_id))
            parent_updates += cursor.rowcount
        
        print(f"   🔗 BOM親アイテム: {parent_updates}件更新")
        
        # 3. bom_componentsテーブルのcomponent_item_id更新
        component_updates = 0
        for old_id, info in updated_items.items():
            cursor.execute("""
                UPDATE bom_components 
                SET component_item_id = ?, updated_at = datetime('now')
                WHERE component_item_id = ?
            """, (info['new_id'], old_id))
            component_updates += cursor.rowcount
        
        print(f"   🧩 BOM構成部品: {component_updates}件更新")
        
        # コミット
        sqlite_conn.commit()
        
        # 外部キー制約を再有効化
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 更新結果の確認
        print(f"\n📊 更新結果確認:")
        print("-" * 60)
        
        # タイプ別の新しいプレフィックス分布
        cursor.execute("""
            SELECT item_type, COUNT(*) as count
            FROM items 
            GROUP BY item_type 
            ORDER BY item_type
        """)
        
        type_distribution = cursor.fetchall()
        
        for item_type, count in type_distribution:
            expected_prefix = type_prefixes.get(item_type, 'UNKNOWN_')
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM items 
                WHERE item_type = ? AND item_id LIKE ?
            """, (item_type, expected_prefix + '%'))
            
            prefix_count = cursor.fetchone()[0]
            
            print(f"   {item_type}: {count}件 (プレフィックス適用: {prefix_count}件)")
        
        # BOM構造の整合性確認
        cursor.execute("""
            SELECT COUNT(*) 
            FROM bom_components b
            LEFT JOIN items p ON b.parent_item_id = p.item_id
            LEFT JOIN items c ON b.component_item_id = c.item_id
            WHERE p.item_id IS NULL OR c.item_id IS NULL
        """)
        
        broken_bom = cursor.fetchone()[0]
        print(f"\n   🔗 BOM構造整合性: {broken_bom}件の問題")
        
        # サンプル表示
        print(f"\n📝 更新後のアイテムIDサンプル:")
        cursor.execute("""
            SELECT item_type, item_id, item_name
            FROM items 
            ORDER BY item_type, item_id
            LIMIT 15
        """)
        
        samples = cursor.fetchall()
        current_type = None
        
        for item_type, item_id, item_name in samples:
            if item_type != current_type:
                print(f"\n   📂 {item_type}:")
                current_type = item_type
            print(f"      {item_id} - {item_name[:40]}...")
        
        sqlite_conn.close()
        
        if broken_bom == 0:
            print(f"\n✅ 全て正常に更新されました！")
        else:
            print(f"\n⚠️  注意: BOM構造に{broken_bom}件の問題があります")
        
        print(f"\n" + "=" * 80)
        print("✅ アイテムタイプ別プレフィックス更新完了")
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
    success = update_item_prefix_by_type()
    if success:
        print("\n🎉 アイテムタイプ別プレフィックス更新が正常に完了しました!")
        print("   各アイテムタイプが分かりやすいプレフィックスになりました:")
        print("   • 完成品: PRODUCT_")
        print("   • 製紐糸: BRAID_") 
        print("   • PS糸: PS_")
        print("   • 原糸: YARN_")
        print("   • 芯糸: CORE_")
        print("   • 成形品: FORM_")
        print("   • 梱包資材: PACK_")
        print("   アプリケーションで確認できます: http://localhost:5002")
    else:
        print("\n�� プレフィックス更新に失敗しました") 