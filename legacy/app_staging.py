"""
釣り糸製造BOM管理システム - 社内ステージング環境
Oracle DB連携版

社内メンバー向けのプロトタイプ検証環境です。
安全にテストできる分離された環境を提供します。
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from bom_manager import BOMManager
import sqlite3
import os
import sys
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'bom_staging_environment_secret_key_2024'

# ステージング専用データベース
STAGING_DB_PATH = "bom_database_staging.db"
bom_manager = BOMManager(STAGING_DB_PATH)

# 環境設定
ENVIRONMENT = "STAGING"
VERSION = "v1.0-staging"

# アイテムタイプの定数（工程順）
ITEM_TYPES = [
    '完成品',
    '製紐糸',
    'PS糸',
    '染色糸',
    '後PS糸',
    '巻き取り糸',
    '原糸',
    '芯糸',
    '成形品',
    '梱包資材'
]

# 用途タイプの定数
USAGE_TYPES = [
    'Main Material',
    'Main Braid Thread',
    'Core Thread',
    'Packaging',
    'Container',
    'Process Material'
]

# 数量単位の定数
UNITS = ['KG', 'M', '個', '枚', 'セット', '本']

# 材質タイプの定数（Oracle実データから拡張）
MATERIAL_TYPES = ['EN', 'SK', 'AL', 'PE', 'ナイロン', 'その他']

# 撚りタイプの定数
TWIST_TYPES = ['S', 'Z']

# 編み方タイプ（Oracle実データから）
KNIT_TYPES = ['X8', 'X4', 'X9', 'X5', 'X16', 'X6丸', 'その他']


def init_staging_database():
    """ステージング用データベースの初期化"""
    if not os.path.exists(STAGING_DB_PATH):
        print("ステージング用データベースを初期化しています...")
        
        # スキーマ作成
        schema_file = 'schema_enhanced.sql' if os.path.exists('schema_enhanced.sql') else 'schema.sql'
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn = sqlite3.connect(STAGING_DB_PATH)
        conn.executescript(schema_sql)
        conn.close()
        
        # サンプルデータの投入
        try:
            if os.path.exists('create_realistic_bom.py'):
                from create_realistic_bom import create_realistic_bom_data
                create_realistic_bom_data(STAGING_DB_PATH)
                print("ステージング用サンプルデータを作成しました。")
            else:
                # 基本的なサンプルデータを作成
                create_basic_sample_data()
                print("基本サンプルデータを作成しました。")
        except Exception as e:
            print(f"サンプルデータ作成中にエラー: {e}")
            create_basic_sample_data()


def create_basic_sample_data():
    """豊富なサンプルデータを作成"""
    conn = sqlite3.connect(STAGING_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # テーブル構造を確認
        cursor.execute("PRAGMA table_info(items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 拡張カラムの存在確認
        has_extended_columns = 'oracle_product_code' in columns
        
        if has_extended_columns:
            # 拡張スキーマの場合のサンプルアイテム
            sample_items = [
                # 完成品（釣り糸製品）
                ('PRODUCT_001', 'ハイパワーライン 8号 100m', '完成品', '個', 'ORA_PROD_001', 'ナイロン', 'ハイパワー', 100, '青', 'X8'),
                ('PRODUCT_002', 'スーパーライン 10号 150m', '完成品', '個', 'ORA_PROD_002', 'ナイロン', 'スーパー', 150, '緑', 'X8'),
                ('PRODUCT_003', 'プロライン 6号 200m', '完成品', '個', None, 'ナイロン', 'プロ', 200, '赤', 'X4'),
                ('PRODUCT_004', 'メガライン 12号 100m', '完成品', '個', 'ORA_PROD_004', 'ナイロン', 'メガ', 100, '黄', 'X16'),
                ('PRODUCT_005', 'ウルトラライン 8号 250m', '完成品', '個', None, 'ナイロン', 'ウルトラ', 250, '紫', 'X8'),
                
                # 製紐糸
                ('BRAID_001', 'X8編み糸 8号', '製紐糸', 'M', None, 'ナイロン', None, 100, None, 'X8'),
                ('BRAID_002', 'X8編み糸 10号', '製紐糸', 'M', None, 'ナイロン', None, 150, None, 'X8'),
                ('BRAID_003', 'X4編み糸 6号', '製紐糸', 'M', None, 'ナイロン', None, 200, None, 'X4'),
                ('BRAID_004', 'X16編み糸 12号', '製紐糸', 'M', None, 'ナイロン', None, 100, None, 'X16'),
                ('BRAID_005', 'X8編み糸 8号特殊', '製紐糸', 'M', None, 'ナイロン', None, 250, None, 'X8'),
                
                # PS糸
                ('PS_001', 'PS糸 8号', 'PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('PS_002', 'PS糸 10号', 'PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('PS_003', 'PS糸 6号', 'PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('PS_004', 'PS糸 12号', 'PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('PS_005', 'PS糸 8号高強度', 'PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                
                # 染色糸
                ('DYED_001', '染色糸 青', '染色糸', 'KG', None, 'ナイロン', None, None, '青', None),
                ('DYED_002', '染色糸 緑', '染色糸', 'KG', None, 'ナイロン', None, None, '緑', None),
                ('DYED_003', '染色糸 赤', '染色糸', 'KG', None, 'ナイロン', None, None, '赤', None),
                ('DYED_004', '染色糸 黄', '染色糸', 'KG', None, 'ナイロン', None, None, '黄', None),
                ('DYED_005', '染色糸 紫', '染色糸', 'KG', None, 'ナイロン', None, None, '紫', None),
                
                # 後PS糸
                ('POST_PS_001', '後PS糸 8号', '後PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('POST_PS_002', '後PS糸 10号', '後PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('POST_PS_003', '後PS糸 6号', '後PS糸', 'KG', None, 'ナイロン', None, None, None, None),
                
                # 巻き取り糸
                ('WIND_001', '巻き取り糸 8号', '巻き取り糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('WIND_002', '巻き取り糸 10号', '巻き取り糸', 'KG', None, 'ナイロン', None, None, None, None),
                ('WIND_003', '巻き取り糸 6号', '巻き取り糸', 'KG', None, 'ナイロン', None, None, None, None),
                
                # 原糸
                ('YARN_001', 'ナイロン原糸 8号', '原糸', 'KG', 'ORA_YARN_001', 'ナイロン', None, None, None, None),
                ('YARN_002', 'ナイロン原糸 10号', '原糸', 'KG', 'ORA_YARN_002', 'ナイロン', None, None, None, None),
                ('YARN_003', 'ナイロン原糸 6号', '原糸', 'KG', 'ORA_YARN_003', 'ナイロン', None, None, None, None),
                ('YARN_004', 'ナイロン原糸 12号', '原糸', 'KG', 'ORA_YARN_004', 'ナイロン', None, None, None, None),
                ('YARN_005', 'ナイロン原糸 8号高品質', '原糸', 'KG', None, 'ナイロン', None, None, None, None),
                
                # 芯糸
                ('CORE_001', '芯糸 8号', '芯糸', 'KG', None, 'ナイロン', None, None, '白', None),
                ('CORE_002', '芯糸 10号', '芯糸', 'KG', None, 'ナイロン', None, None, '白', None),
                ('CORE_003', '芯糸 6号', '芯糸', 'KG', None, 'ナイロン', None, None, '白', None),
                ('CORE_004', '芯糸 12号', '芯糸', 'KG', None, 'ナイロン', None, None, '白', None),
                
                # 成形品（スプール等）
                ('SPOOL_001', 'プラスチックスプール 100m用', '成形品', '個', None, None, None, None, '黒', None),
                ('SPOOL_002', 'プラスチックスプール 150m用', '成形品', '個', None, None, None, None, '黒', None),
                ('SPOOL_003', 'プラスチックスプール 200m用', '成形品', '個', None, None, None, None, '黒', None),
                ('SPOOL_004', 'プラスチックスプール 250m用', '成形品', '個', None, None, None, None, '黒', None),
                
                # 梱包資材
                ('PACK_001', 'ブリスターパック小', '梱包資材', '枚', None, None, None, None, '透明', None),
                ('PACK_002', 'ブリスターパック中', '梱包資材', '枚', None, None, None, None, '透明', None),
                ('PACK_003', 'ブリスターパック大', '梱包資材', '枚', None, None, None, None, '透明', None),
                ('LABEL_001', 'ラベル ハイパワーシリーズ', '梱包資材', '枚', None, None, None, None, None, None),
                ('LABEL_002', 'ラベル スーパーシリーズ', '梱包資材', '枚', None, None, None, None, None, None),
                ('LABEL_003', 'ラベル プロシリーズ', '梱包資材', '枚', None, None, None, None, None, None),
            ]
            
            for item in sample_items:
                cursor.execute("""
                    INSERT OR IGNORE INTO items 
                    (item_id, item_name, item_type, unit_of_measure, oracle_product_code, 
                     yarn_composition, series_name, length_m, color, knit_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, item)
        else:
            # 基本スキーマの場合のサンプルアイテム
            sample_items = [
                # 完成品
                ('PRODUCT_001', 'ハイパワーライン 8号 100m', '完成品', '個'),
                ('PRODUCT_002', 'スーパーライン 10号 150m', '完成品', '個'),
                ('PRODUCT_003', 'プロライン 6号 200m', '完成品', '個'),
                ('PRODUCT_004', 'メガライン 12号 100m', '完成品', '個'),
                ('PRODUCT_005', 'ウルトラライン 8号 250m', '完成品', '個'),
                
                # 製紐糸
                ('BRAID_001', 'X8編み糸 8号', '製紐糸', 'M'),
                ('BRAID_002', 'X8編み糸 10号', '製紐糸', 'M'),
                ('BRAID_003', 'X4編み糸 6号', '製紐糸', 'M'),
                ('BRAID_004', 'X16編み糸 12号', '製紐糸', 'M'),
                ('BRAID_005', 'X8編み糸 8号特殊', '製紐糸', 'M'),
                
                # PS糸
                ('PS_001', 'PS糸 8号', 'PS糸', 'KG'),
                ('PS_002', 'PS糸 10号', 'PS糸', 'KG'),
                ('PS_003', 'PS糸 6号', 'PS糸', 'KG'),
                ('PS_004', 'PS糸 12号', 'PS糸', 'KG'),
                ('PS_005', 'PS糸 8号高強度', 'PS糸', 'KG'),
                
                # 原糸
                ('YARN_001', 'ナイロン原糸 8号', '原糸', 'KG'),
                ('YARN_002', 'ナイロン原糸 10号', '原糸', 'KG'),
                ('YARN_003', 'ナイロン原糸 6号', '原糸', 'KG'),
                ('YARN_004', 'ナイロン原糸 12号', '原糸', 'KG'),
                ('YARN_005', 'ナイロン原糸 8号高品質', '原糸', 'KG'),
                
                # 芯糸
                ('CORE_001', '芯糸 8号', '芯糸', 'KG'),
                ('CORE_002', '芯糸 10号', '芯糸', 'KG'),
                ('CORE_003', '芯糸 6号', '芯糸', 'KG'),
                ('CORE_004', '芯糸 12号', '芯糸', 'KG'),
                
                # 成形品
                ('SPOOL_001', 'プラスチックスプール 100m用', '成形品', '個'),
                ('SPOOL_002', 'プラスチックスプール 150m用', '成形品', '個'),
                ('SPOOL_003', 'プラスチックスプール 200m用', '成形品', '個'),
                ('SPOOL_004', 'プラスチックスプール 250m用', '成形品', '個'),
                
                # 梱包資材
                ('PACK_001', 'ブリスターパック小', '梱包資材', '枚'),
                ('PACK_002', 'ブリスターパック中', '梱包資材', '枚'),
                ('PACK_003', 'ブリスターパック大', '梱包資材', '枚'),
                ('LABEL_001', 'ラベル ハイパワーシリーズ', '梱包資材', '枚'),
                ('LABEL_002', 'ラベル スーパーシリーズ', '梱包資材', '枚'),
                ('LABEL_003', 'ラベル プロシリーズ', '梱包資材', '枚'),
            ]
            
            for item in sample_items:
                cursor.execute("""
                    INSERT OR IGNORE INTO items 
                    (item_id, item_name, item_type, unit_of_measure)
                    VALUES (?, ?, ?, ?)
                """, item)
        
        # 複雑なBOM構成を作成
        sample_boms = [
            # ハイパワーライン 8号 100m の構成
            ('PRODUCT_001', 'BRAID_001', 1.0, 'Main Material'),
            ('PRODUCT_001', 'SPOOL_001', 1.0, 'Container'),
            ('PRODUCT_001', 'PACK_001', 1.0, 'Packaging'),
            ('PRODUCT_001', 'LABEL_001', 1.0, 'Packaging'),
            
            # スーパーライン 10号 150m の構成
            ('PRODUCT_002', 'BRAID_002', 1.0, 'Main Material'),
            ('PRODUCT_002', 'SPOOL_002', 1.0, 'Container'),
            ('PRODUCT_002', 'PACK_002', 1.0, 'Packaging'),
            ('PRODUCT_002', 'LABEL_002', 1.0, 'Packaging'),
            
            # プロライン 6号 200m の構成
            ('PRODUCT_003', 'BRAID_003', 1.0, 'Main Material'),
            ('PRODUCT_003', 'SPOOL_003', 1.0, 'Container'),
            ('PRODUCT_003', 'PACK_003', 1.0, 'Packaging'),
            ('PRODUCT_003', 'LABEL_003', 1.0, 'Packaging'),
            
            # メガライン 12号 100m の構成
            ('PRODUCT_004', 'BRAID_004', 1.0, 'Main Material'),
            ('PRODUCT_004', 'SPOOL_001', 1.0, 'Container'),
            ('PRODUCT_004', 'PACK_001', 1.0, 'Packaging'),
            
            # ウルトラライン 8号 250m の構成
            ('PRODUCT_005', 'BRAID_005', 1.0, 'Main Material'),
            ('PRODUCT_005', 'SPOOL_004', 1.0, 'Container'),
            ('PRODUCT_005', 'PACK_003', 1.0, 'Packaging'),
            
            # 製紐糸の構成
            ('BRAID_001', 'PS_001', 0.8, 'Main Braid Thread'),
            ('BRAID_001', 'CORE_001', 0.1, 'Core Thread'),
            ('BRAID_002', 'PS_002', 0.8, 'Main Braid Thread'),
            ('BRAID_002', 'CORE_002', 0.1, 'Core Thread'),
            ('BRAID_003', 'PS_003', 0.8, 'Main Braid Thread'),
            ('BRAID_003', 'CORE_003', 0.1, 'Core Thread'),
            ('BRAID_004', 'PS_004', 0.8, 'Main Braid Thread'),
            ('BRAID_004', 'CORE_004', 0.1, 'Core Thread'),
            ('BRAID_005', 'PS_005', 0.8, 'Main Braid Thread'),
            ('BRAID_005', 'CORE_001', 0.1, 'Core Thread'),
            
            # PS糸の構成
            ('PS_001', 'YARN_001', 0.9, 'Main Material'),
            ('PS_002', 'YARN_002', 0.9, 'Main Material'),
            ('PS_003', 'YARN_003', 0.9, 'Main Material'),
            ('PS_004', 'YARN_004', 0.9, 'Main Material'),
            ('PS_005', 'YARN_005', 0.9, 'Main Material'),
        ]
        
        for bom in sample_boms:
            cursor.execute("""
                INSERT OR IGNORE INTO bom_components 
                (parent_item_id, component_item_id, quantity, usage_type)
                VALUES (?, ?, ?, ?)
            """, bom)
        
        conn.commit()
        
        # 統計を表示
        cursor.execute("SELECT COUNT(*) FROM items")
        item_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bom_components")
        bom_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT item_type) FROM items")
        type_count = cursor.fetchone()[0]
        
        print(f"豊富なサンプルデータを作成しました:")
        print(f"  - アイテム数: {item_count}件")
        print(f"  - BOM構成: {bom_count}件")
        print(f"  - アイテムタイプ: {type_count}種類")
        print(f"  - スキーマタイプ: {'拡張' if has_extended_columns else '基本'}")
        
    finally:
        conn.close()


