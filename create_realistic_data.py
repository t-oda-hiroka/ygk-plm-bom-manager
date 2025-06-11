#!/usr/bin/env python3
"""
釣り糸製造業 リアルデータ作成スクリプト
実際の製造業界のデータパターンを模したマスターデータとロットデータを生成
"""

import sqlite3
import random
from datetime import datetime, timedelta
from bom_manager import BOMManager

# 実際の釣り糸製造データパターン
RAW_MATERIALS = [
    # ナイロン原糸 (実際のグレード)
    {'code': 'NY6-RAW-001', 'name': 'ナイロン6原糸 (高強度)', 'type': '原糸', 'unit': 'KG', 'material': 'ナイロン'},
    {'code': 'NY66-RAW-002', 'name': 'ナイロン66原糸 (超高強度)', 'type': '原糸', 'unit': 'KG', 'material': 'ナイロン'},
    {'code': 'NY6-RAW-003', 'name': 'ナイロン6原糸 (標準)', 'type': '原糸', 'unit': 'KG', 'material': 'ナイロン'},
    
    # フロロカーボン原糸
    {'code': 'FC-PVDF-001', 'name': 'フロロカーボン原糸 (PVDF)', 'type': '原糸', 'unit': 'KG', 'material': 'フロロカーボン'},
    {'code': 'FC-PVDF-002', 'name': 'フロロカーボン原糸 (高透明)', 'type': '原糸', 'unit': 'KG', 'material': 'フロロカーボン'},
    
    # PE原糸 (実際のグレード)
    {'code': 'PE-UHMW-001', 'name': 'PE原糸 (超高分子量)', 'type': '原糸', 'unit': 'KG', 'material': 'PE'},
    {'code': 'PE-UHMW-002', 'name': 'PE原糸 (高強度グレード)', 'type': '原糸', 'unit': 'KG', 'material': 'PE'},
    
    # 染料・化学品（原糸として分類）
    {'code': 'DYE-BLU-001', 'name': '青色染料 (釣り糸用)', 'type': '原糸', 'unit': 'KG', 'material': '化学品'},
    {'code': 'DYE-GRN-001', 'name': '緑色染料 (釣り糸用)', 'type': '原糸', 'unit': 'KG', 'material': '化学品'},
    {'code': 'DYE-CLR-001', 'name': '透明処理剤', 'type': '原糸', 'unit': 'KG', 'material': '化学品'},
]

INTERMEDIATE_PRODUCTS = [
    # 染色糸
    {'code': 'NY6-DYE-BLU-020', 'name': 'ナイロン6染色糸 青 0.20mm', 'type': '染色糸', 'unit': 'M', 'diameter': 0.20},
    {'code': 'NY6-DYE-GRN-025', 'name': 'ナイロン6染色糸 緑 0.25mm', 'type': '染色糸', 'unit': 'M', 'diameter': 0.25},
    {'code': 'FC-CLR-030', 'name': 'フロロカーボン透明糸 0.30mm', 'type': '染色糸', 'unit': 'M', 'diameter': 0.30},
    
    # 撚り糸
    {'code': 'NY66-S-035', 'name': 'ナイロン66撚り糸 S撚り 0.35mm', 'type': '後PS糸', 'unit': 'M', 'twist': 'S'},
    {'code': 'NY66-Z-040', 'name': 'ナイロン66撚り糸 Z撚り 0.40mm', 'type': '後PS糸', 'unit': 'M', 'twist': 'Z'},
    
    # 編み込み糸
    {'code': 'PE-X8-150', 'name': 'PE編み込み糸 8本編み 1.5号', 'type': '製紐糸', 'unit': 'M', 'knit': 'X8'},
    {'code': 'PE-X4-200', 'name': 'PE編み込み糸 4本編み 2.0号', 'type': '製紐糸', 'unit': 'M', 'knit': 'X4'},
    {'code': 'PE-X8-300', 'name': 'PE編み込み糸 8本編み 3.0号', 'type': '製紐糸', 'unit': 'M', 'knit': 'X8'},
]

