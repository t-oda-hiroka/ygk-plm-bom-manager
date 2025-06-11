# 釣り糸製造BOM管理システム 統合環境版

このプロジェクトは、釣り糸の製造プロセスにおけるBOM（部品表）を管理するための統合環境システムです。

## 🌟 新機能（v1.0統合版）

- **統一環境管理**: 開発・ステージング・本番環境を単一コードベースで管理
- **自動デプロイメント**: `deploy.py`による環境間の自動データ移行
- **統一起動システム**: `start_unified.sh`による環境一括管理
- **環境別設定**: `config.py`による設定の自動切り替え
- **LAN対応**: 社内ネットワークからのアクセス可能

## 概要

製造プロセス（原糸 → PS → ワインダー → 製紐 → センサー → 染色 → 後PS → 巻き → 仕上げ）における糸の名称や状態変化を追跡し、各中間生成物および最終製品の構成部品を管理します。

## 🚀 環境構成

### 開発環境
- **URL**: http://192.168.212.112:5002
- **用途**: 新機能開発、テスト、デバッグ
- **データベース**: `bom_database_dev.db`
- **特徴**: デバッグモード有効、サンプルデータ自動生成

### ステージング環境  
- **URL**: http://192.168.212.112:5003
- **用途**: 本番前テスト、ユーザー受け入れテスト
- **データベース**: `bom_database_staging.db`
- **特徴**: 本番相当環境、リセット機能、環境表示バナー

### 本番環境（予定）
- **URL**: http://192.168.212.112:5001
- **用途**: 実際の業務利用
- **データベース**: `bom_database_prod.db`
- **特徴**: 高セキュリティ、ログ機能、パフォーマンス最適化

## 🔧 セットアップと起動

### 1. 環境要件
- Python 3.7以上
- Flask 2.0以上

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. 統一環境システムの起動

```bash
# 両環境を一括起動
./start_unified.sh both

# 開発環境のみ起動
./start_unified.sh dev

# ステージング環境のみ起動  
./start_unified.sh staging

# 環境状況確認
./start_unified.sh status

# 全環境停止
./start_unified.sh stop
```

### 4. 個別環境の起動（手動）
```bash
# 開発環境
python app_unified.py

# ステージング環境
FLASK_ENV=staging python app_unified.py

# 本番環境
FLASK_ENV=production python app_unified.py
```

## 📦 デプロイメント管理

### 環境間データ移行
```bash
# 開発 → ステージング
python deploy.py deploy development staging

# ステージング → 本番
python deploy.py deploy staging production

# デプロイ履歴確認
python deploy.py history

# ロールバック
python deploy.py rollback staging
```

### デプロイメント内容
- データベースの自動バックアップ
- 環境別データ変換・調整
- Git履歴との連携
- JSON形式のデプロイメントマニフェスト生成

## 📊 システム状況確認

### API エンドポイント
```bash
# 開発環境ステータス
curl http://192.168.212.112:5002/api/status

# ステージング環境ステータス  
curl http://192.168.212.112:5003/api/status
```

### レスポンス例
```json
{
  "environment": "DEVELOPMENT",
  "version": "v1.0",
  "total_items": 36,
  "total_bom_components": 45,
  "item_type_count": 7,
  "last_updated": "2025-06-11T15:30:05.965281"
}
```

## 特徴

- **多段階BOM管理**: 原糸から完成品まで最大7階層のBOM構造を表現
- **柔軟な属性管理**: 材質、デニール、PS値、編み構造、色など糸特有の属性を管理
- **用途別分類**: 主材料、編み糸、芯糸、梱包材などの用途別分類
- **環境別設定**: 開発・ステージング・本番で自動的に設定切り替え
- **統合管理**: 単一コードベースで複数環境を管理

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

### 🚀 統合環境システム（メインシステム）
- `app_unified.py`: 統合Flaskアプリケーション（メイン）
- `config.py`: 環境別設定管理
- `deploy.py`: 自動デプロイメントシステム
- `start_unified.sh`: 統一環境起動スクリプト

### 💾 コアシステム
- `bom_manager.py`: BOM管理システムのメインクラス
- `schema_enhanced.sql`: 拡張データベーススキーマ
- `requirements.txt`: 依存関係（Flask等）
- `bom_database_dev.db`: 開発環境データベース
- `bom_database_staging.db`: ステージング環境データベース

