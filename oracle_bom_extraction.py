#!/usr/bin/env python3
"""
Oracle Database BOM構造抽出調査スクリプト
製造日報から実際のBOM構造を逆算する調査
"""

import cx_Oracle
import sys
from datetime import datetime
import pandas as pd

# 接続パラメータ
HOST = "hrk-ora-db.cvqkhcprwraj.ap-northeast-1.rds.amazonaws.com"
PORT = 1521
SERVICE_NAME = "orcl"
USERNAME = "ygk_pcs"
PASSWORD = "ygkpcs"

def extract_bom_structure():
    """製造日報からBOM構造を抽出"""
    
    # Oracle Instant Clientライブラリパスを明示的に指定
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
    except Exception as e:
        if "has already been initialized" not in str(e):
            print(f"⚠️  Oracle Client初期化警告: {e}")
    
    dsn = f"{HOST}:{PORT}/{SERVICE_NAME}"
    
    print("=" * 80)
    print("Oracle Database BOM構造抽出調査")
    print("=" * 80)
    print(f"調査開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        connection = cx_Oracle.connect(USERNAME, PASSWORD, dsn)
        cursor = connection.cursor()
        
        # 1. 製造日報投入テーブルのサンプルデータを取得
        print("\n📊 T_製紐_日報_明細_投入 サンプルデータ")
        print("=" * 60)
        
        cursor.execute("""
            SELECT * FROM (
                SELECT 
                    見出しID,
                    作業日時,
                    品目コード,
                    品目ID,
                    投入数量,
                    巻きM,
                    備考
                FROM T_製紐_日報_明細_投入
                WHERE 品目コード IS NOT NULL
                ORDER BY 作業日時 DESC
            ) WHERE ROWNUM <= 10
        """)
        
        投入データ = cursor.fetchall()
        
        if 投入データ:
            print("最新の投入記録:")
            for i, row in enumerate(投入データ):
                print(f"  {i+1:2d}. 見出し:{row[0]:<8} 品目:{row[2]:<15} 投入量:{row[4]:<8} 巻きM:{row[5]:<10} 日時:{row[1]}")
        
        # 2. 品目コード別の使用頻度分析
        print("\n📈 品目コード使用頻度 TOP 20")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 
                品目コード,
                COUNT(*) as 使用回数,
                SUM(投入数量) as 総投入量,
                AVG(投入数量) as 平均投入量
            FROM T_製紐_日報_明細_投入
            WHERE 品目コード IS NOT NULL
            AND 投入数量 > 0
            GROUP BY 品目コード
            ORDER BY 使用回数 DESC
            FETCH FIRST 20 ROWS ONLY
        """)
        
        頻度データ = cursor.fetchall()
        
        if 頻度データ:
            print(f"{'品目コード':<15} {'使用回数':<8} {'総投入量':<12} {'平均投入量'}")
            print("-" * 60)
            for row in 頻度データ:
                print(f"{row[0]:<15} {row[1]:<8} {row[2]:<12.2f} {row[3]:<12.2f}")
        
        # 3. 見出しIDごとの投入パターン分析（BOM候補）
        print("\n🔍 見出しID別投入パターン分析（BOM構造候補）")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 見出しID, COUNT(DISTINCT 品目コード) as 品目種類数
            FROM T_製紐_日報_明細_投入
            WHERE 品目コード IS NOT NULL
            GROUP BY 見出しID
            HAVING COUNT(DISTINCT 品目コード) >= 2
            ORDER BY 品目種類数 DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        パターンデータ = cursor.fetchall()
        
        if パターンデータ:
            print("複数品目を使用する製造パターン:")
            for row in パターンデータ:
                print(f"  見出しID: {row[0]:<10} 使用品目種類数: {row[1]}")
                
                # 各見出しIDの詳細投入内容を取得
                cursor.execute("""
                    SELECT 品目コード, SUM(投入数量) as 総量, COUNT(*) as 回数
                    FROM T_製紐_日報_明細_投入
                    WHERE 見出しID = :見出しID
                    AND 品目コード IS NOT NULL
                    GROUP BY 品目コード
                    ORDER BY 総量 DESC
                """, {"見出しID": row[0]})
                
                詳細データ = cursor.fetchall()
                for detail in 詳細データ:
                    print(f"    📦 {detail[0]:<15} 総量:{detail[1]:<10.2f} 使用回数:{detail[2]}")
                print()
        
        # 4. 製品マスタとの照合
        print("\n🔗 製品マスタとの照合調査")
        print("=" * 60)
        
        cursor.execute("""
            SELECT DISTINCT i.品目コード, p.PRODUCT_NAME, p.YARN_COMPOSITION
            FROM T_製紐_日報_明細_投入 i
            JOIN PCS_PRODUCT_MST p ON i.品目コード = p.PRODUCT_CODE
            WHERE i.品目コード IS NOT NULL
            AND p.PRODUCT_NAME IS NOT NULL
            AND ROWNUM <= 10
        """)
        
        製品照合データ = cursor.fetchall()
        
        if 製品照合データ:
            print("製品マスタと一致する品目:")
            for row in 製品照合データ:
                print(f"  📦 {row[0]:<15} {row[1]:<30} 糸構成:{row[2] or 'N/A'}")
        
        # 5. 時系列でのBOM使用パターン
        print("\n📅 時系列BOM使用パターン")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 
                TO_CHAR(作業日時, 'YYYY-MM') as 年月,
                COUNT(DISTINCT 品目コード) as 使用品目数,
                COUNT(*) as 投入回数
            FROM T_製紐_日報_明細_投入
            WHERE 品目コード IS NOT NULL
            AND 作業日時 >= ADD_MONTHS(SYSDATE, -12)
            GROUP BY TO_CHAR(作業日時, 'YYYY-MM')
            ORDER BY 年月 DESC
        """)
        
        時系列データ = cursor.fetchall()
        
        if 時系列データ:
            print("過去12ヶ月の品目使用状況:")
            for row in 時系列データ:
                print(f"  📅 {row[0]}: {row[1]:<4}品目 {row[2]:<8}回投入")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 80)
        print("✅ BOM構造抽出調査完了")
        print("=" * 80)
        
        return True
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle接続エラー: {error}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = extract_bom_structure()
    sys.exit(0 if success else 1) 