FINISHED_PRODUCTS = [
    # モノフィラメント (単糸)
    {'code': 'MONO-NY6-10', 'name': 'モノフィラメント 1.0号 (ナイロン6)', 'type': '完成品', 'unit': 'M', 'line_type': 'モノ'},
    {'code': 'MONO-NY6-15', 'name': 'モノフィラメント 1.5号 (ナイロン6)', 'type': '完成品', 'unit': 'M', 'line_type': 'モノ'},
    {'code': 'MONO-FC-20', 'name': 'モノフィラメント 2.0号 (フロロカーボン)', 'type': '完成品', 'unit': 'M', 'line_type': 'モノ'},
    
    # PE編み込みライン
    {'code': 'BRAID-PE-10', 'name': 'PEブレイデッド 1.0号 8本編み', 'type': '完成品', 'unit': 'M', 'line_type': '編み'},
    {'code': 'BRAID-PE-15', 'name': 'PEブレイデッド 1.5号 8本編み', 'type': '完成品', 'unit': 'M', 'line_type': '編み'},
    {'code': 'BRAID-PE-20', 'name': 'PEブレイデッド 2.0号 4本編み', 'type': '完成品', 'unit': 'M', 'line_type': '編み'},
    
    # スプール巻き製品
    {'code': 'SPOOL-MONO-NY6-10-150', 'name': 'モノフィラメント1.0号 150mスプール', 'type': '完成品', 'unit': '個', 'package': 'スプール'},
    {'code': 'SPOOL-BRAID-PE-15-200', 'name': 'PEブレイデッド1.5号 200mスプール', 'type': '完成品', 'unit': '個', 'package': 'スプール'},
]

# 梱包材料
PACKAGING_MATERIALS = [
    {'code': 'PKG-SPOOL-150', 'name': '150mスプール (プラスチック)', 'type': '梱包資材', 'unit': '個'},
    {'code': 'PKG-SPOOL-200', 'name': '200mスプール (プラスチック)', 'type': '梱包資材', 'unit': '個'},
    {'code': 'PKG-BOX-SINGLE', 'name': '個装箱 (単品用)', 'type': '梱包資材', 'unit': '枚'},
    {'code': 'PKG-LABEL-MONO', 'name': 'モノフィラメント用ラベル', 'type': '梱包資材', 'unit': '枚'},
    {'code': 'PKG-LABEL-BRAID', 'name': 'ブレイデッド用ラベル', 'type': '梱包資材', 'unit': '枚'},
]

def create_realistic_items(bom_manager):
    """リアルなアイテムマスターを作成"""
    print("🎣 釣り糸製造業のリアルなアイテムマスターを作成中...")
    
    all_items = RAW_MATERIALS + INTERMEDIATE_PRODUCTS + FINISHED_PRODUCTS + PACKAGING_MATERIALS
    
    for item in all_items:
        try:
            result = bom_manager.add_item(
                item_id=item['code'],
                item_name=item['name'],
                item_type=item['type'],
                unit_of_measure=item['unit'],
                material_type=item.get('material', ''),
                twist_type=item.get('twist', ''),
                knit_type=item.get('knit', ''),
                source='oracle_sync'  # Oracleからのデータとして記録
            )
            if result:
                print(f"  ✓ {item['code']}: {item['name']}")
            else:
                print(f"  ⚠ 既存: {item['code']}")
        except Exception as e:
            print(f"  ✗ エラー {item['code']}: {e}")

