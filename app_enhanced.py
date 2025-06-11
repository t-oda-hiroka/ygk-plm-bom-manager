"""
釣り糸製造BOM管理システム Web アプリケーション
Oracle DB連携版

Flask を使用してBOM管理システムのWebインターフェースを提供します。
Oracle製品データを活用した現実的なBOM管理機能を含みます。
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from bom_manager import BOMManager
import sqlite3
import os
import sys

app = Flask(__name__)
app.secret_key = 'bom_management_enhanced_secret_key_2024'

# 拡張データベースを使用
ENHANCED_DB_PATH = "bom_database_enhanced.db"
bom_manager = BOMManager(ENHANCED_DB_PATH)

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


def get_enhanced_items_by_type(item_type: str = 'all'):
    """拡張属性を含むアイテム一覧を取得（工程順ソート）"""
    conn = sqlite3.connect(ENHANCED_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        
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
        
        if item_type == 'all':
            cursor.execute(f"""
                SELECT 
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
                    created_at
                FROM items
                ORDER BY 
                    {process_order_sql},
                    CASE WHEN oracle_product_code IS NOT NULL THEN 0 ELSE 1 END,
                    series_name,
                    item_name
            """)
        else:
            cursor.execute(f"""
                SELECT 
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
                    created_at
                FROM items
                WHERE item_type = ?
                ORDER BY 
                    {process_order_sql},
                    CASE WHEN oracle_product_code IS NOT NULL THEN 0 ELSE 1 END,
                    series_name,
                    item_name
            """, (item_type,))
        
        items = []
        for row in cursor.fetchall():
            items.append(dict(row))
        
        return items
        
    finally:
        conn.close()


@app.route('/')
def index():
    """メインページ - Oracle連携強化アイテム一覧を表示"""
    # フィルタリング用のパラメータを取得
    item_type_filter = request.args.get('item_type', 'all')
    search_query = request.args.get('search', '').strip()
    
    # アイテム一覧を取得
    items = get_enhanced_items_by_type(item_type_filter)
    
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
                         total_items_count=len(items))


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
    """アイテム詳細ページ（Oracle連携強化版）"""
    # 拡張属性を含むアイテム情報を取得
    conn = sqlite3.connect(ENHANCED_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
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
                yarn_type,
                raw_num,
                production_num,
                core_yarn_type,
                spool_type,
                oracle_sync_status,
                oracle_last_sync,
                created_at,
                updated_at
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
                             components=components)
                             
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
                         bom_structure=bom_structure)


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
                                 twist_types=TWIST_TYPES)
        
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
                                     twist_types=TWIST_TYPES)
        
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
                         twist_types=TWIST_TYPES)


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
                         usage_types=USAGE_TYPES)


@app.route('/api/items')
def api_items():
    """アイテム一覧APIエンドポイント（JSON）"""
    item_type = request.args.get('type', 'all')
    items = get_enhanced_items_by_type(item_type)
    return jsonify(items)


if __name__ == '__main__':
    # 拡張データベースの存在確認
    if not os.path.exists(ENHANCED_DB_PATH):
        print("拡張データベースが見つかりません。Oracle統合テストを実行してください。")
        print("実行コマンド: python test_oracle_integration.py")
        sys.exit(1)
    
    print("=" * 60)
    print("釣り糸製造BOM管理システム Oracle連携版")
    print("=" * 60)
    print("機能:")
    print("• Oracle製品データ統合")
    print("• 拡張製品属性表示")
    print("• 高度な検索機能")
    print("• リアルタイム同期")
    print("-" * 60)
    print("アクセス: http://localhost:5002")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5002) 