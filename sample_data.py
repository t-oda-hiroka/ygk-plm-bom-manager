"""
釣り糸製造BOM管理システム サンプルデータ投入スクリプト

製造プロセス（原糸 -> PS -> ワインダー -> 製紐 -> センサー -> 染色 -> 後PS -> 巻き -> 仕上げ）
に基づいたサンプルデータを投入します。
"""

from bom_manager import BOMManager
import os


def create_sample_data():
    """サンプルデータを作成してデータベースに投入します"""
    
    # 既存のデータベースファイルを削除（クリーンスタート）
    if os.path.exists("bom_database.db"):
        os.remove("bom_database.db")
    
    # BOMマネージャーを初期化
    bom = BOMManager()
    
    print("サンプルデータを投入中...")
    
    # ========================================
    # レベル 7: 原糸 (Raw Yarn)
    # ========================================
    print("原糸データを投入中...")
    
    bom.add_item(
        item_id="RAW_EN_150D",
        item_name="EN 原糸 150デニール",
        item_type="Raw Yarn",
        unit_of_measure="KG",
        material_type="EN",
        denier=150,
        supplier="東洋紡"
    )
    
    bom.add_item(
        item_id="RAW_SK_120D",
        item_name="SK 原糸 120デニール", 
        item_type="Raw Yarn",
        unit_of_measure="KG",
        material_type="SK",
        denier=120,
        supplier="東洋紡"
    )
    
    # ========================================
    # レベル 6: 芯糸 (Core Yarn) - 購入品
    # ========================================
    print("芯糸データを投入中...")
    
    bom.add_item(
        item_id="CORE_PE_30D",
        item_name="PE芯糸 30デニール",
        item_type="Core Yarn",
        unit_of_measure="M",
        material_type="PE",
        denier=30,
        supplier="外部購入",
        is_purchased=True
    )
    
    # ========================================
    # レベル 5: PS糸 (PS Yarn)
    # ========================================
    print("PS糸データを投入中...")
    
    bom.add_item(
        item_id="PS_EN_100D_S",
        item_name="PS糸 ENPS(4.0) 100デニール S撚",
        item_type="PS Yarn", 
        unit_of_measure="M",
        material_type="EN",
        denier=100,
        ps_ratio=4.0,
        twist_type="S"
    )
    
    bom.add_item(
        item_id="PS_EN_100D_Z",
        item_name="PS糸 ENPS(4.0) 100デニール Z撚",
        item_type="PS Yarn",
        unit_of_measure="M", 
        material_type="EN",
        denier=100,
        ps_ratio=4.0,
        twist_type="Z"
    )
    
    bom.add_item(
        item_id="PS_SK_80D_S",
        item_name="PS糸 SKPS(3.8) 80デニール S撚",
        item_type="PS Yarn",
        unit_of_measure="M",
        material_type="SK", 
        denier=80,
        ps_ratio=3.8,
        twist_type="S"
    )
    
    # ========================================
    # レベル 4: 製紐糸 (Braided Yarn)
    # ========================================
    print("製紐糸データを投入中...")
    
    bom.add_item(
        item_id="BRAID_EN_X8_2_4",
        item_name="製紐糸 ENPS(4.0) BR-1.8 100d x8 2.4号",
        item_type="Braided Yarn",
        unit_of_measure="M",
        material_type="EN",
        braid_structure="x8",
        has_core=True,
        br_value=1.8,
        size="2.4号"
    )
    
    # ========================================
    # レベル 3: 染色糸 (Dyed Yarn)
    # ========================================
    print("染色糸データを投入中...")
    
    bom.add_item(
        item_id="DYED_EN_X8_MULTI",
        item_name="染色糸 ENPS(4.0) BR-1.8 100d x8 2.4号 マルチカラー",
        item_type="Dyed Yarn",
        unit_of_measure="M",
        material_type="EN",
        braid_structure="x8", 
        has_core=True,
        color="マルチ",
        br_value=1.8,
        size="2.4号"
    )
    
    # ========================================
    # レベル 2: 成形品 (Molded Parts)
    # ========================================
    print("成形品データを投入中...")
    
    bom.add_item(
        item_id="SPOOL_100M",
        item_name="100m用スプール",
        item_type="Molded Part",
        unit_of_measure="個",
        capacity_m=100,
        material="プラスチック"
    )
    
    # ========================================
    # レベル 2: 巻き取られた糸 (Wound Product)
    # ========================================
    print("巻き取られた糸データを投入中...")
    
    bom.add_item(
        item_id="WOUND_EN_X8_100M",
        item_name="巻き糸 ENPS(4.0) BR-1.8 100d x8 2.4号 マルチ 100m",
        item_type="Wound Product",
        unit_of_measure="個",
        material_type="EN",
        braid_structure="x8",
        has_core=True,
        color="マルチ",
        length_m=100,
        size="2.4号"
    )
    
    # ========================================
    # レベル 1: 梱包資材 (Packaging Materials)
    # ========================================
    print("梱包資材データを投入中...")
    
    bom.add_item(
        item_id="PKG_CARTON_WXP1",
        item_name="WXP1専用台紙",
        item_type="Packaging Material",
        unit_of_measure="枚",
        package_type="台紙"
    )
    
    bom.add_item(
        item_id="PKG_BOX_STANDARD",
        item_name="標準出荷ダンボール",
        item_type="Packaging Material", 
        unit_of_measure="個",
        package_type="ダンボール"
    )
    
    bom.add_item(
        item_id="PKG_SEAL_SET",
        item_name="シール類一式",
        item_type="Packaging Material",
        unit_of_measure="セット",
        package_type="シール"
    )
    
    # ========================================
    # レベル 0: 完成品 (Finished Product)
    # ========================================
    print("完成品データを投入中...")
    
    bom.add_item(
        item_id="FIN_WXP1_X8_MULTI_8_100M",
        item_name="YGK ロンフォート オッズポート WXP1 X8 マルチ 8号 100m連結",
        item_type="Finished Product",
        unit_of_measure="個",
        product_line="ロンフォート",
        series="オッズポート", 
        model="WXP1",
        braid_structure="X8",
        color="マルチ",
        size="8号",
        length_m=100
    )
    
    # ========================================
    # BOM構成の設定
    # ========================================
    print("BOM構成を設定中...")
    
    # 原糸 -> PS糸
    bom.add_bom_component("PS_EN_100D_S", "RAW_EN_150D", 0.8, "Main Material")  # PS加工で重量減少
    bom.add_bom_component("PS_EN_100D_Z", "RAW_EN_150D", 0.8, "Main Material")
    bom.add_bom_component("PS_SK_80D_S", "RAW_SK_120D", 0.7, "Main Material")
    
    # PS糸 + 芯糸 -> 製紐糸（8本編み + 芯糸）
    bom.add_bom_component("BRAID_EN_X8_2_4", "PS_EN_100D_S", 120.0, "Main Braid Thread")  # 100m製紐糸を作るのに120m必要
    bom.add_bom_component("BRAID_EN_X8_2_4", "PS_EN_100D_Z", 120.0, "Main Braid Thread")
    bom.add_bom_component("BRAID_EN_X8_2_4", "CORE_PE_30D", 105.0, "Core Thread")  # 芯糸
    
    # 製紐糸 -> 染色糸
    bom.add_bom_component("DYED_EN_X8_MULTI", "BRAID_EN_X8_2_4", 1.0, "Main Material")
    
    # 染色糸 + スプール -> 巻き取られた糸
    bom.add_bom_component("WOUND_EN_X8_100M", "DYED_EN_X8_MULTI", 100.0, "Main Material")  # 100m
    bom.add_bom_component("WOUND_EN_X8_100M", "SPOOL_100M", 1.0, "Container")
    
    # 巻き取られた糸 + 梱包資材 -> 完成品
    bom.add_bom_component("FIN_WXP1_X8_MULTI_8_100M", "WOUND_EN_X8_100M", 1.0, "Main Material")
    bom.add_bom_component("FIN_WXP1_X8_MULTI_8_100M", "PKG_CARTON_WXP1", 1.0, "Packaging")
    bom.add_bom_component("FIN_WXP1_X8_MULTI_8_100M", "PKG_BOX_STANDARD", 1.0, "Packaging") 
    bom.add_bom_component("FIN_WXP1_X8_MULTI_8_100M", "PKG_SEAL_SET", 1.0, "Packaging")
    
    print("サンプルデータの投入が完了しました！")
    
    return bom


