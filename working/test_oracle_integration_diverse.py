#!/usr/bin/env python3
"""
Oracle連携テストスクリプト（多様な製品タイプ版）
現在のBOM管理システムにより多様なOracle製品データを統合するテスト
"""

import cx_Oracle
import sqlite3
import sys
from datetime import datetime

def test_diverse_oracle_integration():
    """多様な製品タイプのOracle連携テスト"""
    
    print("=" * 80)
    print("Oracle連携統合テスト（多様な製品タイプ版）")
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
        
        cursor = oracle_conn.cursor()
        
        # 1. ABSORBER系製品（完成品）を取得
        print("\n📦 ABSORBER系製品（完成品）を取得中...")
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
                AND UPPER(PRODUCT_NAME) LIKE '%ABSORBER%'
                ORDER BY PRODUCT_CODE
            ) WHERE ROWNUM <= 5
        """)
        
        absorber_products = cursor.fetchall()
        print(f"  取得件数: {len(absorber_products)}件")
        
        # 2. 様々なシリーズの製品を取得
        print("\n🎣 多様なシリーズ製品を取得中...")
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
                AND SERIES_NAME IS NOT NULL
                AND UPPER(SERIES_NAME) NOT LIKE '%X-BRAID FULLDRAG%'
                ORDER BY SERIES_NAME, PRODUCT_CODE
            ) WHERE ROWNUM <= 10
        """)
        
        diverse_products = cursor.fetchall()
        print(f"  取得件数: {len(diverse_products)}件")
        
        # 3. 原材料系製品を一部追加
        print("\n🧶 原材料マスタを取得中...")
        cursor.execute("""
            SELECT 品目コード, 品目名, 原糸種類, PS, PS糸
            FROM M_品目_PS糸_仮
            WHERE ROWNUM <= 5
        """)
        
        materials = cursor.fetchall()
        print(f"  取得件数: {len(materials)}件")
        
        oracle_conn.close()
        
        # SQLite接続・データ同期
        sqlite_conn = sqlite3.connect("bom_database_enhanced.db")
        cursor = sqlite_conn.cursor()
        
        sync_count = 0
        
        # ABSORBER系製品を完成品として追加
        for product in absorber_products:
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
                    '完成品',  # ABSORBER系は完成品
                    'M',
                    yarn_composition,
                    series_name,
                    length_num,
                    color,
                    knit_type
                ))
                sync_count += 1
                print(f"  ✅ 完成品追加: {item_name}")
            except Exception as e:
                print(f"  ⚠️  同期エラー {oracle_code}: {e}")
        
        # 多様なシリーズ製品を追加
        for product in diverse_products:
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
            
            # アイテムタイプの推定（より詳細に）
            name_upper = item_name.upper()
            series_upper = (series_name or '').upper()
            
            if 'ABSORBER' in name_upper or 'LEADER' in name_upper:
                item_type = '完成品'
            elif 'BRAID' in name_upper or 'BRAID' in series_upper:
                item_type = '製紐糸'
            elif 'DYNEEMA' in name_upper or 'PE' in yarn_composition:
                item_type = '原糸'
            else:
                item_type = '完成品'  # デフォルト
            
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
                print(f"  ✅ {item_type}追加: {item_name}")
            except Exception as e:
                print(f"  ⚠️  同期エラー {oracle_code}: {e}")
        
        # 原材料を追加
        for material in materials:
            oracle_code = material[0]
            material_name = material[1] or f"PS糸_{oracle_code}"
            yarn_type = material[2]
            ps_value = material[3]
            ps_yarn_value = material[4]
            
            item_id = f"MATERIAL_{oracle_code}"
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO items (
                        item_id,
                        oracle_product_code,
                        item_name,
                        item_type,
                        unit_of_measure,
                        yarn_composition,
                        ps_ratio,
                        oracle_sync_status,
                        oracle_last_sync
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'synced', CURRENT_TIMESTAMP)
                """, (
                    item_id,
                    oracle_code,
                    material_name,
                    'PS糸',
                    'KG',
                    yarn_type,
                    ps_value
                ))
                sync_count += 1
                print(f"  ✅ PS糸追加: {material_name}")
            except Exception as e:
                print(f"  ⚠️  原材料同期エラー {oracle_code}: {e}")
        
        sqlite_conn.commit()
        
        # 同期結果確認
        cursor.execute("""
            SELECT item_type, COUNT(*) as count
            FROM items 
            GROUP BY item_type
            ORDER BY count DESC
        """)
        
        type_counts = cursor.fetchall()
        
        print(f"\n📊 同期後のアイテムタイプ分布:")
        total_items = 0
        for type_count in type_counts:
            print(f"  📈 {type_count[0]}: {type_count[1]}件")
            total_items += type_count[1]
        
        print(f"\n✅ 総同期件数: {sync_count}件")
        print(f"✅ 総アイテム数: {total_items}件")
        
        sqlite_conn.close()
        
        print("\n" + "=" * 80)
        print("✅ 多様な製品タイプの Oracle連携統合テスト完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_diverse_oracle_integration()
    sys.exit(0 if success else 1) 