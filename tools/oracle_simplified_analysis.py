#!/usr/bin/env python3
"""
Oracle Database シンプルスキーマ分析スクリプト
BOM関連テーブルの基本構造を調査
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

def simple_table_analysis(cursor, table_name):
    """テーブルの基本構造を分析"""
    print(f"\n📋 テーブル: {table_name}")
    print("-" * 80)
    
    # 行数を取得
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"  📊 行数: {row_count:,} 行")
    except:
        print(f"  📊 行数: 取得失敗")
    
    # カラム情報を取得
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            nullable,
            data_default
        FROM user_tab_columns
        WHERE table_name = :table_name
        ORDER BY column_id
    """, {"table_name": table_name})
    
    columns = cursor.fetchall()
    
    if columns:
        print(f"  📋 カラム数: {len(columns)}")
        print(f"  {'カラム名':<30} {'データ型':<15} {'NULL許可'}")
        print("  " + "-" * 60)
        
        for col in columns[:20]:  # 最初の20カラムのみ表示
            col_name = col[0]
            data_type = col[1]
            nullable = "○" if col[2] == 'Y' else "×"
            
            print(f"  {col_name:<30} {data_type:<15} {nullable}")
        
        if len(columns) > 20:
            print(f"  ... 他 {len(columns) - 20} カラム")

def analyze_bom_potential():
    """BOM管理の可能性があるテーブルを分析"""
    
    # Oracle Instant Clientライブラリパスを明示的に指定
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
    except Exception as e:
        if "has already been initialized" not in str(e):
            print(f"⚠️  Oracle Client初期化警告: {e}")
    
    dsn = f"{HOST}:{PORT}/{SERVICE_NAME}"
    
    print("=" * 80)
    print("Oracle Database BOM関連テーブル分析")
    print("=" * 80)
    print(f"分析開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        connection = cx_Oracle.connect(USERNAME, PASSWORD, dsn)
        cursor = connection.cursor()
        
        # 1. 製品マスタ系テーブル
        print("\n🏭 製品マスタ系テーブル")
        print("=" * 50)
        product_tables = ['PCS_PRODUCT_MST', 'PCS_EPRODUCT_MST']
        
        for table in product_tables:
            cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :name", {"name": table})
            if cursor.fetchone()[0] > 0:
                simple_table_analysis(cursor, table)
        
        # 2. 原材料・糸関連テーブル
        print("\n🧶 原材料・糸関連テーブル")
        print("=" * 50)
        material_tables = ['M_品目_原糸_仮', 'M_品目_PS糸_仮', 'M_品目_木管糸_仮', 'RY_RAWYARN_MST']
        
        for table in material_tables:
            cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :name", {"name": table})
            if cursor.fetchone()[0] > 0:
                simple_table_analysis(cursor, table)
        
        # 3. 受注・オーダー関連テーブル
        print("\n📋 受注・オーダー関連テーブル")
        print("=" * 50)
        order_tables = ['DT_ORDER', 'DT_ORDER_DETAIL', 'PCS_ORDER_INFO_MST']
        
        for table in order_tables:
            cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :name", {"name": table})
            if cursor.fetchone()[0] > 0:
                simple_table_analysis(cursor, table)
        
        # 4. BOM候補テーブル検索
        print("\n🔍 BOM構造候補テーブル検索")
        print("=" * 50)
        
        cursor.execute("""
            SELECT table_name, num_rows
            FROM user_tables 
            WHERE table_name LIKE '%構成%'
               OR table_name LIKE '%部品%'
               OR table_name LIKE '%COMPONENT%'
               OR table_name LIKE '%RECIPE%'
               OR table_name LIKE '%BOM%'
               OR table_name LIKE '%明細%'
               OR table_name LIKE '%DETAIL%'
            ORDER BY table_name
        """)
        
        bom_candidates = cursor.fetchall()
        if bom_candidates:
            print("🎯 BOM関連候補テーブル:")
            for table in bom_candidates:
                print(f"  📄 {table[0]:<40} 行数: {table[1] or 'N/A'}")
        
        # 5. 工程・製造関連テーブル
        print("\n⚙️ 工程・製造関連テーブル")
        print("=" * 50)
        manufacturing_tables = ['BD_BRAIDER_MST', 'PS_MST', 'WD_MST']
        
        for table in manufacturing_tables:
            cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :name", {"name": table})
            if cursor.fetchone()[0] > 0:
                simple_table_analysis(cursor, table)
        
        # 6. 主要製造日報テーブル（BOM展開のヒント）
        print("\n📊 製造日報系テーブル（BOM展開のヒント）")
        print("=" * 50)
        
        daily_report_tables = [
            'T_製紐_日報_明細_設定',
            'T_製紐_日報_明細_投入',
            'T_製紐_日報_明細_作業'
        ]
        
        for table in daily_report_tables:
            cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :name", {"name": table})
            if cursor.fetchone()[0] > 0:
                simple_table_analysis(cursor, table)
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 80)
        print("✅ 簡易スキーマ分析完了")
        print("=" * 80)
        
        return True
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle接続エラー: {error}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = analyze_bom_potential()
    sys.exit(0 if success else 1) 