def demo_queries(bom: BOMManager):
    """デモクエリを実行してデータを確認します"""
    
    print("\n" + "="*60)
    print("BOM管理システム デモンストレーション")
    print("="*60)
    
    # 1. 完成品の直下構成部品を表示
    print("\n1. 完成品の直下構成部品:")
    print("-" * 40)
    components = bom.get_direct_components("FIN_WXP1_X8_MULTI_8_100M")
    for comp in components:
        print(f"  - {comp['item_name']}: {comp['quantity']} {comp['unit_of_measure']} ({comp['usage_type']})")
    
    # 2. 多段階BOM構造をツリー表示
    print("\n2. 多段階BOM構造 (完成品):")
    print("-" * 40)
    bom.print_bom_tree("FIN_WXP1_X8_MULTI_8_100M")
    
    # 3. 製紐糸の構成部品を表示
    print("\n3. 製紐糸の直下構成部品:")
    print("-" * 40)
    components = bom.get_direct_components("BRAID_EN_X8_2_4")
    for comp in components:
        print(f"  - {comp['item_name']}: {comp['quantity']} {comp['unit_of_measure']} ({comp['usage_type']})")
    
    # 4. アイテムタイプ別一覧
    print("\n4. PS糸一覧:")
    print("-" * 40)
    ps_yarns = bom.get_all_items_by_type("PS Yarn")
    for item in ps_yarns:
        print(f"  - {item['item_name']} ({item['item_id']})")
        print(f"    材質: {item['material_type']}, デニール: {item['denier']}, PS値: {item['ps_ratio']}, 撚り: {item['twist_type']}")
    
    # 5. 原糸一覧
    print("\n5. 原糸一覧:")
    print("-" * 40)
    raw_yarns = bom.get_all_items_by_type("Raw Yarn")
    for item in raw_yarns:
        print(f"  - {item['item_name']} ({item['item_id']})")
        print(f"    材質: {item['material_type']}, デニール: {item['denier']}")


if __name__ == "__main__":
    # サンプルデータを作成
    bom_manager = create_sample_data()
    
    # デモクエリを実行
    demo_queries(bom_manager) 