### 🔧 ツール・ユーティリティ (`tools/`)
- `update_item_prefix_by_type.py`: アイテムタイプ別プレフィックス更新
- `oracle_connection_test.py`: Oracle DB接続テスト
- `oracle_schema_analysis.py`: Oracleスキーマ分析
- `oracle_bom_analysis.py`: Oracle BOM構造分析
- `oracle_data_check.py`: データ整合性チェック
- その他Oracle関連ツール群

### 🧪 作業用・実験ファイル (`working/`)
- `create_realistic_bom.py`: リアルBOM構造作成（基本版）
- `create_advanced_bom.py`: 高度BOM構造作成（完全版）
- `test_basic_functionality.py`: 基本機能テスト
- `test_oracle_integration.py`: Oracle連携テスト
- `test_oracle_integration_diverse.py`: 多様パターンテスト

### 📚 レガシーファイル (`legacy/`)
- `app.py`: 旧版シンプルアプリケーション
- `app_enhanced.py`: 旧版Oracle連携アプリケーション
- `app_staging.py`: 旧版ステージングアプリケーション
- `bom_database.db`, `bom_database_enhanced.db`: 旧版データベース
- `schema.sql`: 旧版データベーススキーマ
- その他旧ファイル群

### 💾 バックアップ (`backups/`)
- `backup_development_*.db`: 開発環境バックアップ
- `deployment_manifest_*.json`: デプロイメント履歴

### 🌐 テンプレート
- `templates/`: HTMLテンプレートファイル
  - `base.html`: ベーステンプレート（環境表示対応）
  - `index.html`: アイテム一覧ページ（ソート機能付き）
  - `add_item.html`: アイテム追加フォーム
  - `bom_tree.html`: BOM構造表示ページ
  - `add_bom.html`: BOM構成追加フォーム
  - `item_details.html`: アイテム詳細ページ

## Webアプリケーションの機能

- **アイテム一覧**: 登録されたアイテムの一覧表示とフィルタリング
  - **ソート機能**: 列ヘッダークリックで昇順・降順ソート
  - **データタイプ対応**: 文字列と数値の適切なソート処理
  - **アイテムタイプ別表示**: 完成品を優先したスマートソート
- **アイテム追加**: 新しいアイテムの登録フォーム
- **BOM構成追加**: アイテム間のBOM関係を設定
- **BOM構造表示**: 多段階BOM構造の視覚的なツリー表示
- **アイテム詳細**: 個別アイテムの詳細情報と構成部品一覧
- **環境表示**: 現在の環境を明確に表示（ステージング環境）

## 基本的な使用方法（プログラマティック）

```python
from bom_manager import BOMManager

# BOMマネージャーを初期化
bom = BOMManager("my_bom.db")

# アイテムを追加
bom.add_item(
    item_id="RAW_001",
    item_name="EN 原糸 150デニール",
    item_type="原糸",
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

## 🔧 主要機能

### BOMManagerクラスのメソッド

#### アイテム管理
- `add_item()`: 新しいアイテムを追加
- `get_item()`: アイテム情報を取得
- `get_all_items()`: 全アイテム取得
- `get_all_items_by_type()`: タイプ別アイテム一覧を取得

#### BOM管理
- `add_bom_component()`: BOM構成を追加
- `get_direct_components()`: 直下の構成部品を取得
- `get_multi_level_bom()`: 多段階BOMを展開取得
- `print_bom_tree()`: BOM構造をツリー表示

## 環境管理ワークフロー

### 開発フロー
1. **開発環境**で新機能を開発・テスト
2. **ステージング環境**にデプロイして受け入れテスト
3. **本番環境**にリリース

### データ同期
```bash
# 開発データをステージングに移行
python deploy.py deploy development staging

# 問題があればロールバック
python deploy.py rollback staging
```

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

このシステムは以下の機能拡張の基盤となります：

- Oracle ERP システム連携
- ロット管理機能
- 品質情報管理
- 製造実績記録
- コスト計算
- 在庫管理
- 工程管理

## トラブルシューティング

### よくある問題

#### ポート競合
```bash
# ポート使用状況確認
lsof -i :5002 -i :5003

# プロセス強制終了
./start_unified.sh stop
```

#### 環境が起動しない
```bash
# ログ確認
tail -f dev.log
tail -f staging.log

# 手動起動
python app_unified.py
```

#### データベースエラー
```bash
# 環境リセット（ステージングのみ）
# ブラウザでステージング環境の「環境リセット」ボタンをクリック
```

## ライセンス

このシステムは業務用途で開発されています。 