"""
釣り糸製造BOM管理システム 統合アプリケーション
環境設定に基づく自動切り替え対応
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from bom_manager import BOMManager
import sqlite3
import os
import sys
from datetime import datetime
from config import get_config, create_deployment_info

def create_app(environment=None):
    """アプリケーションファクトリ"""
    app = Flask(__name__)
    
    # 設定の読み込み
    config_class = get_config(environment)
    app.config.from_object(config_class)
    
    # 設定の初期化
    config_class.init_app(app)
    
    # BOMマネージャーの初期化
    bom_manager = BOMManager(app.config['DATABASE_PATH'])
    
    # データベース初期化
    init_database(app)
    
    # ルートの登録
    register_routes(app, bom_manager)
    
    return app


def init_database(app):
    """データベースの初期化"""
    if not os.path.exists(app.config['DATABASE_PATH']) or app.config['ENVIRONMENT'] == 'TESTING':
        print(f"{app.config['ENVIRONMENT']}用データベースを初期化しています...")
        
        # スキーマ作成
        with open(app.config['SCHEMA_FILE'], 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        conn.executescript(schema_sql)
        conn.close()
        
        # サンプルデータの生成（開発・ステージング環境のみ）
        if app.config.get('ENABLE_SAMPLE_DATA'):
            create_sample_data_for_app(app)


def create_sample_data_for_app(app):
    """環境に応じたサンプルデータの作成"""
    try:
        # BOMManagerを直接使用してサンプルデータ作成
        bom = BOMManager(app.config['DATABASE_PATH'])
        
        # サンプルアイテムの作成
        sample_items = [
            # 完成品
            ("PRODUCT_001", "ハイパワーライン 8号 100m", "完成品", "個"),
            ("PRODUCT_002", "スーパーライン 10号 150m", "完成品", "個"),
            ("PRODUCT_003", "プロライン 6号 200m", "完成品", "個"),
            
            # 製紐糸
            ("BRAID_001", "X8編み糸 グレード1", "製紐糸", "M"),
            ("BRAID_002", "X4編み糸 グレード2", "製紐糸", "M"),
            ("BRAID_003", "X16編み糸 高強度", "製紐糸", "M"),
            
            # PS糸
            ("PS_001", "PS糸 6号", "PS糸", "M"),
            ("PS_002", "PS糸 8号", "PS糸", "M"),
            ("PS_003", "PS糸 10号", "PS糸", "M"),
            
            # 染色糸
            ("DYE_001", "染色糸 ブルー", "染色糸", "M"),
            ("DYE_002", "染色糸 グリーン", "染色糸", "M"),
            ("DYE_003", "染色糸 レッド", "染色糸", "M"),
            
            # 原糸
            ("RAW_001", "ナイロン原糸 150D", "原糸", "KG"),
            ("RAW_002", "ナイロン原糸 200D", "原糸", "KG"),
            ("RAW_003", "ナイロン原糸 100D", "原糸", "KG"),
            
            # 芯糸
            ("CORE_001", "芯糸 6号", "芯糸", "M"),
            ("CORE_002", "芯糸 8号", "芯糸", "M"),
            
            # 成形品
            ("MOLD_001", "100m用スプール", "成形品", "個"),
            ("MOLD_002", "150m用スプール", "成形品", "個"),
            ("MOLD_003", "200m用スプール", "成形品", "個"),
            
            # 梱包資材
            ("PKG_001", "ブリスターパック 100m用", "梱包資材", "個"),
            ("PKG_002", "ブリスターパック 150m用", "梱包資材", "個"),
            ("PKG_003", "製品ラベル", "梱包資材", "枚"),
        ]
        
        for item_id, item_name, item_type, unit in sample_items:
            bom.add_item(
                item_id=item_id,
                item_name=item_name,
                item_type=item_type,
                unit_of_measure=unit
            )
        
        # BOM構成の作成
        bom_relations = [
            # 完成品 -> 構成部品
            ("PRODUCT_001", "BRAID_001", 100.0, "Main Material"),
            ("PRODUCT_001", "MOLD_001", 1.0, "Container"),
            ("PRODUCT_001", "PKG_001", 1.0, "Packaging"),
            
            ("PRODUCT_002", "BRAID_002", 150.0, "Main Material"),
            ("PRODUCT_002", "MOLD_002", 1.0, "Container"),
            ("PRODUCT_002", "PKG_002", 1.0, "Packaging"),
            
            ("PRODUCT_003", "BRAID_003", 200.0, "Main Material"),
            ("PRODUCT_003", "MOLD_003", 1.0, "Container"),
            ("PRODUCT_003", "PKG_003", 2.0, "Packaging"),
            
            # 製紐糸 -> PS糸 + 芯糸
            ("BRAID_001", "PS_001", 8.0, "Main Braid Thread"),
            ("BRAID_001", "CORE_001", 1.0, "Core Thread"),
            
            ("BRAID_002", "PS_002", 4.0, "Main Braid Thread"),
            ("BRAID_002", "CORE_002", 1.0, "Core Thread"),
            
            ("BRAID_003", "PS_003", 16.0, "Main Braid Thread"),
            ("BRAID_003", "CORE_001", 1.0, "Core Thread"),
            
            # PS糸 -> 原糸
            ("PS_001", "RAW_001", 0.8, "Main Material"),
            ("PS_002", "RAW_002", 0.8, "Main Material"),
            ("PS_003", "RAW_003", 0.8, "Main Material"),
        ]
        
        for parent_id, component_id, quantity, usage_type in bom_relations:
            bom.add_bom_component(
                parent_item_id=parent_id,
                component_item_id=component_id,
                quantity=quantity,
                usage_type=usage_type
            )
        
        print(f"{app.config['ENVIRONMENT']}用サンプルデータを作成しました。")
        print(f"  - アイテム数: {len(sample_items)}件")
        print(f"  - BOM構成: {len(bom_relations)}件")
        
    except Exception as e:
        print(f"サンプルデータ作成中にエラー: {e}")
        import traceback
        traceback.print_exc()
        # フォールバック：基本的なサンプルデータ
        create_basic_sample_data(app.config['DATABASE_PATH'])
        print("基本サンプルデータを作成しました。")


def create_basic_sample_data(database_path):
    """基本的なサンプルデータの作成（フォールバック用）"""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    try:
        # 基本的なアイテムのみ作成
        basic_items = [
            ('SAMPLE_001', 'サンプル完成品', '完成品', '個'),
            ('SAMPLE_002', 'サンプル原糸', '原糸', 'KG'),
        ]
        
        for item in basic_items:
            cursor.execute("""
                INSERT OR IGNORE INTO items 
                (item_id, item_name, item_type, unit_of_measure)
                VALUES (?, ?, ?, ?)
            """, item)
        
        conn.commit()
    finally:
        conn.close()


def register_routes(app, bom_manager):
    """ルートの登録"""
    
    @app.route('/')
    def index():
        """メインページ"""
        # フィルタリング用のパラメータを取得
        item_type_filter = request.args.get('item_type', 'all')
        search_query = request.args.get('search', '').strip()
        
        # アイテム一覧を取得
        items = get_items_by_type(bom_manager, item_type_filter)
        
        # 検索フィルタリング
        if search_query:
            items = filter_items_by_search(items, search_query)
        
        # 統計計算
        all_items = get_items_by_type(bom_manager, 'all')
        item_type_stats = calculate_item_stats(all_items, app.config['ITEM_TYPES'])
        oracle_items_count = count_oracle_items(items)
        
        # 環境に応じたテンプレート変数
        template_vars = {
            'items': items,
            'item_types': app.config['ITEM_TYPES'],
            'current_filter': item_type_filter,
            'search_query': search_query,
            'oracle_items_count': oracle_items_count,
            'total_items_count': len(items),
            'item_type_stats': item_type_stats,
            'environment': app.config['ENVIRONMENT'],
            'version': app.config['VERSION'],
        }
        
        # 環境固有の変数
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
        
        return render_template('index.html', **template_vars)
    
    
    @app.route('/item_details/<item_id>')
    def item_details(item_id):
        """アイテム詳細ページ"""
        item = bom_manager.get_item(item_id)
        if not item:
            flash(f'アイテム "{item_id}" が見つかりませんでした。', 'error')
            return redirect(url_for('index'))
        
        components = bom_manager.get_direct_components(item_id)
        
        template_vars = {
            'item': item,
            'components': components,
            'environment': app.config['ENVIRONMENT'],
        }
        
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
            
        return render_template('item_details.html', **template_vars)
    
    
    @app.route('/bom_tree/<item_id>')
    def bom_tree(item_id):
        """BOM構造ツリーページ"""
        item = bom_manager.get_item(item_id)
        if not item:
            flash(f'アイテム "{item_id}" が見つかりませんでした。', 'error')
            return redirect(url_for('index'))
        
        bom_structure = bom_manager.get_multi_level_bom(item_id)
        
        template_vars = {
            'item': item,
            'bom_structure': bom_structure,
            'environment': app.config['ENVIRONMENT'],
        }
        
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
            
        return render_template('bom_tree.html', **template_vars)
    
    
    @app.route('/add_item', methods=['GET', 'POST'])
    def add_item():
        """アイテム追加ページ"""
        if request.method == 'POST':
            # フォームデータの処理
            item_id = request.form.get('item_id', '').strip()
            item_name = request.form.get('item_name', '').strip()
            item_type = request.form.get('item_type', '')
            unit_of_measure = request.form.get('unit_of_measure', '')
            
            # 必須フィールドの検証
            if not all([item_id, item_name, item_type, unit_of_measure]):
                flash('必須フィールドをすべて入力してください。', 'error')
            else:
                # 拡張属性の収集
                attributes = collect_extended_attributes(request.form)
                
                # アイテムの追加
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
                    flash('アイテムの追加に失敗しました。', 'error')
        
        template_vars = {
            'item_types': app.config['ITEM_TYPES'],
            'units': app.config['UNITS'],
            'material_types': app.config['MATERIAL_TYPES'],
            'knit_types': app.config['KNIT_TYPES'],
            'twist_types': app.config['TWIST_TYPES'],
            'environment': app.config['ENVIRONMENT'],
        }
        
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
            
        return render_template('add_item.html', **template_vars)
    
    
    @app.route('/add_bom', methods=['GET', 'POST'])
    def add_bom():
        """BOM構成追加ページ"""
        if request.method == 'POST':
            parent_item_id = request.form.get('parent_item_id', '').strip()
            component_item_id = request.form.get('component_item_id', '').strip()
            quantity = request.form.get('quantity', '').strip()
            usage_type = request.form.get('usage_type', '')
            
            if not all([parent_item_id, component_item_id, quantity, usage_type]):
                flash('すべてのフィールドを入力してください。', 'error')
            else:
                try:
                    quantity_float = float(quantity)
                    
                    # 存在確認
                    parent_item = bom_manager.get_item(parent_item_id)
                    component_item = bom_manager.get_item(component_item_id)
                    
                    if not parent_item:
                        flash(f'親アイテム "{parent_item_id}" が見つかりません。', 'error')
                    elif not component_item:
                        flash(f'構成部品アイテム "{component_item_id}" が見つかりません。', 'error')
                    elif parent_item_id == component_item_id:
                        flash('親アイテムと構成部品アイテムは同じにできません。', 'error')
                    else:
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
        
        all_items = get_items_by_type(bom_manager, 'all')
        
        template_vars = {
            'all_items': all_items,
            'usage_types': app.config['USAGE_TYPES'],
            'environment': app.config['ENVIRONMENT'],
        }
        
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
            
        return render_template('add_bom.html', **template_vars)
    
    
    @app.route('/api/items')
    def api_items():
        """アイテム一覧API"""
        item_type = request.args.get('type', 'all')
        items = get_items_by_type(bom_manager, item_type)
        return jsonify(items)
    
    
    @app.route('/api/status')
    def api_status():
        """システム状況API"""
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM items")
        total_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bom_components")
        total_bom_components = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT item_type) FROM items")
        item_type_count = cursor.fetchone()[0]
        
        conn.close()
        
        status_info = {
            'environment': app.config['ENVIRONMENT'],
            'version': app.config['VERSION'],
            'database_path': app.config['DATABASE_PATH'],
            'total_items': total_items,
            'total_bom_components': total_bom_components,
            'item_type_count': item_type_count,
            'last_updated': datetime.now().isoformat()
        }
        
        # デプロイメント情報の追加
        status_info.update(create_deployment_info())
        
        return jsonify(status_info)
    
    
    # ステージング環境のみのルート
    if app.config.get('ENABLE_RESET_FUNCTION'):
        @app.route('/reset_staging', methods=['POST'])
        def reset_staging():
            """ステージング環境リセット"""
            try:
                if os.path.exists(app.config['DATABASE_PATH']):
                    os.remove(app.config['DATABASE_PATH'])
                
                init_database(app)
                flash('ステージング環境をリセットしました。', 'success')
                
            except Exception as e:
                flash(f'リセット中にエラーが発生しました: {str(e)}', 'error')
            
            return redirect(url_for('index'))


def get_items_by_type(bom_manager, item_type):
    """アイテムタイプ別の取得（安全版）"""
    try:
        if item_type == 'all':
            return bom_manager.get_all_items()
        else:
            return bom_manager.get_all_items_by_type(item_type)
    except Exception as e:
        print(f"Error getting items by type: {e}")
        return []


def filter_items_by_search(items, search_query):
    """検索フィルタリング"""
    filtered_items = []
    for item in items:
        searchable_text = ' '.join(filter(None, [
            item.get('item_name', ''),
            item.get('series_name', ''),
            item.get('yarn_composition', ''),
            item.get('color', '')
        ])).upper()
        
        if search_query.upper() in searchable_text:
            filtered_items.append(item)
    
    return filtered_items


def calculate_item_stats(all_items, item_types):
    """アイテム統計の計算"""
    stats = {}
    for item_type in item_types:
        stats[item_type] = len([item for item in all_items if item.get('item_type') == item_type])
    return stats


def count_oracle_items(items):
    """Oracle連携アイテム数のカウント"""
    return len([item for item in items if item.get('oracle_product_code')])


def collect_extended_attributes(form_data):
    """拡張属性の収集"""
    attributes = {}
    
    extended_fields = [
        'yarn_composition', 'series_name', 'color', 'knit_type'
    ]
    
    for field in extended_fields:
        value = form_data.get(field, '').strip()
        if value:
            attributes[field] = value
    
    # 数値フィールド
    numeric_fields = ['length_m']
    for field in numeric_fields:
        value = form_data.get(field, '').strip()
        if value:
            try:
                attributes[field] = int(value)
            except ValueError:
                pass  # 無効な値は無視
    
    return attributes


if __name__ == '__main__':
    # 環境変数から環境を取得
    environment = os.environ.get('FLASK_ENV', 'development')
    if environment == 'development':
        environment = 'development'
    
    # アプリケーションの作成
    app = create_app(environment)
    
    # 起動情報の表示
    print("=" * 60)
    print(f"{app.config['APP_NAME']} - {app.config['ENVIRONMENT']}")
    print("=" * 60)
    print(f"環境: {app.config['ENVIRONMENT']}")
    print(f"バージョン: {app.config['VERSION']}")
    print(f"データベース: {app.config['DATABASE_PATH']}")
    print(f"ポート: {app.config['PORT']}")
    print(f"ホスト: {app.config['HOST']}")
    print("-" * 60)
    print(f"アクセス: http://{app.config['HOST']}:{app.config['PORT']}")
    print("=" * 60)
    
    # アプリケーションの起動
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    ) 