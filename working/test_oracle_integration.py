#!/usr/bin/env python3
"""
Oracle連携テストスクリプト
現在のBOM管理システムにOracle製品データを統合するテスト
"""

import cx_Oracle
import sqlite3
import sys
from datetime import datetime

def test_oracle_integration():
    """Oracle連携の基本テスト"""
    
    print("=" * 80)
    print("Oracle連携統合テスト")
    print("=" * 80)
    print(f"テスト開始時刻: {datetime.now()}")
    print("-" * 80)
    
    # Oracle接続テスト
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
        oracle_conn = cx_Oracle.connect(
            "ygk_pcs", 
            "ygkpcs", 
            "hrk-ora-db.cvqkhcprwraj.ap-northeast-1.rds.amazonaws.com:1521/orcl"
        )
        print("✅ Oracle接続成功")
        
        # サンプル製品データを取得
        cursor = oracle_conn.cursor()
        cursor.execute("""
            SELECT * FROM (
                SELECT 
                    PRODUCT_CODE,
                    PRODUCT_NAME,
                    YARN_COMPOSITION,
                    SERIES_NAME,
                    LENGTH_M,
                    COLOR,
                    KNIT
                FROM PCS_PRODUCT_MST
                WHERE PRODUCT_CODE IS NOT NULL
                AND PRODUCT_NAME IS NOT NULL
                AND SERIES_NAME LIKE '%X-BRAID%'
                ORDER BY PRODUCT_CODE
            ) WHERE ROWNUM <= 10
        """)
        
        oracle_products = cursor.fetchall()
        oracle_conn.close()
        
        print(f"✅ Oracle製品データ取得: {len(oracle_products)}件")
        
        # SQLite接続・拡張スキーマ適用テスト
        sqlite_conn = sqlite3.connect("bom_database_enhanced.db")
        
        # 拡張スキーマを適用
        with open("schema_enhanced.sql", "r", encoding="utf-8") as f:
            schema = f.read()
            sqlite_conn.executescript(schema)
        
        print("✅ 拡張スキーマ適用完了")
        
        # Oracle製品データをSQLiteに同期
        cursor = sqlite_conn.cursor()
        sync_count = 0
        
        for product in oracle_products:
            oracle_code = product[0]
            item_name = product[1]
            yarn_composition = product[2]
            series_name = product[3]
            length_m = product[4]
            color = product[5]
            knit_type = product[6]
            
            # 長さの数値変換
            try:
                length_num = int(''.join(c for c in str(length_m or '') if c.isdigit()) or 0)
            except:
                length_num = None
            
            # アイテムタイプの推定
            if 'ABSORBER' in item_name.upper():
                item_type = '完成品'
            elif 'BRAID' in item_name.upper():
                item_type = '製紐糸'
            else:
                item_type = '完成品'
            
            # SQLiteに挿入
            item_id = f"ORACLE_{oracle_code}"
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO items (
                        item_id,
                        oracle_product_code,
                        item_name,
                        item_type,
                        unit_of_measure,
                        yarn_composition,
                        series_name,
                        length_m,
                        color,
                        knit_type,
                        oracle_sync_status,
                        oracle_last_sync
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'synced', CURRENT_TIMESTAMP)
                """, (
                    item_id,
                    oracle_code,
                    item_name,
                    item_type,
                    'M',
                    yarn_composition,
                    series_name,
                    length_num,
                    color,
                    knit_type
                ))
                sync_count += 1
            except Exception as e:
                print(f"⚠️  同期エラー {oracle_code}: {e}")
        
        sqlite_conn.commit()
        print(f"✅ SQLite同期完了: {sync_count}件")
        
        # 同期結果確認
        cursor.execute("""
            SELECT 
                item_id,
                item_name,
                yarn_composition,
                series_name,
                knit_type,
                oracle_sync_status
            FROM items 
            WHERE oracle_product_code IS NOT NULL
            ORDER BY item_id
        """)
        
        synced_items = cursor.fetchall()
        
        print(f"\n📋 同期された製品一覧 ({len(synced_items)}件):")
        for item in synced_items:
            print(f"  📦 {item[0]}: {item[1]}")
            print(f"      糸構成: {item[2] or 'N/A'}, シリーズ: {item[3] or 'N/A'}")
            print(f"      編み方: {item[4] or 'N/A'}, 同期: {item[5]}")
            print()
        
        # 現在のBOM管理システムとの連携テスト
        from bom_manager import BOMManager
        
        bom_manager = BOMManager("bom_database_enhanced.db")
        
        # 拡張アイテム取得テスト
        print("🔍 拡張アイテム取得テスト:")
        all_items = bom_manager.get_all_items_by_type('完成品')
        oracle_items = [item for item in all_items if item['item_id'].startswith('ORACLE_')]
        
        print(f"  完成品総数: {len(all_items)}件")
        print(f"  Oracle連携製品: {len(oracle_items)}件")
        
        if oracle_items:
            sample_item = oracle_items[0]
            print(f"  サンプル製品: {sample_item['item_name']}")
            print(f"  糸構成: {sample_item.get('yarn_composition', 'N/A')}")
            print(f"  編み方: {sample_item.get('knit_type', 'N/A')}")
        
        sqlite_conn.close()
        
        print("\n" + "=" * 80)
        print("✅ Oracle連携統合テスト完了")
        print("=" * 80)
        
        print("\n💡 次のステップ:")
        print("1. BOMアプリのUI更新（Oracle製品表示対応）")
        print("2. 製品検索機能の強化")
        print("3. Oracle同期機能の自動化")
        print("4. 現実的なBOM構成例の追加")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_oracle_integration()
    sys.exit(0 if success else 1) 