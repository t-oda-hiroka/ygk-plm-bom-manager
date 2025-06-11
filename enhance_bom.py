#!/usr/bin/env python3
"""豊富なBOM構造を追加するスクリプト"""

import sqlite3
from bom_manager import BOMManager

def enhance_bom_data():
    print('🔧 豊富なBOM構造を追加中...')
    bom_manager = BOMManager('bom_database_dev.db')
    
    # 追加アイテムの作成
    additional_items = [
        ('PREMIUM_PE_10', 'プレミアムPEブレイデッド 1.0号 高強度', '完成品', 'M'),
        ('PREMIUM_NY_15', 'プレミアムナイロン 1.5号 耐摩耗', '完成品', 'M'),
        ('TOURNAMENT_FC_20', 'トーナメント用フロロカーボン 2.0号', '完成品', 'M'),
        ('HYBRID_LINE_25', 'ハイブリッドライン PE-NY複合 2.5号', '完成品', 'M'),
        ('BRAID_PE_X8_ULTRA', 'PE編み糸 X8超高密度 スペクトラ芯', '製紐糸', 'M'),
        ('BRAID_NY_X4_HYBRID', 'ナイロン-PE複合編み糸 X4', '製紐糸', 'M'),
        ('BRAID_FC_MONO', 'フロロカーボン単糸 高透明', '製紐糸', 'M'),
        ('TWIST_NY6_S_035', 'ナイロン6撚り糸 S撚り 0.35mm', '後PS糸', 'M'),
        ('TWIST_PE_Z_040', 'PE撚り糸 Z撚り 0.40mm', '後PS糸', 'M'),
        ('DYE_NY6_BLUE_020', 'ナイロン6染色糸 青 0.20mm', '染色糸', 'M'),
        ('DYE_NY6_GREEN_025', 'ナイロン6染色糸 緑 0.25mm', '染色糸', 'M'),
        ('DYE_PE_CLEAR_030', 'PE透明糸 0.30mm UV耐性', '染色糸', 'M'),
        ('RAW_NY6_ULTRA', 'ナイロン6超高強度原糸 スーパータフ', '原糸', 'KG'),
        ('RAW_PE_SPECTRA', 'PE超高分子量原糸 スペクトラ', '原糸', 'KG'),
        ('RAW_FC_PVDF', 'フロロカーボン原糸 PVDF高純度', '原糸', 'KG'),
        ('CORE_PE_ULTRA', 'PE超高強度芯糸 スペクトラ', '芯糸', 'M'),
        ('CORE_NY_FLEX', 'ナイロン柔軟芯糸 高弾性', '芯糸', 'M'),
        ('MOLD_METAL_300', '300m用金属スプール プレミアム', '成形品', '個'),
        ('PKG_PREMIUM_BOX', 'プレミアム製品用化粧箱', '梱包資材', '個'),
        ('PKG_TOURNAMENT_LABEL', 'トーナメント用特製ラベル', '梱包資材', '枚'),
        ('PROC_LUBRICANT', '糸加工用潤滑剤 高性能', '原糸', 'KG'),
        ('PROC_STABILIZER', '糸品質安定剤 UV耐性', '原糸', 'KG'),
        ('PROC_DYE_BLUE', '青色染料 高発色型', '原糸', 'KG'),
        ('PROC_DYE_GREEN', '緑色染料 耐光性', '原糸', 'KG'),
        ('PROC_CLEAR_AGENT', '透明処理剤 高透明', '原糸', 'KG'),
    ]
    
    count = 0
    for item_id, item_name, item_type, unit in additional_items:
        if bom_manager.add_item(item_id=item_id, item_name=item_name, item_type=item_type, unit_of_measure=unit):
            count += 1
            print(f'  ✅ {item_name}')
    
    print(f'📦 {count}個のアイテムを追加しました')
    
    # BOM構成の追加
    bom_relations = [
        # プレミアム製品のBOM
        ('PREMIUM_PE_10', 'BRAID_PE_X8_ULTRA', 1.0, 'Main Material'),
        ('PREMIUM_PE_10', 'CORE_PE_ULTRA', 0.1, 'Core Thread'),
        ('PREMIUM_PE_10', 'PROC_STABILIZER', 0.05, 'Process Material'),
        
        ('PREMIUM_NY_15', 'BRAID_NY_X4_HYBRID', 1.0, 'Main Material'),
        ('PREMIUM_NY_15', 'CORE_NY_FLEX', 0.1, 'Core Thread'),
        ('PREMIUM_NY_15', 'PROC_LUBRICANT', 0.03, 'Process Material'),
        
        ('TOURNAMENT_FC_20', 'BRAID_FC_MONO', 1.0, 'Main Material'),
        ('TOURNAMENT_FC_20', 'PROC_CLEAR_AGENT', 0.02, 'Process Material'),
        
        ('HYBRID_LINE_25', 'BRAID_NY_X4_HYBRID', 0.6, 'Main Material'),
        ('HYBRID_LINE_25', 'BRAID_PE_X8_ULTRA', 0.4, 'Main Material'),
        ('HYBRID_LINE_25', 'CORE_PE_ULTRA', 0.05, 'Core Thread'),
        
        # 製紐糸のBOM
        ('BRAID_PE_X8_ULTRA', 'TWIST_PE_Z_040', 8.0, 'Main Braid Thread'),
        ('BRAID_PE_X8_ULTRA', 'CORE_PE_ULTRA', 1.0, 'Core Thread'),
        ('BRAID_PE_X8_ULTRA', 'PROC_STABILIZER', 0.1, 'Process Material'),
        
        ('BRAID_NY_X4_HYBRID', 'TWIST_NY6_S_035', 2.0, 'Main Braid Thread'),
        ('BRAID_NY_X4_HYBRID', 'TWIST_PE_Z_040', 2.0, 'Main Braid Thread'),
        ('BRAID_NY_X4_HYBRID', 'CORE_NY_FLEX', 0.5, 'Core Thread'),
        ('BRAID_NY_X4_HYBRID', 'PROC_LUBRICANT', 0.05, 'Process Material'),
        
        ('BRAID_FC_MONO', 'DYE_PE_CLEAR_030', 1.0, 'Main Material'),
        ('BRAID_FC_MONO', 'PROC_CLEAR_AGENT', 0.02, 'Process Material'),
        
        # 撚り糸のBOM
        ('TWIST_NY6_S_035', 'DYE_NY6_BLUE_020', 0.9, 'Main Material'),
        ('TWIST_NY6_S_035', 'PROC_LUBRICANT', 0.1, 'Process Material'),
        
        ('TWIST_PE_Z_040', 'DYE_PE_CLEAR_030', 0.9, 'Main Material'),
        ('TWIST_PE_Z_040', 'PROC_STABILIZER', 0.1, 'Process Material'),
        
        # 染色糸のBOM
        ('DYE_NY6_BLUE_020', 'RAW_NY6_ULTRA', 0.95, 'Main Material'),
        ('DYE_NY6_BLUE_020', 'PROC_DYE_BLUE', 0.05, 'Process Material'),
        
        ('DYE_NY6_GREEN_025', 'RAW_NY6_ULTRA', 0.95, 'Main Material'),
        ('DYE_NY6_GREEN_025', 'PROC_DYE_GREEN', 0.05, 'Process Material'),
        
        ('DYE_PE_CLEAR_030', 'RAW_PE_SPECTRA', 0.98, 'Main Material'),
        ('DYE_PE_CLEAR_030', 'PROC_CLEAR_AGENT', 0.02, 'Process Material'),
        
        # 芯糸のBOM
        ('CORE_PE_ULTRA', 'RAW_PE_SPECTRA', 0.95, 'Main Material'),
        ('CORE_PE_ULTRA', 'PROC_STABILIZER', 0.05, 'Process Material'),
        ('CORE_NY_FLEX', 'RAW_NY6_ULTRA', 0.92, 'Main Material'),
        ('CORE_NY_FLEX', 'PROC_LUBRICANT', 0.08, 'Process Material'),
        
        # 既存製品の強化
        ('PRODUCT_001', 'BRAID_PE_X8_ULTRA', 100.0, 'Main Material'),
        ('PRODUCT_002', 'BRAID_NY_X4_HYBRID', 150.0, 'Main Material'),
        ('PRODUCT_003', 'BRAID_FC_MONO', 200.0, 'Main Material'),
        
        ('BRAID_001', 'TWIST_NY6_S_035', 8.0, 'Main Braid Thread'),
        ('BRAID_001', 'PROC_LUBRICANT', 0.1, 'Process Material'),
        
        ('BRAID_002', 'TWIST_PE_Z_040', 4.0, 'Main Braid Thread'),
        ('BRAID_002', 'PROC_STABILIZER', 0.08, 'Process Material'),
        
        ('BRAID_003', 'TWIST_NY6_S_035', 16.0, 'Main Braid Thread'),
        ('BRAID_003', 'CORE_PE_ULTRA', 1.0, 'Core Thread'),
        ('BRAID_003', 'PROC_LUBRICANT', 0.15, 'Process Material'),
        
        ('PS_001', 'DYE_NY6_BLUE_020', 1.0, 'Main Material'),
        ('PS_001', 'PROC_LUBRICANT', 0.05, 'Process Material'),
        
        ('PS_002', 'DYE_NY6_GREEN_025', 1.0, 'Main Material'),
        ('PS_002', 'PROC_STABILIZER', 0.05, 'Process Material'),
        
        ('PS_003', 'DYE_PE_CLEAR_030', 1.0, 'Main Material'),
        ('PS_003', 'PROC_CLEAR_AGENT', 0.03, 'Process Material'),
        
        ('DYE_001', 'RAW_NY6_ULTRA', 0.95, 'Main Material'),
        ('DYE_001', 'PROC_DYE_BLUE', 0.05, 'Process Material'),
        
        ('DYE_002', 'RAW_NY6_ULTRA', 0.95, 'Main Material'),
        ('DYE_002', 'PROC_DYE_GREEN', 0.05, 'Process Material'),
        
        ('DYE_003', 'RAW_001', 0.95, 'Main Material'),
        ('DYE_003', 'PROC_DYE_BLUE', 0.03, 'Process Material'),
        ('DYE_003', 'PROC_STABILIZER', 0.02, 'Process Material'),
        
        ('CORE_001', 'RAW_001', 0.9, 'Main Material'),
        ('CORE_002', 'RAW_PE_SPECTRA', 0.9, 'Main Material'),
    ]
    
    count_bom = 0
    for parent_id, component_id, quantity, usage_type in bom_relations:
        if bom_manager.add_bom_component(parent_item_id=parent_id, component_item_id=component_id, quantity=quantity, usage_type=usage_type):
            count_bom += 1
            print(f'  🔗 {parent_id} ← {component_id} ({quantity})')
    
    print(f'🔗 {count_bom}個のBOM構成を追加しました')
    
    # Oracle連携設定
    conn = sqlite3.connect('bom_database_dev.db')
    cursor = conn.cursor()
    oracle_items = ['PREMIUM_PE_10', 'PREMIUM_NY_15', 'TOURNAMENT_FC_20', 'HYBRID_LINE_25', 'BRAID_PE_X8_ULTRA', 'BRAID_NY_X4_HYBRID', 'DYE_NY6_BLUE_020', 'DYE_NY6_GREEN_025', 'RAW_NY6_ULTRA', 'RAW_PE_SPECTRA', 'RAW_FC_PVDF']
    for item_id in oracle_items:
        cursor.execute("UPDATE items SET oracle_product_code = ? WHERE item_id = ?", (f"ORA-{item_id}", item_id))
    conn.commit()
    conn.close()
    print(f'🌐 {len(oracle_items)}個のOracle連携アイテムを設定しました')
    
    # 統計表示
    conn = sqlite3.connect('bom_database_dev.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM items")
    item_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bom_components")
    bom_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT parent_item_id) FROM bom_components")
    parents_with_bom = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM items WHERE oracle_product_code IS NOT NULL")
    oracle_count = cursor.fetchone()[0]
    conn.close()
    
    print(f'\n✅ BOM構造拡張完了！')
    print(f'📊 最終統計:')
    print(f'  • 総アイテム数: {item_count}')
    print(f'  • 総BOM構成数: {bom_count}')
    print(f'  • BOM構成を持つ親アイテム数: {parents_with_bom}')
    print(f'  • Oracle連携アイテム数: {oracle_count}')

if __name__ == '__main__':
    enhance_bom_data() 