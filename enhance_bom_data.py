#!/usr/bin/env python3
"""
BOM構造大幅拡張スクリプト - 豊富なデータ作成
Oracle風の詳細なBOM構造を直接データベースに追加
"""

import sqlite3
from bom_manager import BOMManager

def enhance_bom_data():
    """豊富なBOM構造を直接データベースに追加"""
    
    print("🔧 BOM構造を大幅拡張中...")
    
    bom_manager = BOMManager('bom_database_dev.db')
    
    # 大幅に拡張されたサンプルアイテムの作成
    sample_items = [
        # ============= 完成品レベル =============
        # 既存製品（より詳細な名前）
        ("PRODUCT_001", "ハイパワーライン PE X8編み 1.0号 100m", "完成品", "個"),
        ("PRODUCT_002", "スーパーライン ナイロン 1.5号 150m", "完成品", "個"),
        ("PRODUCT_003", "プロライン フロロカーボン 2.0号 200m", "完成品", "個"),
        
        # 新規プレミアム製品
        ("PREMIUM_PE_10", "プレミアムPEブレイデッド 1.0号 高強度", "完成品", "M"),
        ("PREMIUM_NY_15", "プレミアムナイロン 1.5号 耐摩耗", "完成品", "M"),
        ("TOURNAMENT_FC_20", "トーナメント用フロロカーボン 2.0号", "完成品", "M"),
        ("HYBRID_LINE_25", "ハイブリッドライン PE-NY複合 2.5号", "完成品", "M"),
        
        # スプール製品
        ("SPOOL_PE_10_300", "PE 1.0号 300mスプール製品", "完成品", "個"),
        ("SPOOL_NY_15_500", "ナイロン 1.5号 500mスプール製品", "完成品", "個"),
        ("SPOOL_FC_20_200", "フロロカーボン 2.0号 200mスプール製品", "完成品", "個"),
        
        # ============= 製紐糸レベル =============
        # 既存製紐糸（詳細化）
        ("BRAID_001", "PE編み糸 X8構造 グレード1", "製紐糸", "M"),
        ("BRAID_002", "ナイロン編み糸 X4構造 グレード2", "製紐糸", "M"),
        ("BRAID_003", "PE編み糸 X16構造 高強度", "製紐糸", "M"),
        
        # 新規高度な製紐糸
        ("BRAID_PE_X8_ULTRA", "PE編み糸 X8超高密度 スペクトラ芯", "製紐糸", "M"),
        ("BRAID_NY_X4_HYBRID", "ナイロン-PE複合編み糸 X4", "製紐糸", "M"),
        ("BRAID_FC_MONO", "フロロカーボン単糸 高透明", "製紐糸", "M"),
        
        # ============= PS糸・後PS糸レベル =============
        # 既存PS糸（詳細化）
        ("PS_001", "ナイロン6 PS糸 6号 標準", "PS糸", "M"),
        ("PS_002", "ナイロン66 PS糸 8号 高強度", "PS糸", "M"),
        ("PS_003", "PE PS糸 10号 超高分子量", "PS糸", "M"),
        
        # 新規撚り糸（後PS糸）
        ("TWIST_NY6_S_035", "ナイロン6撚り糸 S撚り 0.35mm", "後PS糸", "M"),
        ("TWIST_PE_Z_040", "PE撚り糸 Z撚り 0.40mm", "後PS糸", "M"),
        ("TWIST_NY66_S_050", "ナイロン66撚り糸 S撚り 0.50mm", "後PS糸", "M"),
        
        # ============= 染色糸レベル =============
        # 既存染色糸（詳細化）
        ("DYE_001", "ナイロン6染色糸 ブルー 高発色", "染色糸", "M"),
        ("DYE_002", "ナイロン6染色糸 グリーン 耐色性", "染色糸", "M"),
        ("DYE_003", "ナイロン6染色糸 レッド 蛍光", "染色糸", "M"),
        
        # 新規詳細染色糸
        ("DYE_NY6_BLUE_020", "ナイロン6染色糸 青 0.20mm", "染色糸", "M"),
        ("DYE_NY6_GREEN_025", "ナイロン6染色糸 緑 0.25mm", "染色糸", "M"),
        ("DYE_PE_CLEAR_030", "PE透明糸 0.30mm UV耐性", "染色糸", "M"),
        ("DYE_FC_CLEAR_035", "フロロカーボン透明糸 0.35mm", "染色糸", "M"),
        
        # ============= 原糸レベル =============
        # 既存原糸（詳細化）
        ("RAW_001", "ナイロン6原糸 150D 標準グレード", "原糸", "KG"),
        ("RAW_002", "ナイロン66原糸 200D 高強度グレード", "原糸", "KG"),
        ("RAW_003", "ナイロン6原糸 100D 細糸グレード", "原糸", "KG"),
        
        # 新規高性能原糸
        ("RAW_NY6_ULTRA", "ナイロン6超高強度原糸 スーパータフ", "原糸", "KG"),
        ("RAW_PE_SPECTRA", "PE超高分子量原糸 スペクトラ", "原糸", "KG"),
        ("RAW_FC_PVDF", "フロロカーボン原糸 PVDF高純度", "原糸", "KG"),
        ("RAW_NY66_PREMIUM", "ナイロン66プレミアム原糸", "原糸", "KG"),
        
        # ============= 芯糸 =============
        # 既存芯糸（詳細化）
        ("CORE_001", "ナイロン芯糸 6号 標準", "芯糸", "M"),
        ("CORE_002", "PE芯糸 8号 高強度", "芯糸", "M"),
        
        # 新規高性能芯糸
        ("CORE_PE_ULTRA", "PE超高強度芯糸 スペクトラ", "芯糸", "M"),
        ("CORE_NY_FLEX", "ナイロン柔軟芯糸 高弾性", "芯糸", "M"),
        
        # ============= 成形品・梱包資材 =============
        # 既存成形品（詳細化）
        ("MOLD_001", "100m用プラスチックスプール 標準", "成形品", "個"),
        ("MOLD_002", "150m用プラスチックスプール 中", "成形品", "個"),
        ("MOLD_003", "200m用プラスチックスプール 大", "成形品", "個"),
        
        # 新規高級成形品
        ("MOLD_METAL_300", "300m用金属スプール プレミアム", "成形品", "個"),
        ("MOLD_CARBON_500", "500m用カーボンスプール 軽量", "成形品", "個"),
        
        # 既存梱包資材（詳細化）
        ("PKG_001", "ブリスターパック 100m用 標準", "梱包資材", "個"),
        ("PKG_002", "ブリスターパック 150m用 中", "梱包資材", "個"),
        ("PKG_003", "製品ラベル 多色印刷", "梱包資材", "枚"),
        
        # 新規高級梱包資材
        ("PKG_PREMIUM_BOX", "プレミアム製品用化粧箱", "梱包資材", "個"),
        ("PKG_TOURNAMENT_LABEL", "トーナメント用特製ラベル", "梱包資材", "枚"),
        ("PKG_INSTRUCTION_CARD", "使用説明カード", "梱包資材", "枚"),
        
        # ============= 工程材料 =============
        ("PROC_LUBRICANT", "糸加工用潤滑剤 高性能", "原糸", "KG"),
        ("PROC_STABILIZER", "糸品質安定剤 UV耐性", "原糸", "KG"),
        ("PROC_DYE_BLUE", "青色染料 高発色型", "原糸", "KG"),
        ("PROC_DYE_GREEN", "緑色染料 耐光性", "原糸", "KG"),
        ("PROC_CLEAR_AGENT", "透明処理剤 高透明", "原糸", "KG"),
    ]
    
    print(f"📦 {len(sample_items)}個のアイテムを作成中...")
    for item_id, item_name, item_type, unit in sample_items:
        try:
            success = bom_manager.add_item(
                item_id=item_id,
                item_name=item_name,
                item_type=item_type,
                unit_of_measure=unit
            )
            if success:
                print(f"  ✅ {item_name}")
            else:
                print(f"  ⚠️ 既存: {item_name}")
        except Exception as e:
            print(f"  ❌ エラー {item_name}: {e}")
    
    # 大幅に拡張されたBOM構成の作成
    bom_relations = [
        # ============= 完成品レベルのBOM =============
        
        # 既存製品の詳細化
        ("PRODUCT_001", "BRAID_PE_X8_ULTRA", 100.0, "Main Material"),
        ("PRODUCT_001", "MOLD_001", 1.0, "Container"),
        ("PRODUCT_001", "PKG_001", 1.0, "Packaging"),
        ("PRODUCT_001", "PKG_INSTRUCTION_CARD", 1.0, "Packaging"),
        
        ("PRODUCT_002", "BRAID_NY_X4_HYBRID", 150.0, "Main Material"),
        ("PRODUCT_002", "MOLD_002", 1.0, "Container"),
        ("PRODUCT_002", "PKG_002", 1.0, "Packaging"),
        ("PRODUCT_002", "PKG_INSTRUCTION_CARD", 1.0, "Packaging"),
        
        ("PRODUCT_003", "BRAID_FC_MONO", 200.0, "Main Material"),
        ("PRODUCT_003", "MOLD_003", 1.0, "Container"),
        ("PRODUCT_003", "PKG_003", 2.0, "Packaging"),
        ("PRODUCT_003", "PKG_INSTRUCTION_CARD", 1.0, "Packaging"),
        
        # 新規プレミアム製品のBOM
        ("PREMIUM_PE_10", "BRAID_PE_X8_ULTRA", 1.0, "Main Material"),
        ("PREMIUM_PE_10", "CORE_PE_ULTRA", 0.1, "Core Thread"),
        ("PREMIUM_PE_10", "PROC_STABILIZER", 0.05, "Process Material"),
        
        ("PREMIUM_NY_15", "BRAID_NY_X4_HYBRID", 1.0, "Main Material"),
        ("PREMIUM_NY_15", "CORE_NY_FLEX", 0.1, "Core Thread"),
        ("PREMIUM_NY_15", "PROC_LUBRICANT", 0.03, "Process Material"),
        
        ("TOURNAMENT_FC_20", "BRAID_FC_MONO", 1.0, "Main Material"),
        ("TOURNAMENT_FC_20", "PROC_CLEAR_AGENT", 0.02, "Process Material"),
        
        ("HYBRID_LINE_25", "BRAID_NY_X4_HYBRID", 0.6, "Main Material"),
        ("HYBRID_LINE_25", "BRAID_PE_X8_ULTRA", 0.4, "Main Material"),
        ("HYBRID_LINE_25", "CORE_PE_ULTRA", 0.05, "Core Thread"),
        
        # スプール製品のBOM
        ("SPOOL_PE_10_300", "PREMIUM_PE_10", 300.0, "Main Material"),
        ("SPOOL_PE_10_300", "MOLD_METAL_300", 1.0, "Container"),
        ("SPOOL_PE_10_300", "PKG_PREMIUM_BOX", 1.0, "Packaging"),
        ("SPOOL_PE_10_300", "PKG_TOURNAMENT_LABEL", 2.0, "Packaging"),
        
        ("SPOOL_NY_15_500", "PREMIUM_NY_15", 500.0, "Main Material"),
        ("SPOOL_NY_15_500", "MOLD_CARBON_500", 1.0, "Container"),
        ("SPOOL_NY_15_500", "PKG_PREMIUM_BOX", 1.0, "Packaging"),
        ("SPOOL_NY_15_500", "PKG_TOURNAMENT_LABEL", 2.0, "Packaging"),
        
        ("SPOOL_FC_20_200", "TOURNAMENT_FC_20", 200.0, "Main Material"),
        ("SPOOL_FC_20_200", "MOLD_003", 1.0, "Container"),
        ("SPOOL_FC_20_200", "PKG_PREMIUM_BOX", 1.0, "Packaging"),
        ("SPOOL_FC_20_200", "PKG_TOURNAMENT_LABEL", 1.0, "Packaging"),
        
        # ============= 製紐糸レベルのBOM =============
        
        # 既存製紐糸の詳細化
        ("BRAID_001", "TWIST_NY6_S_035", 8.0, "Main Braid Thread"),
        ("BRAID_001", "CORE_001", 1.0, "Core Thread"),
        ("BRAID_001", "PROC_LUBRICANT", 0.1, "Process Material"),
        
        ("BRAID_002", "TWIST_PE_Z_040", 4.0, "Main Braid Thread"),
        ("BRAID_002", "CORE_002", 1.0, "Core Thread"),
        ("BRAID_002", "PROC_STABILIZER", 0.08, "Process Material"),
        
        ("BRAID_003", "TWIST_NY66_S_050", 16.0, "Main Braid Thread"),
        ("BRAID_003", "CORE_PE_ULTRA", 1.0, "Core Thread"),
        ("BRAID_003", "PROC_LUBRICANT", 0.15, "Process Material"),
        
        # 新規高度な製紐糸のBOM
        ("BRAID_PE_X8_ULTRA", "TWIST_PE_Z_040", 8.0, "Main Braid Thread"),
        ("BRAID_PE_X8_ULTRA", "CORE_PE_ULTRA", 1.0, "Core Thread"),
        ("BRAID_PE_X8_ULTRA", "PROC_STABILIZER", 0.1, "Process Material"),
        
        ("BRAID_NY_X4_HYBRID", "TWIST_NY6_S_035", 2.0, "Main Braid Thread"),
        ("BRAID_NY_X4_HYBRID", "TWIST_PE_Z_040", 2.0, "Main Braid Thread"),
        ("BRAID_NY_X4_HYBRID", "CORE_NY_FLEX", 0.5, "Core Thread"),
        ("BRAID_NY_X4_HYBRID", "PROC_LUBRICANT", 0.05, "Process Material"),
        
        ("BRAID_FC_MONO", "DYE_FC_CLEAR_035", 1.0, "Main Material"),
        ("BRAID_FC_MONO", "PROC_CLEAR_AGENT", 0.02, "Process Material"),
        
        # ============= PS糸・後PS糸レベルのBOM =============
        
        # 既存PS糸の詳細化
        ("PS_001", "DYE_NY6_BLUE_020", 1.0, "Main Material"),
        ("PS_001", "PROC_LUBRICANT", 0.05, "Process Material"),
        
        ("PS_002", "DYE_NY6_GREEN_025", 1.0, "Main Material"),
        ("PS_002", "PROC_STABILIZER", 0.05, "Process Material"),
        
        ("PS_003", "DYE_PE_CLEAR_030", 1.0, "Main Material"),
        ("PS_003", "PROC_CLEAR_AGENT", 0.03, "Process Material"),
        
        # 新規撚り糸のBOM
        ("TWIST_NY6_S_035", "DYE_NY6_BLUE_020", 0.9, "Main Material"),
        ("TWIST_NY6_S_035", "PROC_LUBRICANT", 0.1, "Process Material"),
        
        ("TWIST_PE_Z_040", "DYE_PE_CLEAR_030", 0.9, "Main Material"),
        ("TWIST_PE_Z_040", "PROC_STABILIZER", 0.1, "Process Material"),
        
        ("TWIST_NY66_S_050", "DYE_NY6_GREEN_025", 0.85, "Main Material"),
        ("TWIST_NY66_S_050", "PROC_LUBRICANT", 0.15, "Process Material"),
        
        # ============= 染色糸レベルのBOM =============
        
        # 既存染色糸の詳細化
        ("DYE_001", "RAW_NY6_ULTRA", 0.95, "Main Material"),
        ("DYE_001", "PROC_DYE_BLUE", 0.05, "Process Material"),
        
        ("DYE_002", "RAW_NY6_ULTRA", 0.95, "Main Material"),
        ("DYE_002", "PROC_DYE_GREEN", 0.05, "Process Material"),
        
        ("DYE_003", "RAW_001", 0.95, "Main Material"),
        ("DYE_003", "PROC_DYE_BLUE", 0.03, "Process Material"),  # 蛍光用特殊配合
        ("DYE_003", "PROC_STABILIZER", 0.02, "Process Material"),
        
        # 新規詳細染色糸のBOM
        ("DYE_NY6_BLUE_020", "RAW_NY6_ULTRA", 0.95, "Main Material"),
        ("DYE_NY6_BLUE_020", "PROC_DYE_BLUE", 0.05, "Process Material"),
        
        ("DYE_NY6_GREEN_025", "RAW_NY6_ULTRA", 0.95, "Main Material"),
        ("DYE_NY6_GREEN_025", "PROC_DYE_GREEN", 0.05, "Process Material"),
        
        ("DYE_PE_CLEAR_030", "RAW_PE_SPECTRA", 0.98, "Main Material"),
        ("DYE_PE_CLEAR_030", "PROC_CLEAR_AGENT", 0.02, "Process Material"),
        
        ("DYE_FC_CLEAR_035", "RAW_FC_PVDF", 0.95, "Main Material"),
        ("DYE_FC_CLEAR_035", "PROC_CLEAR_AGENT", 0.05, "Process Material"),
        
        # ============= 芯糸レベルのBOM =============
        
        # 芯糸の原材料ベースBOM
        ("CORE_001", "RAW_001", 0.9, "Main Material"),
        ("CORE_002", "RAW_PE_SPECTRA", 0.9, "Main Material"),
        ("CORE_PE_ULTRA", "RAW_PE_SPECTRA", 0.95, "Main Material"),
        ("CORE_PE_ULTRA", "PROC_STABILIZER", 0.05, "Process Material"),
        ("CORE_NY_FLEX", "RAW_NY66_PREMIUM", 0.92, "Main Material"),
        ("CORE_NY_FLEX", "PROC_LUBRICANT", 0.08, "Process Material"),
    ]
    
    print(f"\n🔗 {len(bom_relations)}個のBOM構成を追加中...")
    total_added = 0
    for parent_id, component_id, quantity, usage_type in bom_relations:
        try:
            success = bom_manager.add_bom_component(
                parent_item_id=parent_id,
                component_item_id=component_id,
                quantity=quantity,
                usage_type=usage_type
            )
            
            if success:
                parent_item = bom_manager.get_item(parent_id)
                component_item = bom_manager.get_item(component_id)
                if parent_item and component_item:
                    print(f"  ✅ {parent_item['item_name']} ← {component_item['item_name']} ({quantity})")
                    total_added += 1
            else:
                print(f"  ⚠️ 既存または追加失敗: {parent_id} ← {component_id}")
                
        except Exception as e:
            print(f"  ❌ エラー: {parent_id} ← {component_id} - {e}")
    
    # Oracle連携風にoracle_product_codeを設定
    conn = sqlite3.connect('bom_database_dev.db')
    cursor = conn.cursor()
    
    # 特定のアイテムにOracle製品コードを付与
    oracle_items = [
        'PREMIUM_PE_10', 'PREMIUM_NY_15', 'TOURNAMENT_FC_20', 'HYBRID_LINE_25',
        'BRAID_PE_X8_ULTRA', 'BRAID_NY_X4_HYBRID', 'BRAID_FC_MONO',
        'DYE_NY6_BLUE_020', 'DYE_NY6_GREEN_025', 'DYE_PE_CLEAR_030',
        'RAW_NY6_ULTRA', 'RAW_PE_SPECTRA', 'RAW_FC_PVDF'
    ]
    
    print(f"\n🌐 Oracle連携アイテムを設定中...")
    for item_id in oracle_items:
        cursor.execute("""
            UPDATE items SET oracle_product_code = ? 
            WHERE item_id = ?
        """, (f"ORA-{item_id}", item_id))
        print(f"  ✅ {item_id} → ORA-{item_id}")
    
    conn.commit()
    conn.close()
    
    # 統計表示
    try:
        conn = sqlite3.connect('bom_database_dev.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM items")
        item_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bom_components")
        bom_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT parent_item_id) 
            FROM bom_components
        """)
        parents_with_bom = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM items WHERE oracle_product_code IS NOT NULL")
        oracle_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n✅ BOM構造拡張完了！")
        print(f"📊 最終統計:")
        print(f"  • 総アイテム数: {item_count}")
        print(f"  • 総BOM構成数: {bom_count}")
        print(f"  • BOM構成を持つ親アイテム数: {parents_with_bom}")
        print(f"  • Oracle連携アイテム数: {oracle_count}")
        print(f"  • 新規BOM構成追加: {total_added} 件")
        
    except Exception as e:
        print(f"統計取得エラー: {e}")

if __name__ == "__main__":
    enhance_bom_data() 