def get_enhanced_items_by_type(item_type: str = 'all'):
    """拡張属性を含むアイテム一覧を取得（工程順ソート）"""
    conn = sqlite3.connect(STAGING_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        
        # テーブル構造確認
        cursor.execute("PRAGMA table_info(items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 基本カラム
        select_columns = [
            "item_id",
            "item_name", 
            "item_type",
            "unit_of_measure",
            "created_at"
        ]
        
        # 拡張カラムを安全に追加
        if 'oracle_product_code' in columns:
            select_columns.append("oracle_product_code")
        else:
            select_columns.append("NULL as oracle_product_code")
            
        if 'yarn_composition' in columns:
            select_columns.append("yarn_composition")
        else:
            select_columns.append("NULL as yarn_composition")
            
        if 'series_name' in columns:
            select_columns.append("series_name")
        else:
            select_columns.append("NULL as series_name")
            
        if 'length_m' in columns:
            select_columns.append("length_m")
        else:
            select_columns.append("NULL as length_m")
            
        if 'color' in columns:
            select_columns.append("color")
        else:
            select_columns.append("NULL as color")
            
        if 'knit_type' in columns:
            select_columns.append("knit_type")
        else:
            select_columns.append("NULL as knit_type")
            
        if 'oracle_sync_status' in columns:
            select_columns.append("oracle_sync_status")
        else:
            select_columns.append("NULL as oracle_sync_status")
        
        # 工程順のソート順序を定義
        process_order_sql = """
            CASE item_type
                WHEN '完成品' THEN 1
                WHEN '製紐糸' THEN 2
                WHEN 'PS糸' THEN 3
                WHEN '染色糸' THEN 4
                WHEN '後PS糸' THEN 5
                WHEN '巻き取り糸' THEN 6
                WHEN '原糸' THEN 7
                WHEN '芯糸' THEN 8
                WHEN '成形品' THEN 9
                WHEN '梱包資材' THEN 10
                ELSE 11
            END
        """
        
        # 安全なORDER BY句（カラム存在確認）
        if 'oracle_product_code' in columns and 'series_name' in columns:
            order_clause = f"""
                ORDER BY 
                    {process_order_sql},
                    CASE WHEN oracle_product_code IS NOT NULL THEN 0 ELSE 1 END,
                    series_name,
                    item_name
            """
        else:
            order_clause = f"""
                ORDER BY 
                    {process_order_sql},
                    item_name
            """
        
        # クエリ実行
        if item_type == 'all':
            cursor.execute(f"""
                SELECT {', '.join(select_columns)}
                FROM items
                {order_clause}
            """)
        else:
            cursor.execute(f"""
                SELECT {', '.join(select_columns)}
                FROM items
                WHERE item_type = ?
                {order_clause}
            """, (item_type,))
        
        items = []
        for row in cursor.fetchall():
            items.append(dict(row))
        
        return items
        
    finally:
        conn.close()


@app.route('/')
def index():
    """メインページ - ステージング環境アイテム一覧"""
    # フィルタリング用のパラメータを取得
    item_type_filter = request.args.get('item_type', 'all')
    search_query = request.args.get('search', '').strip()
    
    # 全アイテムを取得（統計計算のため）
    all_items = get_enhanced_items_by_type('all')
    
    # アイテムタイプ別の統計を計算
    item_type_stats = {}
    for item_type in ITEM_TYPES:
        item_type_stats[item_type] = len([item for item in all_items if item.get('item_type') == item_type])
    
    # フィルタリングされたアイテム一覧を取得
    if item_type_filter and item_type_filter != 'all':
        items = get_enhanced_items_by_type(item_type_filter)
    else:
        items = all_items
    
    # 検索フィルタリング
    if search_query:
        filtered_items = []
        for item in items:
            # 商品名、シリーズ名、糸構成で検索
            searchable_text = ' '.join(filter(None, [
                item.get('item_name', ''),
                item.get('series_name', ''),
                item.get('yarn_composition', ''),
                item.get('color', '')
            ])).upper()
            
            if search_query.upper() in searchable_text:
                filtered_items.append(item)
        items = filtered_items
    
    # Oracle連携製品数をカウント
    oracle_items_count = len([item for item in items if item.get('oracle_product_code')])
    
    return render_template('index.html', 
                         items=items,
                         item_types=ITEM_TYPES,
                         current_filter=item_type_filter,
                         search_query=search_query,
                         oracle_items_count=oracle_items_count,
                         total_items_count=len(items),
                         item_type_stats=item_type_stats,
                         environment=ENVIRONMENT,
                         version=VERSION,
                         is_staging=True)


@app.route('/oracle_sync')
def oracle_sync():
    """Oracle同期ページ"""
    return jsonify({"message": "Oracle同期機能は実装中です"})


@app.route('/api/oracle_sync', methods=['POST'])
def api_oracle_sync():
    """Oracle同期API"""
    try:
        # Oracle同期テストスクリプトを実行
        import subprocess
        result = subprocess.run([sys.executable, 'test_oracle_integration.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Oracle同期が完了しました',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Oracle同期でエラーが発生しました',
                'error': result.stderr
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'同期処理エラー: {str(e)}'
        })


@app.route('/item_details/<item_id>')
def item_details(item_id):
    """アイテム詳細ページ（ステージング版）"""
    # 拡張属性を含むアイテム情報を取得
    conn = sqlite3.connect(STAGING_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        
        # テーブル構造を確認
        cursor.execute("PRAGMA table_info(items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 基本カラム
        select_columns = ["item_id", "item_name", "item_type", "unit_of_measure", "created_at"]
        
        # 拡張カラムを安全に追加
        extended_columns = [
            'oracle_product_code', 'yarn_composition', 'series_name', 'length_m', 
            'color', 'knit_type', 'yarn_type', 'raw_num', 'production_num', 
            'core_yarn_type', 'spool_type', 'oracle_sync_status', 'oracle_last_sync', 'updated_at'
        ]
        
        for col in extended_columns:
            if col in columns:
                select_columns.append(col)
            else:
                select_columns.append(f"NULL as {col}")
        
        cursor.execute(f"""
            SELECT {', '.join(select_columns)}
            FROM items
            WHERE item_id = ?
        """, (item_id,))
        
        row = cursor.fetchone()
        if not row:
            flash(f'アイテム "{item_id}" が見つかりませんでした。', 'error')
            return redirect(url_for('index'))
        
        item = dict(row)
        
        # 直下の構成部品を取得
        components = bom_manager.get_direct_components(item_id)
        
        return render_template('item_details.html',
                             item=item,
                             components=components,
                             environment=ENVIRONMENT,
                             is_staging=True)
                             
    finally:
        conn.close()


@app.route('/bom_tree/<item_id>')
def bom_tree(item_id):
    """BOM構造ツリーページ"""
    # アイテム情報を取得
    item = bom_manager.get_item(item_id)
    if not item:
        flash(f'アイテム "{item_id}" が見つかりませんでした。', 'error')
        return redirect(url_for('index'))
    
    # BOM構造を取得
    bom_structure = bom_manager.get_multi_level_bom(item_id)
    
    return render_template('bom_tree.html',
                         item=item,
                         bom_structure=bom_structure,
                         environment=ENVIRONMENT,
                         is_staging=True)


@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    """アイテム追加ページ（拡張版）"""
    if request.method == 'POST':
        # 基本フィールド
        item_id = request.form.get('item_id', '').strip()
        item_name = request.form.get('item_name', '').strip()
        item_type = request.form.get('item_type', '')
        unit_of_measure = request.form.get('unit_of_measure', '')
        
        # 必須フィールドの検証
        if not all([item_id, item_name, item_type, unit_of_measure]):
            flash('必須フィールドをすべて入力してください。', 'error')
            return render_template('add_item.html',
                                 item_types=ITEM_TYPES,
                                 units=UNITS,
                                 material_types=MATERIAL_TYPES,
                                 knit_types=KNIT_TYPES,
                                 twist_types=TWIST_TYPES,
                                 environment=ENVIRONMENT,
                                 is_staging=True)
        
        # 拡張属性を収集
        attributes = {}
        
        # 糸構成
        yarn_composition = request.form.get('yarn_composition', '')
        if yarn_composition:
            attributes['yarn_composition'] = yarn_composition
        
        # シリーズ名
        series_name = request.form.get('series_name', '')
        if series_name:
            attributes['series_name'] = series_name
        
        # 色
        color = request.form.get('color', '')
        if color:
            attributes['color'] = color
        
        # 編み方
        knit_type = request.form.get('knit_type', '')
        if knit_type:
            attributes['knit_type'] = knit_type
        
        # 長さ
        length_m = request.form.get('length_m', '')
        if length_m:
            try:
                attributes['length_m'] = int(length_m)
            except ValueError:
                flash('長さ(m)は数値で入力してください。', 'error')
                return render_template('add_item.html',
                                     item_types=ITEM_TYPES,
                                     units=UNITS,
                                     material_types=MATERIAL_TYPES,
                                     knit_types=KNIT_TYPES,
                                     twist_types=TWIST_TYPES,
                                     environment=ENVIRONMENT,
                                     is_staging=True)
        
        # アイテムを追加
        success = bom_manager.add_item(
            item_id=item_id,
            item_name=item_name,
            item_type=item_type,
            unit_of_measure=unit_of_measure,
            **attributes
        )
        
        if success:
            flash(f'アイテム "{item_name}" を追加しました。', 'success')
            return redirect(url_for('index'))
        else:
            flash('アイテムの追加に失敗しました。IDが重複している可能性があります。', 'error')
    
    return render_template('add_item.html',
                         item_types=ITEM_TYPES,
                         units=UNITS,
                         material_types=MATERIAL_TYPES,
                         knit_types=KNIT_TYPES,
                         twist_types=TWIST_TYPES,
                         environment=ENVIRONMENT,
                         is_staging=True)


@app.route('/add_bom', methods=['GET', 'POST'])
def add_bom():
    """BOM構成追加ページ"""
    if request.method == 'POST':
        parent_item_id = request.form.get('parent_item_id', '').strip()
        component_item_id = request.form.get('component_item_id', '').strip()
        quantity = request.form.get('quantity', '').strip()
        usage_type = request.form.get('usage_type', '')
        
        # 必須フィールドの検証
        if not all([parent_item_id, component_item_id, quantity, usage_type]):
            flash('すべてのフィールドを入力してください。', 'error')
        else:
            try:
                quantity_float = float(quantity)
                
                # 親アイテムと構成部品アイテムの存在確認
                parent_item = bom_manager.get_item(parent_item_id)
                component_item = bom_manager.get_item(component_item_id)
                
                if not parent_item:
                    flash(f'親アイテム "{parent_item_id}" が見つかりません。', 'error')
                elif not component_item:
                    flash(f'構成部品アイテム "{component_item_id}" が見つかりません。', 'error')
                elif parent_item_id == component_item_id:
                    flash('親アイテムと構成部品アイテムは同じにできません。', 'error')
                else:
                    # BOM構成を追加
                    success = bom_manager.add_bom_component(
                        parent_item_id=parent_item_id,
                        component_item_id=component_item_id,
                        quantity=quantity_float,
                        usage_type=usage_type
                    )
                    
                    if success:
                        flash(f'BOM構成を追加しました。', 'success')
                        return redirect(url_for('bom_tree', item_id=parent_item_id))
                    else:
                        flash('BOM構成の追加に失敗しました。', 'error')
                        
            except ValueError:
                flash('数量は数値で入力してください。', 'error')
    
    # 拡張アイテム一覧を取得
    all_items = get_enhanced_items_by_type('all')
    
    return render_template('add_bom.html',
                         all_items=all_items,
                         usage_types=USAGE_TYPES,
                         environment=ENVIRONMENT,
                         is_staging=True)


@app.route('/api/items')
def api_items():
    """アイテム一覧APIエンドポイント（JSON）"""
    item_type = request.args.get('type', 'all')
    items = get_enhanced_items_by_type(item_type)
    return jsonify(items)


@app.route('/api/status')
def api_status():
    """ステージング環境の状態確認API"""
    conn = sqlite3.connect(STAGING_DB_PATH)
    cursor = conn.cursor()
    
    # データベース統計
    cursor.execute("SELECT COUNT(*) FROM items")
    total_items = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bom_components")
    total_bom_components = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT item_type) FROM items")
    item_type_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'environment': ENVIRONMENT,
        'version': VERSION,
        'database_path': STAGING_DB_PATH,
        'total_items': total_items,
        'total_bom_components': total_bom_components,
        'item_type_count': item_type_count,
        'last_updated': datetime.now().isoformat()
    })


@app.route('/reset_staging', methods=['POST'])
def reset_staging():
    """ステージングデータベースのリセット（管理者用）"""
    try:
        if os.path.exists(STAGING_DB_PATH):
            os.remove(STAGING_DB_PATH)
        
        init_staging_database()
        flash('ステージング環境をリセットしました。', 'success')
        
    except Exception as e:
        flash(f'リセット中にエラーが発生しました: {str(e)}', 'error')
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    # ステージング用データベースの初期化
    init_staging_database()
    
    print("=" * 60)
    print("釣り糸製造BOM管理システム - 社内ステージング環境")
    print("=" * 60)
    print(f"環境: {ENVIRONMENT}")
    print(f"バージョン: {VERSION}")
    print(f"データベース: {STAGING_DB_PATH}")
    print("機能:")
    print("• 安全なテスト環境")
    print("• サンプルデータ付き")
    print("• リセット機能")
    print("• 拡張製品属性表示")
    print("• BOM構造管理")
    print("-" * 60)
    print("アクセス: http://localhost:5003")
    print("社内メンバー向けプロトタイプ検証環境です")
    print("=" * 60)
    
    app.run(debug=False, host='0.0.0.0', port=5003) 