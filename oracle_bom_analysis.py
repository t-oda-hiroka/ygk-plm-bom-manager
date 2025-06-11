#!/usr/bin/env python3
"""
Oracle Database BOM構造分析スクリプト
製造日報や製品マスタから実際のBOM構造のヒントを探る
"""

import cx_Oracle
import sqlite3
import sys
from datetime import datetime
from collections import defaultdict

# 接続パラメータ
HOST = "hrk-ora-db.cvqkhcprwraj.ap-northeast-1.rds.amazonaws.com"
PORT = 1521
SERVICE_NAME = "orcl"
USERNAME = "ygk_pcs"
PASSWORD = "ygkpcs"

def analyze_bom_patterns():
    """Oracle製造データからBOM構造パターンを分析"""
    
    print("=" * 80)
    print("Oracle Database BOM構造分析")
    print("=" * 80)
    print(f"分析開始時刻: {datetime.now()}")
    print("-" * 80)
    
    try:
        cx_Oracle.init_oracle_client(lib_dir="/usr/local/lib")
        oracle_conn = cx_Oracle.connect(USERNAME, PASSWORD, f"{HOST}:{PORT}/{SERVICE_NAME}")
        cursor = oracle_conn.cursor()
        
        # 1. 製品マスタの糸構成分析
        print("\n🔍 製品マスタの糸構成分析")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 
                YARN_COMPOSITION,
                KNIT,
                COUNT(*) as 製品数
            FROM PCS_PRODUCT_MST
            WHERE YARN_COMPOSITION IS NOT NULL
            AND KNIT IS NOT NULL
            GROUP BY YARN_COMPOSITION, KNIT
            ORDER BY COUNT(*) DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        yarn_patterns = cursor.fetchall()
        
        print("糸構成 × 編み方の組み合わせ:")
        for pattern in yarn_patterns:
            print(f"  📊 {pattern[0]} × {pattern[1]}: {pattern[2]}製品")
            print()
        
        # 2. 製造日報の投入パターン分析（サンプル）
        print("\n🏭 製造日報の投入パターン分析")
        print("=" * 60)
        
        # 最近の投入データからパターンを抽出
        cursor.execute("""
            SELECT * FROM (
                SELECT 
                    見出しID,
                    COUNT(DISTINCT 品目コード) as 使用品目数
                FROM T_製紐_日報_明細_投入
                WHERE 品目コード IS NOT NULL
                AND 作業日時 >= ADD_MONTHS(SYSDATE, -3)
                GROUP BY 見出しID
                HAVING COUNT(DISTINCT 品目コード) >= 2
                ORDER BY COUNT(DISTINCT 品目コード) DESC
            ) WHERE ROWNUM <= 5
        """)
        
        manufacturing_patterns = cursor.fetchall()
        
        if manufacturing_patterns:
            print("複数品目を使用する製造パターン:")
            for pattern in manufacturing_patterns:
                print(f"  🔧 見出しID {pattern[0]}: {pattern[1]}品目使用")
                print()
        
        # 3. 原材料マスタの関連性分析
        print("\n🧶 原材料マスタの構成分析")
        print("=" * 60)
        
        # PS糸と原糸の関係
        cursor.execute("""
            SELECT 
                原糸種類,
                COUNT(*) as PS糸種類数,
                AVG(PS) as 平均PS値,
                AVG(PS糸) as 平均PS糸値
            FROM M_品目_PS糸_仮
            WHERE 原糸種類 IS NOT NULL
            GROUP BY 原糸種類
            ORDER BY PS糸種類数 DESC
        """)
        
        material_patterns = cursor.fetchall()
        
        print("原糸種類別PS糸構成:")
        for pattern in material_patterns:
            print(f"  🧵 {pattern[0]}: {pattern[1]}種類 (平均PS値: {pattern[2]:.2f})")
        
        oracle_conn.close()
        
        # 4. 現在の製品データに基づくBOM構造提案
        print("\n💡 推奨BOM構造パターン")
        print("=" * 60)
        
        sqlite_conn = sqlite3.connect("bom_database_enhanced.db")
        cursor = sqlite_conn.cursor()
        
        # 登録済み製品の確認
        cursor.execute("""
            SELECT item_type, COUNT(*) as count
            FROM items 
            WHERE oracle_product_code IS NOT NULL
            GROUP BY item_type
            ORDER BY count DESC
        """)
        
        current_items = cursor.fetchall()
        
        print("現在の登録製品:")
        for item in current_items:
            print(f"  📦 {item[0]}: {item[1]}件")
        
        sqlite_conn.close()
        
        # 5. BOM構造案の提示
        print("🎯 推奨BOM構造案:")
        print("-" * 40)
        
        bom_proposals = [
            {
                "parent": "完成品 (X-BRAID FC ABSORBER)",
                "components": [
                    {"item": "製紐糸 (X-BRAID)", "quantity": 1, "usage": "Main Material"},
                    {"item": "梱包資材", "quantity": 1, "usage": "Packaging"},
                    {"item": "スプール", "quantity": 1, "usage": "Container"}
                ]
            },
            {
                "parent": "製紐糸 (X-BRAID FULLDRAG X8)",
                "components": [
                    {"item": "原糸 (PEライン)", "quantity": 8, "usage": "Main Braid Thread"},
                    {"item": "芯糸", "quantity": 1, "usage": "Core Thread"}
                ]
            },
            {
                "parent": "PS糸 (OB系)",
                "components": [
                    {"item": "原糸", "quantity": 1, "usage": "Main Material"},
                    {"item": "PS加工材料", "quantity": 1, "usage": "Process Material"}
                ]
            }
        ]
        
        for i, bom in enumerate(bom_proposals, 1):
            print(f"\n{i}. {bom['parent']}")
            for comp in bom['components']:
                print(f"   ├─ {comp['item']} × {comp['quantity']} ({comp['usage']})")
        
        print("\n" + "=" * 80)
        print("✅ BOM構造分析完了")
        print("=" * 80)
        
        return True
        
    except cx_Oracle.Error as error:
        print(f"❌ Oracle接続エラー: {error}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = analyze_bom_patterns()
    sys.exit(0 if success else 1) 