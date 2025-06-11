#!/usr/bin/env python3
"""
Oracle Database接続テストスクリプト
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

def test_oracle_connection():
    """Oracle接続テストを実行"""
    
    # Oracle Instant Clientライブラリパスを明示的に指定
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
        print("🔧 Oracle Instant Clientライブラリを初期化しました")
    except Exception as e:
        # 既に初期化されている場合はエラーを無視
        if "has already been initialized" not in str(e):
            print(f"⚠️  Oracle Client初期化警告: {e}")
    
    # DSN（Data Source Name）を構築
    dsn = f"{HOST}:{PORT}/{SERVICE_NAME}"
    
    print("=" * 60)
    print("Oracle Database 接続テスト")
    print("=" * 60)
    print(f"接続先: {dsn}")
    print(f"ユーザー: {USERNAME}")
    print(f"テスト開始時刻: {datetime.now()}")
    print("-" * 60)
    
    try:
        # 接続試行
        print("接続を試行中...")
        connection = cx_Oracle.connect(USERNAME, PASSWORD, dsn)
        print("✅ Oracle接続成功！")
        
        cursor = connection.cursor()
        
        # 1. データベースバージョン情報を取得
        print("\n📊 データベース情報:")
        cursor.execute("SELECT * FROM v$version WHERE rownum = 1")
        version = cursor.fetchone()
        print(f"  Oracle Version: {version[0]}")
        
        # 2. 現在の接続情報を取得
        cursor.execute("SELECT user, instance_name FROM v$instance, dual")
        instance_info = cursor.fetchone()
        print(f"  接続ユーザー: {instance_info[0]}")
        print(f"  インスタンス名: {instance_info[1]}")
        
        # 3. 現在の日時を取得
        cursor.execute("SELECT SYSDATE FROM dual")
        current_time = cursor.fetchone()
        print(f"  サーバー時刻: {current_time[0]}")
        
        # 4. ユーザーのテーブル一覧を取得
        print("\n📋 ユーザーのテーブル一覧:")
        cursor.execute("""
            SELECT table_name, num_rows, last_analyzed
            FROM user_tables 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        if tables:
            for table in tables:
                analyzed = table[2].strftime('%Y-%m-%d %H:%M:%S') if table[2] else 'N/A'
                print(f"  📄 {table[0]:<30} 行数: {table[1] or 'N/A':<10} 最終分析: {analyzed}")
        else:
            print("  ⚠️  テーブルが見つかりませんでした")
        
        # 5. ユーザーのビュー一覧を取得
        print("\n👁️  ユーザーのビュー一覧:")
        cursor.execute("""
            SELECT view_name 
            FROM user_views 
            ORDER BY view_name
        """)
        
        views = cursor.fetchall()
        if views:
            for view in views:
                print(f"  👁️  {view[0]}")
        else:
            print("  ⚠️  ビューが見つかりませんでした")
        
        # 6. 権限情報を取得
        print("\n🔐 ユーザー権限情報:")
        cursor.execute("""
            SELECT privilege, admin_option 
            FROM user_sys_privs 
            ORDER BY privilege
        """)
        
        privileges = cursor.fetchall()
        if privileges:
            for priv in privileges:
                admin_flag = "（管理者権限）" if priv[1] == 'YES' else ""
                print(f"  🔑 {priv[0]} {admin_flag}")
        else:
            print("  ⚠️  システム権限が見つかりませんでした")
        
        # 7. 表領域情報を取得
        print("\n💾 表領域情報:")
        cursor.execute("""
            SELECT tablespace_name, bytes/1024/1024 as size_mb, max_bytes/1024/1024 as max_size_mb
            FROM user_ts_quotas
            ORDER BY tablespace_name
        """)
        
        tablespaces = cursor.fetchall()
        if tablespaces:
            for ts in tablespaces:
                max_size = f"{ts[2]:.2f}MB" if ts[2] else "無制限"
                print(f"  💾 {ts[0]:<20} 使用: {ts[1]:.2f}MB 最大: {max_size}")
        else:
            print("  ⚠️  表領域割り当て情報が見つかりませんでした")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("✅ 接続テスト完了")
        print("=" * 60)
        
        return True
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle接続エラー: {error}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_oracle_connection()
    sys.exit(0 if success else 1) 