#!/usr/bin/env python3
"""
Oracle Database スキーマ分析スクリプト
BOM管理に関連するテーブル構造を詳細調査
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

def analyze_table_structure(cursor, table_name):
    """テーブル構造を詳細分析"""
    print(f"\n📋 テーブル: {table_name}")
    print("-" * 80)
    
    # カラム情報を取得
    cursor.execute("""
        SELECT 
            utc.column_name,
            utc.data_type,
            utc.data_length,
            utc.data_precision,
            utc.data_scale,
            utc.nullable,
            utc.data_default,
            ucc.comments
        FROM user_tab_columns utc
        LEFT JOIN user_col_comments ucc ON utc.table_name = ucc.table_name 
            AND utc.column_name = ucc.column_name
        WHERE utc.table_name = :table_name
        ORDER BY utc.column_id
    """, {"table_name": table_name})
    
    columns = cursor.fetchall()
    
    if columns:
        print(f"{'カラム名':<30} {'データ型':<15} {'NULL許可':<8} {'デフォルト':<15} {'コメント'}")
        print("-" * 120)
        
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            if col[1] in ['NUMBER'] and col[2]:
                if col[3] and col[4]:
                    data_type = f"{col[1]}({col[3]},{col[4]})"
                elif col[3]:
                    data_type = f"{col[1]}({col[3]})"
            elif col[1] in ['VARCHAR2', 'CHAR'] and col[2]:
                data_type = f"{col[1]}({col[2]})"
            
            nullable = "○" if col[5] == 'Y' else "×"
            default_val = str(col[6])[:15] if col[6] else ""
            comment = col[7] if col[7] else ""
            
            print(f"{col_name:<30} {data_type:<15} {nullable:<8} {default_val:<15} {comment}")
    
    # インデックス情報を取得
    cursor.execute("""
        SELECT 
            index_name,
            column_name,
            column_position,
            uniqueness
        FROM user_indexes ui
        JOIN user_ind_columns uic ON ui.index_name = uic.index_name
        WHERE ui.table_name = :table_name
        ORDER BY ui.index_name, uic.column_position
    """, {"table_name": table_name})
    
    indexes = cursor.fetchall()
    if indexes:
        print(f"\n🔍 インデックス:")
        current_index = None
        for idx in indexes:
            if current_index != idx[0]:
                uniqueness = "UNIQUE" if idx[3] == "UNIQUE" else "NON-UNIQUE"
                print(f"  📌 {idx[0]} ({uniqueness})")
                current_index = idx[0]
            print(f"     - {idx[1]} (位置: {idx[2]})")
    
    # 外部キー制約を取得
    cursor.execute("""
        SELECT 
            constraint_name,
            column_name,
            r_constraint_name,
            delete_rule
        FROM user_cons_columns ucc1
        JOIN user_constraints uc ON ucc1.constraint_name = uc.constraint_name
        WHERE uc.table_name = :table_name
        AND uc.constraint_type = 'R'
        ORDER BY ucc1.position
    """, {"table_name": table_name})
    
    foreign_keys = cursor.fetchall()
    if foreign_keys:
        print(f"\n🔗 外部キー制約:")
        for fk in foreign_keys:
            print(f"  🔑 {fk[0]}: {fk[1]} → {fk[2]} (削除: {fk[3]})")

def analyze_oracle_schema():
    """Oracle スキーマを分析"""
    
    # Oracle Instant Clientライブラリパスを明示的に指定
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
    except Exception as e:
        if "has already been initialized" not in str(e):
            print(f"⚠️  Oracle Client初期化警告: {e}")
    
    dsn = f"{HOST}:{PORT}/{SERVICE_NAME}"
    
    print("=" * 80)
    print("Oracle Database スキーマ分析")
    print("=" * 80)
    print(f"分析開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        connection = cx_Oracle.connect(USERNAME, PASSWORD, dsn)
        cursor = connection.cursor()
        
        # BOM管理に関連しそうなテーブルを特定
        print("🔍 BOM管理に関連する可能性のあるテーブルを検索中...")
        
        # 製品マスタ系
        product_tables = ['PCS_PRODUCT_MST', 'PCS_EPRODUCT_MST']
        
        # 原材料・糸関連
        material_tables = ['M_品目_原糸_仮', 'M_品目_PS糸_仮', 'M_品目_木管糸_仮', 'RY_RAWYARN_MST']
        
        # 製造・工程関連
        manufacturing_tables = ['BD_BRAIDER_MST', 'PS_MST', 'WD_MST']
        
        # オーダー・受注関連
        order_tables = ['DT_ORDER', 'DT_ORDER_DETAIL', 'PCS_ORDER_INFO_MST']
        
        # 主要なテーブルを分析
        important_tables = product_tables + material_tables + manufacturing_tables + order_tables
        
        for table_name in important_tables:
            # テーブルが存在するかチェック
            cursor.execute("""
                SELECT COUNT(*) FROM user_tables WHERE table_name = :table_name
            """, {"table_name": table_name})
            
            if cursor.fetchone()[0] > 0:
                analyze_table_structure(cursor, table_name)
            else:
                print(f"\n⚠️  テーブル {table_name} は存在しません")
        
        # BOM構造を示唆するテーブルを検索
        print("\n" + "=" * 80)
        print("🔍 BOM構造関連テーブル検索")
        print("=" * 80)
        
        cursor.execute("""
            SELECT table_name, num_rows
            FROM user_tables 
            WHERE table_name LIKE '%BOM%' 
               OR table_name LIKE '%構成%'
               OR table_name LIKE '%部品%'
               OR table_name LIKE '%COMPONENT%'
               OR table_name LIKE '%RECIPE%'
            ORDER BY table_name
        """)
        
        bom_related_tables = cursor.fetchall()
        if bom_related_tables:
            print("🎯 BOM関連テーブル候補:")
            for table in bom_related_tables:
                print(f"  📄 {table[0]:<40} 行数: {table[1] or 'N/A'}")
                analyze_table_structure(cursor, table[0])
        else:
            print("⚠️  明示的なBOM関連テーブルは見つかりませんでした")
        
        # 親子関係を示唆するテーブルを検索
        print("\n" + "=" * 80)
        print("🔍 親子関係テーブル検索")
        print("=" * 80)
        
        cursor.execute("""
            SELECT DISTINCT table_name
            FROM user_tab_columns
            WHERE column_name LIKE '%PARENT%'
               OR column_name LIKE '%CHILD%'
               OR column_name LIKE '%親%'
               OR column_name LIKE '%子%'
            ORDER BY table_name
        """)
        
        parent_child_tables = cursor.fetchall()
        if parent_child_tables:
            print("🌳 親子関係を示唆するテーブル:")
            for table in parent_child_tables:
                print(f"  📄 {table[0]}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 80)
        print("✅ スキーマ分析完了")
        print("=" * 80)
        
        return True
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle接続エラー: {error}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = analyze_oracle_schema()
    sys.exit(0 if success else 1) 