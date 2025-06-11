#!/usr/bin/env python3
"""
ロット管理機能テストスクリプト
"""

from bom_manager import BOMManager
import datetime

def test_lot_management():
    """ロット管理機能のテスト"""
    print("🧪 ロット管理機能テスト開始")
    print("=" * 50)
    
    # BOMManagerを初期化
    bom = BOMManager('bom_database_dev.db')
    
    try:
        # テスト用のロットを作成
        print("📦 ロット作成中...")
        lot_id = bom.create_lot(
            item_id='TEST_RAW_001',
            process_code='P',  # PS工程
            planned_quantity=100.0,
            production_date='2025-01-11',
            quality_grade='A',
            location='工場A-棚1',
            operator_id='OP001'
        )
        print(f'✅ ロット作成成功: {lot_id}')
        
        # 作成されたロットの情報を取得
        print("\n📋 ロット情報の取得中...")
        lot_info = bom.get_lot(lot_id)
        if lot_info:
            print(f'✅ ロット情報取得成功:')
            print(f'   - ID: {lot_info["lot_id"]}')
            print(f'   - アイテム: {lot_info["item_name"]}')
            print(f'   - 工程: {lot_info["process_name"]}')
            print(f'   - 数量: {lot_info["current_quantity"]} {lot_info["unit_of_measure"]}')
            print(f'   - 品質: {lot_info["grade_name"]}')
            print(f'   - 状態: {lot_info["lot_status"]}')
            print(f'   - 場所: {lot_info["location"]}')
            print(f'   - 作業者: {lot_info["operator_id"]}')
        
        # 全ロット一覧を取得
        print("\n📊 全ロット一覧の取得中...")
        all_lots = bom.get_all_lots()
        print(f'✅ 総ロット数: {len(all_lots)}')
        
        for lot in all_lots:
            print(f'   - {lot["lot_id"]}: {lot["item_name"]} ({lot["lot_status"]})')
        
        # ロットID生成のテスト
        print("\n🔢 ロットID生成テスト...")
        test_lot_id = bom.generate_lot_id('W', '2025-01-11')  # Winder工程
        print(f'✅ 生成されたロットID: {test_lot_id}')
        
        print("\n" + "=" * 50)
        print("🎉 ロット管理機能テスト完了！")
        
        return True
        
    except Exception as e:
        print(f'❌ エラー: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_lot_management()
    exit(0 if success else 1) 