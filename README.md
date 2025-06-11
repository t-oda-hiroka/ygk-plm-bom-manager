# 釣り糸製造BOM管理システム プロトタイプ

このプロジェクトは、釣り糸の製造プロセスにおけるBOM（部品表）を管理するためのプロトタイプシステムです。

## 概要

製造プロセス（原糸 → PS → ワインダー → 製紐 → センサー → 染色 → 後PS → 巻き → 仕上げ）における糸の名称や状態変化を追跡し、各中間生成物および最終製品の構成部品を管理します。

## 特徴

- **多段階BOM管理**: 原糸から完成品まで最大7階層のBOM構造を表現
- **柔軟な属性管理**: 材質、デニール、PS値、編み構造、色など糸特有の属性を管理
- **用途別分類**: 主材料、編み糸、芯糸、梱包材などの用途別分類
- **SQLiteベース**: 軽量でファイルベースのデータベース
- **Pythonインターフェース**: 直感的なPython APIを提供

## データ構造

### アイテムタイプ
- **原糸**: 東洋紡などから仕入れる基本材料
- **PS糸**: PS（延伸）加工を施した糸
- **製紐糸**: 複数のPS糸を編み込んだ糸
- **染色糸**: 染色工程を経た糸
- **後PS糸**: 染色後にPS加工を施した糸
- **巻き取り糸**: スプールに巻き取られた糸
- **完成品**: 最終的な製品
- **芯糸**: 製紐の芯として使用する糸
- **梱包資材**: 台紙、ダンボール、シール等
- **成形品**: スプール等の容器

### BOM階層例
```
完成品: YGK ロンフォート オッズポート WXP1 X8 マルチ 8号 100m連結
├─ 巻き糸 ENPS(4.0) BR-1.8 100d x8 2.4号 マルチ 100m
│  ├─ 染色糸 ENPS(4.0) BR-1.8 100d x8 2.4号 マルチカラー
│  │  └─ 製紐糸 ENPS(4.0) BR-1.8 100d x8 2.4号
│  │     ├─ PS糸 ENPS(4.0) 100デニール S撚
│  │     │  └─ EN 原糸 150デニール
│  │     ├─ PS糸 ENPS(4.0) 100デニール Z撚
│  │     │  └─ EN 原糸 150デニール
│  │     └─ PE芯糸 30デニール
│  └─ 100m用スプール
├─ WXP1専用台紙
├─ 標準出荷ダンボール
└─ シール類一式
```

## ファイル構成

- `schema.sql`: データベーススキーマ定義
- `bom_manager.py`: BOM管理システムのメインクラス
- `app.py`: Flask Webアプリケーション
- `sample_data.py`: サンプルデータ投入スクリプト
- `test_basic_functionality.py`: 基本機能テストスクリプト
- `requirements.txt`: 依存関係（Flask等）
- `README.md`: このファイル
- `templates/`: HTMLテンプレートファイル
  - `base.html`: ベーステンプレート
  - `index.html`: アイテム一覧ページ
  - `add_item.html`: アイテム追加フォーム
  - `bom_tree.html`: BOM構造表示ページ
  - `add_bom.html`: BOM構成追加フォーム
  - `item_details.html`: アイテム詳細ページ

## 実行手順

### 1. 環境要件
- Python 3.7以上
- 標準ライブラリのみ使用（追加インストール不要）

### 2. サンプルデータの投入と動作確認

```bash
# サンプルデータを投入し、デモンストレーションを実行
python sample_data.py
```

### 3. Webアプリケーションの起動

```bash
# 依存関係をインストール
pip install Flask

# Webアプリケーションを起動
python app.py
```

アプリケーションが起動したら、ブラウザで以下のURLにアクセスしてください：

**http://localhost:5001**

#### Webアプリケーションの機能

- **アイテム一覧**: 登録されたアイテムの一覧表示とフィルタリング
  - **ソート機能**: 列ヘッダークリックで昇順・降順ソート
  - **データタイプ対応**: 文字列と数値の適切なソート処理
- **アイテム追加**: 新しいアイテムの登録フォーム
- **BOM構成追加**: アイテム間のBOM関係を設定
- **BOM構造表示**: 多段階BOM構造の視覚的なツリー表示
- **アイテム詳細**: 個別アイテムの詳細情報と構成部品一覧

### 4. 基本的な使用方法（プログラマティック）

```python
from bom_manager import BOMManager

# BOMマネージャーを初期化
bom = BOMManager("my_bom.db")

# アイテムを追加
bom.add_item(
    item_id="RAW_001",
    item_name="EN 原糸 150デニール",
    item_type="Raw Yarn",
    unit_of_measure="KG",
    material_type="EN",
    denier=150
)

# BOM構成を追加
bom.add_bom_component(
    parent_item_id="PS_001",
    component_item_id="RAW_001", 
    quantity=0.8,
    usage_type="Main Material"
)

# 構成部品を取得
components = bom.get_direct_components("PS_001")

# BOM構造をツリー表示
bom.print_bom_tree("完成品アイテムID")
```

## 主要機能

### BOMManagerクラスのメソッド

#### アイテム管理
- `add_item()`: 新しいアイテムを追加
- `get_item()`: アイテム情報を取得
- `get_all_items_by_type()`: タイプ別アイテム一覧を取得

#### BOM管理
- `add_bom_component()`: BOM構成を追加
- `get_direct_components()`: 直下の構成部品を取得
- `get_multi_level_bom()`: 多段階BOMを展開取得
- `print_bom_tree()`: BOM構造をツリー表示

## サンプルデータの内容

投入されるサンプルデータは以下の製造フローを表現しています：

1. **原糸** (EN 150d, SK 120d)
2. **PS糸** (ENPS 100d S撚/Z撚, SKPS 80d S撚)
3. **芯糸** (PE 30d - 購入品)
4. **製紐糸** (8本編み + 芯糸)
5. **染色糸** (マルチカラー)
6. **巻き取り糸** (100m スプール)
7. **完成品** (梱包材込み)

## データベース設計

### items テーブル
- 基本情報: item_id, item_name, item_type, unit_of_measure
- 材料属性: material_type, denier, ps_ratio, braid_structure, has_core, color, length_m, twist_type
- 拡張属性: additional_attributes (JSON)

### bom_components テーブル  
- BOM関係: parent_item_id, component_item_id, quantity, usage_type
- 外部キー制約とユニーク制約で整合性を保証

## 拡張可能性

このプロトタイプは以下の機能拡張の基盤となります：

- ロット管理機能
- 品質情報管理
- 製造実績記録
- コスト計算
- 在庫管理
- 工程管理

## ライセンス

このプロトタイプは検証・学習目的で作成されています。 