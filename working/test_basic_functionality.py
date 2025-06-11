"""
釣り糸製造BOM管理システム 基本機能テストスクリプト

このスクリプトは要件に基づいた基本機能のテストを行います。
"""

from bom_manager import BOMManager
import os


def test_basic_functionality():
    """基本機能のテストを実行します"""
    
    print("="*60)
    print("釣り糸製造BOM管理システム 基本機能テスト")
    print("="*60)
    
    # テスト用データベースファイル
    test_db = "test_bom.db"
    
    # 既存のテストファイルを削除
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # BOMマネージャーを初期化
    bom = BOMManager(test_db)
    
    print("\n1. アイテム追加テスト")
    print("-" * 30)
    
    # 原糸の追加
    success1 = bom.add_item(
        item_id="TEST_RAW_EN",
        item_name="テスト用EN原糸",
        item_type="Raw Yarn",
        unit_of_measure="KG",
        material_type="EN",
        denier=150
    )
    print(f"原糸追加: {'成功' if success1 else '失敗'}")
    
    # PS糸の追加
    success2 = bom.add_item(
        item_id="TEST_PS_EN",
        item_name="テスト用PS糸",
        item_type="PS Yarn",
        unit_of_measure="M",
        material_type="EN",
        denier=100,
        ps_ratio=4.0,
        twist_type="S"
    )
    print(f"PS糸追加: {'成功' if success2 else '失敗'}")
    
    print("\n2. BOM構成追加テスト")
    print("-" * 30)
    
    # BOM構成の追加
    success3 = bom.add_bom_component(
        parent_item_id="TEST_PS_EN",
        component_item_id="TEST_RAW_EN",
        quantity=0.8,
        usage_type="Main Material"
    )
    print(f"BOM構成追加: {'成功' if success3 else '失敗'}")
    
    print("\n3. アイテム取得テスト")
    print("-" * 30)
    
    # アイテム情報の取得
    raw_yarn = bom.get_item("TEST_RAW_EN")
    if raw_yarn:
        print(f"原糸取得成功:")
        print(f"  - ID: {raw_yarn['item_id']}")
        print(f"  - 名前: {raw_yarn['item_name']}")
        print(f"  - タイプ: {raw_yarn['item_type']}")
        print(f"  - 材質: {raw_yarn['material_type']}")
        print(f"  - デニール: {raw_yarn['denier']}")
    else:
        print("原糸取得失敗")
    
    ps_yarn = bom.get_item("TEST_PS_EN")
    if ps_yarn:
        print(f"\nPS糸取得成功:")
        print(f"  - ID: {ps_yarn['item_id']}")
        print(f"  - 名前: {ps_yarn['item_name']}")
        print(f"  - タイプ: {ps_yarn['item_type']}")
        print(f"  - 材質: {ps_yarn['material_type']}")
        print(f"  - PS値: {ps_yarn['ps_ratio']}")
        print(f"  - 撚り: {ps_yarn['twist_type']}")
    else:
        print("PS糸取得失敗")
    
    print("\n4. 直下構成部品取得テスト")
    print("-" * 30)
    
    # PS糸の構成部品を取得
    components = bom.get_direct_components("TEST_PS_EN")
    if components:
        print(f"PS糸の構成部品 ({len(components)}件):")
        for comp in components:
            print(f"  - {comp['item_name']}: {comp['quantity']} {comp['unit_of_measure']} ({comp['usage_type']})")
    else:
        print("構成部品が見つかりませんでした")
    
    print("\n5. タイプ別アイテム一覧テスト")
    print("-" * 30)
    
    # Raw Yarnタイプのアイテム一覧
    raw_yarns = bom.get_all_items_by_type("Raw Yarn")
    print(f"原糸一覧 ({len(raw_yarns)}件):")
    for item in raw_yarns:
        print(f"  - {item['item_name']} ({item['item_id']})")
    
    # PS Yarnタイプのアイテム一覧
    ps_yarns = bom.get_all_items_by_type("PS Yarn")
    print(f"\nPS糸一覧 ({len(ps_yarns)}件):")
    for item in ps_yarns:
        print(f"  - {item['item_name']} ({item['item_id']})")
    
    print("\n6. 多段階BOM展開テスト")
    print("-" * 30)
    
    # 多段階BOM構造の取得
    bom_tree = bom.get_multi_level_bom("TEST_PS_EN")
    if bom_tree and bom_tree.get('item'):
        print("多段階BOM構造:")
        bom.print_bom_tree("TEST_PS_EN")
    else:
        print("BOM構造の取得に失敗しました")
    
    print("\n" + "="*60)
    print("基本機能テスト完了")
    print("="*60)
    
    # テストファイルを削除
    if os.path.exists(test_db):
        os.remove(test_db)
        print(f"\nテストファイル '{test_db}' を削除しました")


if __name__ == "__main__":
    test_basic_functionality() 