def create_realistic_lots(bom_manager):
    """リアルなロットデータを作成"""
    print("\n📦 リアルなロットデータを作成中...")
    
    # ロット作成のベース日付
    base_date = datetime.now() - timedelta(days=30)
    
    lots_to_create = [
        # 原材料ロット（入荷分）
        {
            'item_code': 'NY6-RAW-001',
            'production_date': base_date.strftime('%Y-%m-%d'),
            'planned_quantity': 500.0,
            'actual_quantity': 498.5,
            'quality_grade': 'A',
            'location': '原材料倉庫A-01',
            'supplier': 'ナイロン化学工業'
        },
        {
            'item_code': 'PE-UHMW-001',
            'production_date': (base_date + timedelta(days=2)).strftime('%Y-%m-%d'),
            'planned_quantity': 300.0,
            'actual_quantity': 299.8,
            'quality_grade': 'A',
            'location': '原材料倉庫A-02',
            'supplier': 'PE素材株式会社'
        },
        {
            'item_code': 'FC-PVDF-001',
            'production_date': (base_date + timedelta(days=3)).strftime('%Y-%m-%d'),
            'planned_quantity': 200.0,
            'actual_quantity': 201.2,
            'quality_grade': 'A',
            'location': '原材料倉庫A-03',
            'supplier': 'フロロポリマー工業'
        },
        
        # 中間製品ロット
        {
            'item_code': 'NY6-DYE-BLU-020',
            'production_date': (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            'planned_quantity': 10000.0,
            'actual_quantity': 9850.0,
            'quality_grade': 'A',
            'location': '製造工程-染色A',
            'equipment': '染色機No.3'
        },
        {
            'item_code': 'PE-X8-150',
            'production_date': (base_date + timedelta(days=8)).strftime('%Y-%m-%d'),
            'planned_quantity': 5000.0,
            'actual_quantity': 4980.0,
            'quality_grade': 'A',
            'location': '製造工程-編み込みB',
            'equipment': '8本編み機No.2'
        },
        
        # 完成品ロット
        {
            'item_code': 'MONO-NY6-15',
            'production_date': (base_date + timedelta(days=10)).strftime('%Y-%m-%d'),
            'planned_quantity': 3000.0,
            'actual_quantity': 2980.0,
            'quality_grade': 'A',
            'location': '製品倉庫-1F',
            'equipment': '押出成形機No.5'
        },
        {
            'item_code': 'BRAID-PE-15',
            'production_date': (base_date + timedelta(days=12)).strftime('%Y-%m-%d'),
            'planned_quantity': 2500.0,
            'actual_quantity': 2475.0,
            'quality_grade': 'A',
            'location': '製品倉庫-1F',
            'equipment': '最終編み込み機No.1'
        },
        
        # スプール製品
        {
            'item_code': 'SPOOL-MONO-NY6-10-150',
            'production_date': (base_date + timedelta(days=15)).strftime('%Y-%m-%d'),
            'planned_quantity': 100.0,
            'actual_quantity': 100.0,
            'quality_grade': 'A',
            'location': '製品倉庫-包装エリア',
            'equipment': '自動スプール巻き機No.3'
        },
    ]
    
    lot_count = 0
    created_lots = []  # 作成されたロットIDを記録
    
    for lot_data in lots_to_create:
        try:
            
            # 工程コードを決定（アイテムタイプに基づく）
            item_type_to_process = {
                '原糸': 'P',      # Process (前処理) - 原材料、染料、処理剤を含む
                '染色糸': 'W',    # Winding (巻き取り)
                '後PS糸': 'B',    # Braiding (撚り)
                '製紐糸': 'S',    # Spinning (編み込み)
                '完成品': 'C',    # Coating (仕上げ)
                '梱包資材': 'E',  # End (最終)
                '成形品': 'F'     # Finishing (包装)
            }
            
            # アイテム情報を取得してprocess_codeを決定
            process_code = 'P'  # デフォルト
            try:
                with sqlite3.connect('bom_database_dev.db') as temp_conn:
                    cursor = temp_conn.execute("SELECT item_type FROM items WHERE item_id = ?", (lot_data['item_code'],))
                    item_row = cursor.fetchone()
                    
                    if item_row:
                        process_code = item_type_to_process.get(item_row[0], 'P')
            except Exception as e:
                print(f"    ⚠ アイテム情報取得エラー: {e}")
                # デフォルト値を使用
            
            # ロット作成
            try:
                result = bom_manager.create_lot(
                    item_id=lot_data['item_code'],
                    process_code=process_code,
                    planned_quantity=lot_data['planned_quantity'],
                    production_date=lot_data['production_date'],
                    actual_quantity=lot_data['actual_quantity'],
                    quality_grade=lot_data['quality_grade'],
                    location=lot_data.get('location'),
                    equipment_id=lot_data.get('equipment'),
                    operator_id='OP001'  # 作業者ID
                )
                
                if result:
                    print(f"  ✓ ロット作成: {result} ({lot_data['item_code']})")
                    created_lots.append({'lot_id': result, 'item_code': lot_data['item_code']})
                    lot_count += 1
                else:
                    print(f"  ⚠ ロット作成失敗")
            except Exception as e:
                print(f"  ✗ ロット作成エラー ({lot_data['item_code']}): {e}")
                import traceback
                print(f"    詳細: {traceback.format_exc()}")
                continue
                
        except Exception as e:
            print(f"  ✗ ロット作成エラー: {e}")
    
    return created_lots

def create_lot_genealogy_relationships(bom_manager, created_lots):
    """リアルなロット系統関係を作成"""
    print("\n🔗 ロット系統関係を作成中...")
    
    if len(created_lots) < 4:
        print("  ⚠ 系統関係を作成するにはより多くのロットが必要です")
        return
    
    # 実際に作成されたロットから系統関係を作成
    # アイテムコード別にロットをグループ化
    lots_by_item = {}
    for lot in created_lots:
        item_code = lot['item_code']
        if item_code not in lots_by_item:
            lots_by_item[item_code] = []
        lots_by_item[item_code].append(lot['lot_id'])
    
    # 製造フローに基づく系統関係を作成
    genealogy_relationships = []
    
    # NY6原糸 → NY6染色糸 (原材料投入)
    if 'NY6-RAW-001' in lots_by_item and 'NY6-DYE-BLU-020' in lots_by_item:
        genealogy_relationships.append({
            'parent': lots_by_item['NY6-DYE-BLU-020'][0],
            'child': lots_by_item['NY6-RAW-001'][0],
            'consumed': 50.0,
            'usage': 'Main Material'
        })
    
    # PE原糸 → PE編み糸
    if 'PE-UHMW-001' in lots_by_item and 'PE-X8-150' in lots_by_item:
        genealogy_relationships.append({
            'parent': lots_by_item['PE-X8-150'][0],
            'child': lots_by_item['PE-UHMW-001'][0],
            'consumed': 80.0,
            'usage': 'Main Material'
        })
    
    # 染色糸 → モノフィラメント
    if 'NY6-DYE-BLU-020' in lots_by_item and 'MONO-NY6-15' in lots_by_item:
        genealogy_relationships.append({
            'parent': lots_by_item['MONO-NY6-15'][0],
            'child': lots_by_item['NY6-DYE-BLU-020'][0],
            'consumed': 150.0,
            'usage': 'Main Material'
        })
    
    # PE編み糸 → ブレイデッド
    if 'PE-X8-150' in lots_by_item and 'BRAID-PE-15' in lots_by_item:
        genealogy_relationships.append({
            'parent': lots_by_item['BRAID-PE-15'][0],
            'child': lots_by_item['PE-X8-150'][0],
            'consumed': 200.0,
            'usage': 'Main Material'
        })
    
    for rel in genealogy_relationships:
        try:
            result = bom_manager.add_lot_genealogy(
                parent_lot_id=rel['parent'],
                child_lot_id=rel['child'],
                consumed_quantity=rel['consumed'],
                usage_type=rel['usage'],
                consumption_date=datetime.now().strftime('%Y-%m-%d')
            )
            if result:
                print(f"  ✓ 系統関係: {rel['child']} → {rel['parent']} ({rel['consumed']})")
            else:
                print(f"  ⚠ 系統関係作成失敗: {rel['child']} → {rel['parent']}")
        except Exception as e:
            print(f"  ✗ 系統関係エラー: {e}")

def main():
    """メイン実行関数"""
    print("🎣 釣り糸製造業リアルデータ作成開始")
    print("=" * 50)
    
    try:
        # BOMManagerを初期化
        bom_manager = BOMManager('bom_database_dev.db')
        
        # データ作成実行
        create_realistic_items(bom_manager)
        created_lots = create_realistic_lots(bom_manager)
        create_lot_genealogy_relationships(bom_manager, created_lots)
        
        print("\n" + "=" * 50)
        print("✅ リアルデータ作成完了!")
        print("\n📊 作成されたデータ:")
        
        # 統計表示
        conn = sqlite3.connect('bom_database_dev.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM items")
        item_count = cursor.fetchone()[0]
        print(f"  • アイテムマスター: {item_count}件")
        
        cursor.execute("SELECT COUNT(*) FROM lots")
        lot_count = cursor.fetchone()[0]
        print(f"  • ロット: {lot_count}件")
        
        cursor.execute("SELECT COUNT(*) FROM lot_genealogy")
        genealogy_count = cursor.fetchone()[0]
        print(f"  • ロット系統関係: {genealogy_count}件")
        
        cursor.execute("SELECT COUNT(*) FROM inventory_transactions")
        transaction_count = cursor.fetchone()[0]
        print(f"  • 在庫取引: {transaction_count}件")
        
        conn.close()
        
        print(f"\n🌐 アプリケーション: http://localhost:5002/lots")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 