"""
釣り糸製造BOM管理システム 統合アプリケーション
環境設定に基づく自動切り替え対応
Oracle DB直接参照モード対応（リードオンリー）
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from bom_manager import BOMManager
from oracle_bom_manager import OracleBOMManager
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
    
    # Oracle直接参照モードの判定
    oracle_direct_mode = app.config.get('ORACLE_DIRECT_MODE', False)
    
    if oracle_direct_mode:
        # Oracle直接参照BOM管理システムを使用（リードオンリー）
        bom_manager = OracleBOMManager(fallback_db_path=app.config['DATABASE_PATH'])
        print(f"🌐 Oracle直接参照モード: リードオンリー動作")
    else:
        # 通常のBOM管理システムを使用
        bom_manager = BOMManager(app.config['DATABASE_PATH'])
        print(f"💾 通常モード: SQLite DB使用")
    
    # データベース初期化（通常モードのみ）
    if not oracle_direct_mode:
        init_database(app)
    
    # ルートの登録
    register_routes(app, bom_manager, oracle_direct_mode)
    
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


def register_routes(app, bom_manager, oracle_direct_mode):
    """ルートの登録"""
    
    @app.route('/')
    def dashboard():
        """ダッシュボード（メインページ）"""
        # 統計データを取得
        all_items = get_items_by_type(bom_manager, 'all')
        all_lots = bom_manager.get_all_lots(limit=1000)
        
        # 基本統計
        total_items_count = len(all_items)
        oracle_items_count = count_oracle_items(all_items)
        total_lots_count = len(all_lots)
        active_lots_count = len([lot for lot in all_lots if lot['lot_status'] == 'active'])
        
        # アイテムタイプ別統計
        item_type_stats = calculate_item_stats(all_items, app.config['ITEM_TYPES'])
        
        # BOM構成数を取得
        total_bom_components = 0
        try:
            with sqlite3.connect(bom_manager.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM bom_components")
                total_bom_components = cursor.fetchone()[0]
        except:
            pass
        
        # 系統図関係数を取得
        total_genealogy_relations = 0
        try:
            with sqlite3.connect(bom_manager.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM lot_genealogy")
                total_genealogy_relations = cursor.fetchone()[0]
        except:
            pass
        
        # テンプレート変数
        template_vars = {
            'total_items_count': total_items_count,
            'oracle_items_count': oracle_items_count,
            'total_lots_count': total_lots_count,
            'active_lots_count': active_lots_count,
            'total_bom_components': total_bom_components,
            'total_genealogy_relations': total_genealogy_relations,
            'item_type_stats': item_type_stats,
            'environment': app.config['ENVIRONMENT'],
            'version': app.config['VERSION'],
        }
        
        # 環境固有の変数
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
        
        return render_template('dashboard.html', **template_vars)

    @app.route('/items')
    def items_list():
        """アイテム一覧ページ"""
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
        
        # パンくず作成
        breadcrumbs = create_breadcrumbs(
            get_home_breadcrumb(),
            get_items_list_breadcrumb()
        )
        
        # 環境に応じたテンプレート変数
        template_vars = {
            'items': items,
            'item_types': app.config['ITEM_TYPES'],
            'current_filter': item_type_filter,
            'search_query': search_query,
            'oracle_items_count': oracle_items_count,
            'total_items_count': len(items),
            'item_type_stats': item_type_stats,
            'breadcrumbs': breadcrumbs,
            'environment': app.config['ENVIRONMENT'],
            'version': app.config['VERSION'],
        }
        
        # 環境固有の変数
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
        
        return render_template('items_list.html', **template_vars)
    
    
    @app.route('/item_details/<item_id>')
    def item_details(item_id):
        """アイテム詳細ページ"""
        item = bom_manager.get_item(item_id)
        if not item:
            flash(f'アイテム "{item_id}" が見つかりませんでした。', 'error')
            return redirect(url_for('items_list'))
        
        components = bom_manager.get_direct_components(item_id)
        
        # このアイテムに関連するロット一覧を取得
        related_lots = bom_manager.get_lots_by_item(item_id)
        
        # ロット状態別の統計
        lot_stats = {
            'total': len(related_lots),
            'active': len([lot for lot in related_lots if lot['lot_status'] == 'active']),
            'consumed': len([lot for lot in related_lots if lot['lot_status'] == 'consumed']),
            'completed': len([lot for lot in related_lots if lot['lot_status'] == 'completed'])
        }
        
        # パンくず作成
        breadcrumbs = create_breadcrumbs(
            get_home_breadcrumb(),
            get_items_list_breadcrumb(),
            get_item_breadcrumb(item)
        )
        
        template_vars = {
            'item': item,
            'components': components,
            'related_lots': related_lots,
            'lot_stats': lot_stats,
            'breadcrumbs': breadcrumbs,
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
            return redirect(url_for('items_list'))
        
        bom_structure = bom_manager.get_multi_level_bom(item_id)
        
        # パンくず作成
        breadcrumbs = create_breadcrumbs(
            get_home_breadcrumb(),
            get_items_list_breadcrumb(),
            get_item_breadcrumb(item),
            {'text': 'BOM構造', 'url': None, 'icon': 'fas fa-project-diagram'}
        )
        
        template_vars = {
            'item': item,
            'bom_structure': bom_structure,
            'breadcrumbs': breadcrumbs,
            'environment': app.config['ENVIRONMENT'],
        }
        
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
            
        return render_template('bom_tree.html', **template_vars)
    
    
    @app.route('/items/<item_id>/lots')
    def item_lots(item_id):
        """アイテム専用ロット管理画面"""
        item = bom_manager.get_item(item_id)
        if not item:
            flash(f'アイテム "{item_id}" が見つかりませんでした。', 'error')
            return redirect(url_for('items_list'))
        
        # フィルタリング用のパラメータを取得
        status_filter = request.args.get('status', 'all')
        process_filter = request.args.get('process', 'all')
        search_query = request.args.get('search', '').strip()
        
        # このアイテムに関連するロット一覧を取得
        lots = bom_manager.get_lots_by_item(item_id, status=None)  # 全ステータス取得
        
        # フィルタリング適用
        if status_filter != 'all':
            lots = [lot for lot in lots if lot['lot_status'] == status_filter]
        
        if process_filter != 'all':
            lots = [lot for lot in lots if lot['process_code'] == process_filter]
        
        if search_query:
            lots = [lot for lot in lots if 
                   search_query.lower() in lot['lot_id'].lower() or
                   search_query.lower() in lot.get('location', '').lower() or
                   search_query.lower() in lot.get('operator_id', '').lower()]
        
        # 統計情報計算
        all_lots = bom_manager.get_lots_by_item(item_id, status=None)
        lot_stats = {
            'total': len(all_lots),
            'active': len([lot for lot in all_lots if lot['lot_status'] == 'active']),
            'consumed': len([lot for lot in all_lots if lot['lot_status'] == 'consumed']),
            'completed': len([lot for lot in all_lots if lot['lot_status'] == 'completed']),
            'pending': len([lot for lot in all_lots if lot['lot_status'] == 'pending'])
        }
        
        # 工程別統計
        process_stats = {}
        for lot in all_lots:
            process = lot['process_code']
            if process not in process_stats:
                process_stats[process] = {'count': 0, 'process_name': lot['process_name']}
            process_stats[process]['count'] += 1
        
        # 品質グレード別統計
        quality_stats = {}
        for lot in all_lots:
            grade = lot.get('grade_name', '未設定')
            quality_stats[grade] = quality_stats.get(grade, 0) + 1
        
        # 数量統計
        total_quantity = sum([lot['current_quantity'] for lot in all_lots if lot['lot_status'] == 'active'])
        avg_quantity = total_quantity / len(all_lots) if len(all_lots) > 0 else 0
        
        # フィルタ用選択肢取得
        processes_seen = set()
        processes = []
        for lot in all_lots:
            process_code = lot['process_code']
            if process_code not in processes_seen:
                processes.append({'code': process_code, 'name': lot['process_name']})
                processes_seen.add(process_code)
        processes = sorted(processes, key=lambda x: x['code'])
        
        # パンくず作成
        breadcrumbs = create_breadcrumbs(
            get_home_breadcrumb(),
            get_items_list_breadcrumb(),
            get_item_breadcrumb(item),
            {'text': 'ロット管理', 'url': None, 'icon': 'fas fa-layer-group'}
        )
        
        template_vars = {
            'item': item,
            'lots': lots,
            'lot_stats': lot_stats,
            'process_stats': process_stats,
            'quality_stats': quality_stats,
            'total_quantity': total_quantity,
            'avg_quantity': avg_quantity,
            'processes': processes,
            'breadcrumbs': breadcrumbs,
            'current_filters': {
                'status': status_filter,
                'process': process_filter,
                'search': search_query
            },
            'environment': app.config['ENVIRONMENT'],
        }
        
        if app.config.get('SHOW_ENVIRONMENT_BANNER'):
            template_vars['is_staging'] = True
            
        return render_template('items/lots.html', **template_vars)
    
    
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
                    return redirect(url_for('items_list'))
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
        """APIステータス確認"""
        try:
            items = bom_manager.get_all_items()
            return jsonify({
                'status': 'ok',
                'environment': app.config['ENVIRONMENT'],
                'database': app.config['DATABASE_PATH'],
                'items_count': len(items),
                'sample_data_enabled': app.config.get('ENABLE_SAMPLE_DATA', False)
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # =============================================================================
    # ロット管理ルート
    # =============================================================================
    
    @app.route('/lots')
    def lots_list():
        """ロット一覧画面"""
        # フィルタリング用のパラメータを取得
        item_type_filter = request.args.get('item_type', 'all')
        status_filter = request.args.get('status', 'all')
        process_filter = request.args.get('process', 'all')
        search_query = request.args.get('search', '').strip()
        
        # ロット一覧取得
        lots = bom_manager.get_all_lots(limit=200)
        
        # フィルタリング
        if item_type_filter != 'all':
            lots = [lot for lot in lots if lot['item_type'] == item_type_filter]
        
        if status_filter != 'all':
            lots = [lot for lot in lots if lot['lot_status'] == status_filter]
        
        if process_filter != 'all':
            lots = [lot for lot in lots if lot['process_code'] == process_filter]
        
        if search_query:
            lots = [lot for lot in lots if 
                   search_query.lower() in lot['lot_id'].lower() or
                   search_query.lower() in lot['item_name'].lower() or
                   search_query.lower() in lot.get('lot_name', '').lower()]
        
        # 統計情報計算
        total_lots = len(lots)
        active_lots = len([lot for lot in lots if lot['lot_status'] == 'active'])
        consumed_lots = len([lot for lot in lots if lot['lot_status'] == 'consumed'])
        
        # 工程別統計
        process_stats = {}
        for lot in lots:
            process = lot['process_code']
            if process not in process_stats:
                process_stats[process] = {'count': 0, 'process_name': lot['process_name']}
            process_stats[process]['count'] += 1
        
        # フィルタ用選択肢取得
        item_types = list(set([lot['item_type'] for lot in lots]))
        
        # プロセス一覧の重複削除（辞書をsetに入れられないため別の方法で実装）
        processes_seen = set()
        processes = []
        for lot in lots:
            process_code = lot['process_code']
            if process_code not in processes_seen:
                processes.append({'code': process_code, 'name': lot['process_name']})
                processes_seen.add(process_code)
        processes = sorted(processes, key=lambda x: x['code'])
        
        # パンくず作成
        breadcrumbs = create_breadcrumbs(
            get_home_breadcrumb(),
            get_lots_list_breadcrumb()
        )
        
        return render_template('lots/list.html',
                             lots=lots,
                             total_lots=total_lots,
                             active_lots=active_lots,
                             consumed_lots=consumed_lots,
                             process_stats=process_stats,
                             item_types=sorted(item_types),
                             processes=processes,
                             breadcrumbs=breadcrumbs,
                             current_filters={
                                 'item_type': item_type_filter,
                                 'status': status_filter,
                                 'process': process_filter,
                                 'search': search_query
                             })
    
    @app.route('/lots/create', methods=['GET', 'POST'])
    def create_lot():
        """ロット作成画面"""
        if request.method == 'POST':
            try:
                # フォームデータ取得
                item_id = request.form['item_id']
                process_code = request.form['process_code']
                planned_quantity = float(request.form['planned_quantity'])
                production_date = request.form.get('production_date')
                quality_grade = request.form.get('quality_grade', 'A')
                
                # オプション属性
                kwargs = {}
                if request.form.get('equipment_id'):
                    kwargs['equipment_id'] = request.form['equipment_id']
                if request.form.get('operator_id'):
                    kwargs['operator_id'] = request.form['operator_id']
                if request.form.get('location'):
                    kwargs['location'] = request.form['location']
                if request.form.get('measured_length'):
                    kwargs['measured_length'] = float(request.form['measured_length'])
                if request.form.get('measured_weight'):
                    kwargs['measured_weight'] = float(request.form['measured_weight'])
                if request.form.get('measurement_notes'):
                    kwargs['measurement_notes'] = request.form['measurement_notes']
                
                # ロット作成
                lot_id = bom_manager.create_lot(
                    item_id=item_id,
                    process_code=process_code,
                    planned_quantity=planned_quantity,
                    production_date=production_date,
                    quality_grade=quality_grade,
                    **kwargs
                )
                
                flash(f'ロット {lot_id} を作成しました。', 'success')
                return redirect(url_for('lot_details', lot_id=lot_id))
                
            except Exception as e:
                flash(f'ロット作成エラー: {str(e)}', 'error')
        
        # GET: フォーム表示
        items = bom_manager.get_all_items()
        
        # 工程ステップ取得
        with sqlite3.connect(bom_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM process_steps ORDER BY process_level")
            processes = [dict(row) for row in cursor.fetchall()]
        
        # 品質グレード取得
        with sqlite3.connect(bom_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM quality_grades ORDER BY grade_code")
            quality_grades = [dict(row) for row in cursor.fetchall()]
        
        return render_template('lots/create.html',
                             items=items,
                             processes=processes,
                             quality_grades=quality_grades)
    
    @app.route('/lots/<lot_id>')
    def lot_details(lot_id):
        """ロット詳細画面"""
        lot = bom_manager.get_lot(lot_id)
        if not lot:
            flash(f'ロット {lot_id} が見つかりません。', 'error')
            return redirect(url_for('lots_list'))
        
        # 在庫移動履歴取得
        with sqlite3.connect(bom_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM inventory_transactions 
                WHERE lot_id = ? 
                ORDER BY transaction_date DESC
            """, (lot_id,))
            transactions = [dict(row) for row in cursor.fetchall()]
        
        # 系統図情報取得（親として）
        with sqlite3.connect(bom_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT lg.*, l.lot_id as child_lot, i.item_name as child_item_name
                FROM lot_genealogy lg
                JOIN lots l ON lg.child_lot_id = l.lot_id
                JOIN items i ON l.item_id = i.item_id
                WHERE lg.parent_lot_id = ?
                ORDER BY lg.consumption_date DESC
            """, (lot_id,))
            consumed_materials = [dict(row) for row in cursor.fetchall()]
        
        # 系統図情報取得（子として）
        with sqlite3.connect(bom_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT lg.*, l.lot_id as parent_lot, i.item_name as parent_item_name
                FROM lot_genealogy lg
                JOIN lots l ON lg.parent_lot_id = l.lot_id
                JOIN items i ON l.item_id = i.item_id
                WHERE lg.child_lot_id = ?
                ORDER BY lg.consumption_date DESC
            """, (lot_id,))
            used_in_lots = [dict(row) for row in cursor.fetchall()]
        
        # パンくず作成
        breadcrumbs = create_breadcrumbs(
            get_home_breadcrumb(),
            get_lots_list_breadcrumb(),
            get_lot_breadcrumb(lot)
        )
        
        return render_template('lots/details.html',
                             lot=lot,
                             transactions=transactions,
                             consumed_materials=consumed_materials,
                             used_in_lots=used_in_lots,
                             breadcrumbs=breadcrumbs)
    
    @app.route('/lots/<lot_id>/genealogy')
    def lot_genealogy(lot_id):
        """ロット系統図画面"""
        lot = bom_manager.get_lot(lot_id)
        if not lot:
            flash(f'ロット {lot_id} が見つかりません。', 'error')
            return redirect(url_for('lots_list'))
        
        # 前方・後方トレース取得
        forward_tree = bom_manager.get_lot_genealogy_tree(lot_id, 'forward')
        backward_tree = bom_manager.get_lot_genealogy_tree(lot_id, 'backward')
        
        # パンくず作成
        breadcrumbs = create_breadcrumbs(
            get_home_breadcrumb(),
            get_lots_list_breadcrumb(),
            get_lot_breadcrumb(lot),
            {'text': '系統図', 'url': None, 'icon': 'fas fa-sitemap'}
        )
        
        return render_template('lots/genealogy.html',
                             lot=lot,
                             forward_tree=forward_tree,
                             backward_tree=backward_tree,
                             breadcrumbs=breadcrumbs)
    
    @app.route('/lots/<lot_id>/consume', methods=['GET', 'POST'])
    def consume_lot(lot_id):
        """ロット消費（投入）画面"""
        lot = bom_manager.get_lot(lot_id)
        if not lot:
            flash(f'ロット {lot_id} が見つかりません。', 'error')
            return redirect(url_for('lots_list'))
        
        if request.method == 'POST':
            try:
                parent_lot_id = request.form['parent_lot_id']
                consumed_quantity = float(request.form['consumed_quantity'])
                usage_type = request.form.get('usage_type', 'Main Material')
                notes = request.form.get('notes', '')
                
                # ロット系統図追加
                success = bom_manager.add_lot_genealogy(
                    parent_lot_id=parent_lot_id,
                    child_lot_id=lot_id,
                    consumed_quantity=consumed_quantity,
                    usage_type=usage_type,
                    notes=notes
                )
                
                if success:
                    flash(f'ロット {lot_id} を {parent_lot_id} に投入しました。', 'success')
                    return redirect(url_for('lot_details', lot_id=parent_lot_id))
                else:
                    flash('ロット投入に失敗しました。', 'error')
                    
            except Exception as e:
                flash(f'ロット投入エラー: {str(e)}', 'error')
        
        # 投入可能な親ロット候補を取得
        # 現在のロットより後の工程のアクティブロットを取得
        with sqlite3.connect(bom_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT l.*, i.item_name, p.process_name, p.process_level
                FROM lots l
                JOIN items i ON l.item_id = i.item_id
                JOIN process_steps p ON l.process_code = p.process_code
                JOIN process_steps current_p ON current_p.process_code = ?
                WHERE l.lot_status = 'active' 
                  AND p.process_level > current_p.process_level
                  AND l.current_quantity > 0
                ORDER BY p.process_level, l.production_date DESC
            """, (lot['process_code'],))
            candidate_lots = [dict(row) for row in cursor.fetchall()]
        
        return render_template('lots/consume.html',
                             lot=lot,
                             candidate_lots=candidate_lots)
    
    # =============================================================================
    # 管理・デバッグ機能（既存コード）
    # =============================================================================
    
    # 環境別のデバッグ機能を追加
    if app.config['ENVIRONMENT'] in ['DEVELOPMENT', 'STAGING']:
        @app.route('/reset_staging', methods=['POST'])
        def reset_staging():
            """ステージング環境のリセット（開発用）"""
            if app.config['ENVIRONMENT'] != 'STAGING':
                return jsonify({'error': 'この機能はステージング環境でのみ利用可能です'}), 403
            
            try:
                # データベースを削除して再作成
                if os.path.exists(app.config['DATABASE_PATH']):
                    os.remove(app.config['DATABASE_PATH'])
                
                init_database(app)
                return jsonify({'message': 'ステージング環境をリセットしました'})
            except Exception as e:
                return jsonify({'error': f'リセット失敗: {str(e)}'}), 500


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


def create_breadcrumbs(*breadcrumbs_data):
    """パンくずナビゲーションを作成するヘルパー関数
    
    Args:
        *breadcrumbs_data: (text, url, icon) のタプルまたは辞書のリスト
    
    Returns:
        list: パンくず情報のリスト
    """
    breadcrumbs = []
    
    for breadcrumb in breadcrumbs_data:
        if isinstance(breadcrumb, tuple):
            if len(breadcrumb) == 2:
                text, url = breadcrumb
                icon = None
            elif len(breadcrumb) == 3:
                text, url, icon = breadcrumb
            else:
                continue
            
            breadcrumbs.append({
                'text': text,
                'url': url,
                'icon': icon
            })
        elif isinstance(breadcrumb, dict):
            breadcrumbs.append(breadcrumb)
    
    return breadcrumbs


def get_home_breadcrumb():
    """ホームのパンくず"""
    return {'text': 'ホーム', 'url': url_for('dashboard'), 'icon': 'fas fa-home'}


def get_items_list_breadcrumb():
    """アイテム一覧のパンくず"""
    return {'text': 'アイテム一覧', 'url': url_for('items_list'), 'icon': 'fas fa-list'}


def get_item_breadcrumb(item):
    """アイテム詳細のパンくず"""
    display_name = item['item_name']
    if len(display_name) > 30:
        display_name = display_name[:27] + '...'
    
    return {'text': display_name, 'url': url_for('item_details', item_id=item['item_id']), 'icon': 'fas fa-cube'}


def get_lots_list_breadcrumb():
    """ロット一覧のパンくず"""
    return {'text': 'ロット一覧', 'url': url_for('lots_list'), 'icon': 'fas fa-layer-group'}


def get_lot_breadcrumb(lot):
    """ロット詳細のパンくず"""
    return {'text': lot['lot_id'], 'url': url_for('lot_details', lot_id=lot['lot_id']), 'icon': 'fas fa-box'}


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