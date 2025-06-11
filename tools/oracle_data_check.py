#!/usr/bin/env python3
"""
Oracle Database データ状況確認スクリプト
実際のデータの存在状況を基本レベルで確認
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

def check_data_status():
    """データ状況を確認"""
    
    # Oracle Instant Clientライブラリパスを明示的に指定
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
    except Exception as e:
        if "has already been initialized" not in str(e):
            print(f"⚠️  Oracle Client初期化警告: {e}")
    
    dsn = f"{HOST}:{PORT}/{SERVICE_NAME}"
    
    print("=" * 80)
    print("Oracle Database データ状況確認")
    print("=" * 80)
    print(f"確認開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        connection = cx_Oracle.connect(USERNAME, PASSWORD, dsn)
        cursor = connection.cursor()
        
        # 1. 製造日報投入テーブルの基本情報
        print("\n📊 T_製紐_日報_明細_投入 基本データ確認")
        print("=" * 60)
        
        # 全行数
        cursor.execute("SELECT COUNT(*) FROM T_製紐_日報_明細_投入")
        total_count = cursor.fetchone()[0]
        print(f"総行数: {total_count:,}")
        
        # 品目コードがNULLでない行数
        cursor.execute("SELECT COUNT(*) FROM T_製紐_日報_明細_投入 WHERE 品目コード IS NOT NULL")
        non_null_count = cursor.fetchone()[0]
        print(f"品目コードがNULLでない行数: {non_null_count:,}")
        
        # 品目コードが空文字でない行数
        cursor.execute("SELECT COUNT(*) FROM T_製紐_日報_明細_投入 WHERE 品目コード IS NOT NULL AND TRIM(品目コード) != ''")
        non_empty_count = cursor.fetchone()[0]
        print(f"品目コードが空でない行数: {non_empty_count:,}")
        
        # 実際のサンプルデータ（条件なし）
        print("\n📋 実際のサンプルデータ（条件なし）")
        print("-" * 60)
        
        cursor.execute("""
            SELECT * FROM (
                SELECT 見出しID, 品目コード, 投入数量, 作業日時
                FROM T_製紐_日報_明細_投入
                ORDER BY ROWNUM
            ) WHERE ROWNUM <= 5
        """)
        
        sample_data = cursor.fetchall()
        for i, row in enumerate(sample_data):
            print(f"  {i+1}. 見出し:{row[0]} 品目:{row[1]} 投入量:{row[2]} 日時:{row[3]}")
        
        # 2. 製品マスタの基本確認
        print("\n🏭 PCS_PRODUCT_MST 基本データ確認")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM PCS_PRODUCT_MST")
        product_count = cursor.fetchone()[0]
        print(f"製品マスタ総行数: {product_count:,}")
        
        cursor.execute("SELECT COUNT(*) FROM PCS_PRODUCT_MST WHERE PRODUCT_CODE IS NOT NULL")
        product_code_count = cursor.fetchone()[0]
        print(f"製品コードがあるもの: {product_code_count:,}")
        
        # サンプル製品コード
        cursor.execute("""
            SELECT PRODUCT_CODE, PRODUCT_NAME FROM (
                SELECT PRODUCT_CODE, PRODUCT_NAME
                FROM PCS_PRODUCT_MST
                WHERE PRODUCT_CODE IS NOT NULL
                ORDER BY ROWNUM
            ) WHERE ROWNUM <= 5
        """)
        
        product_samples = cursor.fetchall()
        print("\n製品コードサンプル:")
        for i, row in enumerate(product_samples):
            print(f"  {i+1}. コード:{row[0]} 名前:{row[1]}")
        
        # 3. 投入テーブルと製品マスタの照合確認
        print("\n🔗 データ照合確認")
        print("=" * 60)
        
        # 共通する品目コードがあるか確認
        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT 品目コード
                FROM T_製紐_日報_明細_投入
                WHERE 品目コード IS NOT NULL
            ) i
            JOIN (
                SELECT DISTINCT PRODUCT_CODE
                FROM PCS_PRODUCT_MST
                WHERE PRODUCT_CODE IS NOT NULL
            ) p ON i.品目コード = p.PRODUCT_CODE
        """)
        
        match_count = cursor.fetchone()[0]
        print(f"投入データと製品マスタで一致する品目コード数: {match_count}")
        
        # 4. カラム名の実際の確認
        print("\n📋 T_製紐_日報_明細_投入 カラム確認")
        print("=" * 60)
        
        cursor.execute("""
            SELECT column_name, data_type, nullable
            FROM user_tab_columns
            WHERE table_name = 'T_製紐_日報_明細_投入'
            ORDER BY column_id
        """)
        
        columns = cursor.fetchall()
        print("カラム一覧:")
        for col in columns:
            print(f"  📄 {col[0]:<20} {col[1]:<15} NULL:{col[2]}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 80)
        print("✅ データ状況確認完了")
        print("=" * 80)
        
        return True
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle接続エラー: {error}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = check_data_status()
    sys.exit(0 if success else 1) 