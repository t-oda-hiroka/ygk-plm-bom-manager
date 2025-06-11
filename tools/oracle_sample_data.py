#!/usr/bin/env python3
"""
Oracle Database サンプルデータ取得スクリプト
統合ポイント特定のための実際のデータ確認
"""

import cx_Oracle
import sys
from datetime import datetime

# 接続パラメータ
HOST = "hrk-ora-db.cvqkhcprwraj.ap-northeast-1.rds.amazonaws.com"
PORT = 1521
SERVICE_NAME = "orcl"
USERNAME = "ygk_pcs"
PASSWORD = "ygkpcs"

def get_sample_data():
    """統合に必要なサンプルデータを取得"""
    
    # Oracle Instant Clientライブラリパスを明示的に指定
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
    except Exception as e:
        if "has already been initialized" not in str(e):
            print(f"⚠️  Oracle Client初期化警告: {e}")
    
    dsn = f"{HOST}:{PORT}/{SERVICE_NAME}"
    
    print("=" * 80)
    print("Oracle Database サンプルデータ取得（統合ポイント特定）")
    print("=" * 80)
    print(f"取得開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        connection = cx_Oracle.connect(USERNAME, PASSWORD, dsn)
        cursor = connection.cursor()
        
        # 1. 製品マスタのサンプル（BOMアプリのitemsテーブル拡張の参考）
        print("\n🏭 PCS_PRODUCT_MST サンプルデータ")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 
                PRODUCT_CODE,
                PRODUCT_NAME,
                YARN_COMPOSITION,
                SERIES_NAME,
                LENGTH_M,
                COLOR,
                YARN_TYPE,
                RAW_NUM,
                PRODUCTION_NUM,
                KNIT,
                CORE_YARN_TYPE,
                SPOOL_TYPE
            FROM (
                SELECT * FROM PCS_PRODUCT_MST 
                WHERE PRODUCT_CODE IS NOT NULL
                AND PRODUCT_NAME IS NOT NULL
                ORDER BY ROWNUM
            ) WHERE ROWNUM <= 5
        """)
        
        product_samples = cursor.fetchall()
        
        print("製品マスタサンプル:")
        for i, row in enumerate(product_samples):
            print(f"\n  📦 製品 {i+1}:")
            print(f"    コード: {row[0]}")
            print(f"    名前: {row[1]}")
            print(f"    糸構成: {row[2] or 'N/A'}")
            print(f"    シリーズ: {row[3] or 'N/A'}")
            print(f"    長さ: {row[4] or 'N/A'}M")
            print(f"    色: {row[5] or 'N/A'}")
            print(f"    糸種: {row[6] or 'N/A'}")
            print(f"    生糸号数: {row[7] or 'N/A'}")
            print(f"    編み方: {row[9] or 'N/A'}")
            print(f"    芯糸種類: {row[10] or 'N/A'}")
        
        # 2. 原材料マスタのサンプル
        print(f"\n🧶 原材料マスタサンプル")
        print("=" * 60)
        
        # 原糸マスタ
        cursor.execute("""
            SELECT 品目コード, 原糸種類, 原糸
            FROM M_品目_原糸_仮
            WHERE ROWNUM <= 3
        """)
        
        raw_yarn_samples = cursor.fetchall()
        print("原糸マスタ:")
        for row in raw_yarn_samples:
            print(f"  🧵 {row[0]}: {row[1]} ({row[2]})")
        
        # PS糸マスタ
        cursor.execute("""
            SELECT 品目コード, 品目名, 原糸種類, PS, PS糸
            FROM M_品目_PS糸_仮
            WHERE ROWNUM <= 3
        """)
        
        ps_yarn_samples = cursor.fetchall()
        print("PS糸マスタ:")
        for row in ps_yarn_samples:
            print(f"  🎯 {row[0]}: {row[1]} - {row[2]} (PS:{row[3]}, PS糸:{row[4]})")
        
        # 3. デニール・材質の分布確認
        print(f"\n📊 製品属性の分布")
        print("=" * 60)
        
        # 糸種の分布
        cursor.execute("""
            SELECT YARN_TYPE, COUNT(*) as 件数
            FROM PCS_PRODUCT_MST
            WHERE YARN_TYPE IS NOT NULL
            GROUP BY YARN_TYPE
            ORDER BY 件数 DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        yarn_type_dist = cursor.fetchall()
        print("糸種分布:")
        for row in yarn_type_dist:
            print(f"  📈 {row[0]}: {row[1]}件")
        
        # 編み方の分布
        cursor.execute("""
            SELECT KNIT, COUNT(*) as 件数
            FROM PCS_PRODUCT_MST
            WHERE KNIT IS NOT NULL
            GROUP BY KNIT
            ORDER BY 件数 DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        knit_dist = cursor.fetchall()
        print("編み方分布:")
        for row in knit_dist:
            print(f"  🪢 {row[0]}: {row[1]}件")
        
        # 4. 統合候補のユニークキー確認
        print(f"\n🔑 統合キー候補")
        print("=" * 60)
        
        # PRODUCT_CODEの重複確認
        cursor.execute("""
            SELECT COUNT(*) as 総数, COUNT(DISTINCT PRODUCT_CODE) as ユニーク数
            FROM PCS_PRODUCT_MST
            WHERE PRODUCT_CODE IS NOT NULL
        """)
        
        key_check = cursor.fetchone()
        print(f"PRODUCT_CODE: 総数{key_check[0]}, ユニーク{key_check[1]} - {'✅重複なし' if key_check[0] == key_check[1] else '❌重複あり'}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 80)
        print("✅ サンプルデータ取得完了")
        print("=" * 80)
        
        # 統合提案
        print("\n💡 統合ポイント提案:")
        print("1. 製品マスタ統合: PRODUCT_CODE をキーとして活用可能")
        print("2. 属性拡張: 糸構成、編み方、デニール等の詳細属性を追加")
        print("3. 原材料統合: 原糸・PS糸マスタから材料情報を取得")
        print("4. 分類強化: 実際の糸種・編み方分布を活用した分類")
        
        return True
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle接続エラー: {error}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = get_sample_data()
    sys.exit(0 if success else 1) 