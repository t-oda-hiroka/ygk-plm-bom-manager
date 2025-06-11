"""
釣り糸製造BOM管理システム Web アプリケーション

Flask を使用してBOM管理システムのWebインターフェースを提供します。
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from bom_manager import BOMManager
import os

app = Flask(__name__)
app.secret_key = 'bom_management_secret_key_2024'

# BOMマネージャーのインスタンスを作成
bom_manager = BOMManager("bom_database.db")

# アイテムタイプの定数
ITEM_TYPES = [
    '原糸',
    'PS糸', 
    '製紐糸',
    '染色糸',
    '後PS糸',
    '巻き取り糸',
    '完成品',
    '芯糸',
    '梱包資材',
    '成形品'
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

# 材質タイプの定数
MATERIAL_TYPES = ['EN', 'SK', 'AL', 'PE', 'その他']

# 撚りタイプの定数
TWIST_TYPES = ['S', 'Z']


@app.route('/')
def index():
    """メインページ - アイテム一覧を表示"""
    # フィルタリング用のパラメータを取得
    item_type_filter = request.args.get('item_type', '')
    
    # アイテム一覧を取得
    if item_type_filter and item_type_filter != 'all':
        items = bom_manager.get_all_items_by_type(item_type_filter)
    else:
        # 全アイテムを取得
        all_items = []
        for item_type in ITEM_TYPES:
            items_of_type = bom_manager.get_all_items_by_type(item_type)
            all_items.extend(items_of_type)
        items = all_items
    
    return render_template('index.html', 
                         items=items, 
                         item_types=ITEM_TYPES,
                         current_filter=item_type_filter)


@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    """アイテム追加ページ"""
    if request.method == 'POST':
        # フォームデータを取得
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
                                 twist_types=TWIST_TYPES)
        
        # オプション属性を収集
        attributes = {}
        
        # 材質
        material_type = request.form.get('material_type', '')
        if material_type:
            attributes['material_type'] = material_type
        
        # デニール
        denier = request.form.get('denier', '')
        if denier:
            try:
                attributes['denier'] = int(denier)
            except ValueError:
                flash('デニールは数値で入力してください。', 'error')
                return render_template('add_item.html',
                                     item_types=ITEM_TYPES,
                                     units=UNITS,
                                     material_types=MATERIAL_TYPES,
                                     twist_types=TWIST_TYPES)
        
        # PS値
        ps_ratio = request.form.get('ps_ratio', '')
        if ps_ratio:
            try:
                attributes['ps_ratio'] = float(ps_ratio)
            except ValueError:
                flash('PS値は数値で入力してください。', 'error')
                return render_template('add_item.html',
                                     item_types=ITEM_TYPES,
                                     units=UNITS,
                                     material_types=MATERIAL_TYPES,
                                     twist_types=TWIST_TYPES)
        
        # 編み構造
        braid_structure = request.form.get('braid_structure', '')
        if braid_structure:
            attributes['braid_structure'] = braid_structure
        
        # 芯糸有無
        has_core = request.form.get('has_core') == 'on'
        attributes['has_core'] = has_core
        
        # 色
        color = request.form.get('color', '')
        if color:
            attributes['color'] = color
        
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
                                     twist_types=TWIST_TYPES)
        
        # 撚りタイプ
        twist_type = request.form.get('twist_type', '')
        if twist_type:
            attributes['twist_type'] = twist_type
        
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
                         twist_types=TWIST_TYPES)


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
    
    # 全アイテムを取得（セレクトボックス用）
    all_items = []
    for item_type in ITEM_TYPES:
        items_of_type = bom_manager.get_all_items_by_type(item_type)
        all_items.extend(items_of_type)
    
    return render_template('add_bom.html',
                         all_items=all_items,
                         usage_types=USAGE_TYPES)


@app.route('/item_details/<item_id>')
def item_details(item_id):
    """アイテム詳細ページ"""
    item = bom_manager.get_item(item_id)
    if not item:
        flash(f'アイテム "{item_id}" が見つかりませんでした。', 'error')
        return redirect(url_for('index'))
    
    # 直下の構成部品を取得
    components = bom_manager.get_direct_components(item_id)
    
    return render_template('item_details.html',
                         item=item,
                         components=components)


@app.route('/api/items')
def api_items():
    """アイテム一覧APIエンドポイント（JSON）"""
    item_type = request.args.get('type', '')
    
    if item_type and item_type != 'all':
        items = bom_manager.get_all_items_by_type(item_type)
    else:
        all_items = []
        for item_type in ITEM_TYPES:
            items_of_type = bom_manager.get_all_items_by_type(item_type)
            all_items.extend(items_of_type)
        items = all_items
    
    return jsonify(items)


if __name__ == '__main__':
    # サンプルデータが投入されていない場合は投入
    if not os.path.exists("bom_database.db"):
        from sample_data import create_sample_data
        print("サンプルデータを投入中...")
        create_sample_data()
        print("サンプルデータの投入が完了しました。")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 