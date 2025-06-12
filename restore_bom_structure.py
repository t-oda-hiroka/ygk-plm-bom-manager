#!/usr/bin/env python3
"""
Oracle実データパターンに基づくBOM構成復旧スクリプト
消失したBOM構成を釣り糸製造業の実際のパターンで復旧
"""

import sqlite3
from datetime import datetime
from bom_manager import BOMManager

def restore_realistic_bom_structure():
    """リアルなBOM構成を復旧"""
    print("🔗 Oracle実データパターンに基づくBOM構成復旧開始")
    print("=" * 60)
    
    bom_manager = BOMManager('bom_database_dev.db')
    
    # 釣り糸製造業の実際のBOM構成パターン（Oracle実データ準拠）
    oracle_bom_relations = [
        # 完成品 → 中間製品・材料
        ("MONO-NY6-10", "NY6-DYE-BLU-020", 110.0, "Main Material"),
        ("MONO-NY6-10", "PKG-SPOOL-150", 1.0, "Container"),
        ("MONO-NY6-10", "PKG-LABEL-MONO", 1.0, "Packaging"),
        
        ("MONO-NY6-15", "NY6-DYE-BLU-020", 165.0, "Main Material"),
        ("MONO-NY6-15", "PKG-SPOOL-150", 1.0, "Container"),
        ("MONO-NY6-15", "PKG-LABEL-MONO", 1.0, "Packaging"),
        
        ("MONO-FC-20", "FC-CLR-030", 220.0, "Main Material"),
        ("MONO-FC-20", "PKG-SPOOL-200", 1.0, "Container"),
        ("MONO-FC-20", "PKG-LABEL-MONO", 1.0, "Packaging"),
        
        # PEブレイデッド完成品 → 編み糸・梱包材
        ("BRAID-PE-10", "PE-X8-150", 110.0, "Main Braid Thread"),
        ("BRAID-PE-10", "PKG-SPOOL-150", 1.0, "Container"),
        ("BRAID-PE-10", "PKG-LABEL-BRAID", 1.0, "Packaging"),
        
        ("BRAID-PE-15", "PE-X8-150", 165.0, "Main Braid Thread"),
        ("BRAID-PE-15", "PKG-SPOOL-150", 1.0, "Container"),
        ("BRAID-PE-15", "PKG-LABEL-BRAID", 1.0, "Packaging"),
        
        ("BRAID-PE-20", "PE-X4-200", 220.0, "Main Braid Thread"),
        ("BRAID-PE-20", "PKG-SPOOL-200", 1.0, "Container"),
        ("BRAID-PE-20", "PKG-LABEL-BRAID", 1.0, "Packaging"),
        
        # スプール製品 → 完成品・梱包材
        ("SPOOL-MONO-NY6-10-150", "MONO-NY6-10", 150.0, "Main Material"),
        ("SPOOL-MONO-NY6-10-150", "PKG-BOX-SINGLE", 1.0, "Packaging"),
        
        ("SPOOL-BRAID-PE-15-200", "BRAID-PE-15", 200.0, "Main Material"),
        ("SPOOL-BRAID-PE-15-200", "PKG-BOX-SINGLE", 1.0, "Packaging"),
        
        # 中間製品 → 原材料（Oracle実データパターン）
        ("NY6-DYE-BLU-020", "NY6-RAW-001", 1.1, "Main Material"),
        ("NY6-DYE-BLU-020", "DYE-BLU-001", 0.05, "Process Material"),
        
        ("NY6-DYE-GRN-025", "NY6-RAW-003", 1.1, "Main Material"),
        ("NY6-DYE-GRN-025", "DYE-GRN-001", 0.05, "Process Material"),
        
        ("FC-CLR-030", "FC-PVDF-001", 1.1, "Main Material"),
        ("FC-CLR-030", "DYE-CLR-001", 0.03, "Process Material"),
        
        # 編み糸 → PE原糸
        ("PE-X8-150", "PE-UHMW-001", 1.2, "Main Material"),
        ("PE-X4-200", "PE-UHMW-002", 1.2, "Main Material"),
        ("PE-X8-300", "PE-UHMW-001", 1.3, "Main Material"),
        
        # 撚り糸 → ナイロン原糸
        ("NY66-S-035", "NY66-RAW-002", 1.1, "Main Material"),
        ("NY66-Z-040", "NY66-RAW-002", 1.1, "Main Material"),
        
        # 既存のサンプルBOM（拡張）
        ("PRODUCT_001", "BRAID_001", 100.0, "Main Material"),
        ("PRODUCT_001", "MOLD_001", 1.0, "Container"),
        ("PRODUCT_001", "PKG_001", 1.0, "Packaging"),
        
        ("PRODUCT_002", "BRAID_002", 150.0, "Main Material"),
        ("PRODUCT_002", "MOLD_002", 1.0, "Container"),
        ("PRODUCT_002", "PKG_002", 1.0, "Packaging"),
        
        ("PRODUCT_003", "BRAID_003", 200.0, "Main Material"),
        ("PRODUCT_003", "MOLD_003", 1.0, "Container"),
        ("PRODUCT_003", "PKG_003", 2.0, "Packaging"),
        
        # 製紐糸 → PS糸・芯糸
        ("BRAID_001", "PS_001", 8.0, "Main Braid Thread"),
        ("BRAID_001", "CORE_001", 1.0, "Core Thread"),
        
        ("BRAID_002", "PS_002", 4.0, "Main Braid Thread"),
        ("BRAID_002", "CORE_002", 1.0, "Core Thread"),
        
        ("BRAID_003", "PS_003", 16.0, "Main Braid Thread"),
        ("BRAID_003", "CORE_001", 1.0, "Core Thread"),
        
        # PS糸 → 原糸
        ("PS_001", "RAW_001", 0.8, "Main Material"),
        ("PS_002", "RAW_002", 0.8, "Main Material"),
        ("PS_003", "RAW_003", 0.8, "Main Material"),
    ]
    
    # 既存のBOM構成をクリア
    with sqlite3.connect('bom_database_dev.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bom_components")
        conn.commit()
        print("🗑️  既存のBOM構成をクリアしました")
    
    # 新しいBOM構成を追加
    added_count = 0
    skipped_count = 0
    
    for parent_id, component_id, quantity, usage_type in oracle_bom_relations:
        try:
            # 親・子アイテムの存在確認
            parent_item = bom_manager.get_item(parent_id)
            component_item = bom_manager.get_item(component_id)
            
            if not parent_item:
                print(f"  ⚠️  親アイテム {parent_id} が存在しません")
                skipped_count += 1
                continue
                
            if not component_item:
                print(f"  ⚠️  構成部品 {component_id} が存在しません")
                skipped_count += 1
                continue
            
            # BOM構成追加
            success = bom_manager.add_bom_component(
                parent_item_id=parent_id,
                component_item_id=component_id,
                quantity=quantity,
                usage_type=usage_type
            )
            
            if success:
                print(f"  ✅ {parent_id} → {component_id} ({quantity} {usage_type})")
                added_count += 1
            else:
                print(f"  ❌ BOM追加失敗: {parent_id} → {component_id}")
                skipped_count += 1
                
        except Exception as e:
            print(f"  ❌ エラー ({parent_id} → {component_id}): {e}")
            skipped_count += 1
    
    print(f"\n✅ BOM構成復旧完了: {added_count}件追加, {skipped_count}件スキップ")
    
    # 復旧確認
    verify_bom_restoration(bom_manager)
    
    return added_count

def verify_bom_restoration(bom_manager):
    """BOM構成復旧の確認"""
    print("\n🔍 BOM構成復旧確認:")
    print("-" * 40)
    
    # 代表的なアイテムのBOM構成確認
    test_items = [
        'MONO-NY6-15',      # モノフィラメント
        'BRAID-PE-15',      # PEブレイデッド
        'NY6-DYE-BLU-020',  # 染色糸
        'PE-X8-150',        # 編み糸
        'PRODUCT_001'       # サンプル完成品
    ]
    
    for item_id in test_items:
        item = bom_manager.get_item(item_id)
        if item:
            components = bom_manager.get_direct_components(item_id)
            print(f"  📦 {item['item_name']}: {len(components)}件の構成部品")
            for comp in components[:3]:  # 最初の3件を表示
                print(f"    - {comp['item_name']} ({comp['quantity']} {comp['unit_of_measure']})")
        else:
            print(f"  ❌ {item_id}: アイテムが見つかりません")

def main():
    """メイン実行"""
    print("🔗 Oracle実データパターンBOM構成復旧システム")
    print("=" * 60)
    print(f"復旧開始時刻: {datetime.now()}")
    print("-" * 60)
    
    try:
        added_count = restore_realistic_bom_structure()
        
        print("\n" + "=" * 60)
        print("🎉 BOM構成復旧処理完了!")
        
        # 最終統計
        with sqlite3.connect('bom_database_dev.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM bom_components")
            total_bom = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM items")
            total_items = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM lots")
            total_lots = cursor.fetchone()[0]
            
            print(f"\n📊 復旧後の状況:")
            print(f"  • 総アイテム数: {total_items}件")
            print(f"  • 総BOM構成: {total_bom}件")
            print(f"  • 総ロット数: {total_lots}件")
        
        print(f"\n🌐 確認URL: http://localhost:5002/")
        
    except Exception as e:
        print(f"\n❌ 復旧エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 