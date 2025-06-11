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

## 🔄 Oracle DB連携システム

### Oracle DBの位置づけ

本システムは既存のOracle ERPシステムとの密接な連携を前提として設計されています。Oracle DBは以下の役割を担います：

- **マスターシステム**: 製品コード、品目マスタの権威ソース
- **ERP基盤**: 購買、在庫、販売の基幹データ管理
- **連携基盤**: BOM管理システムへのデータ供給

### Oracle連携アーキテクチャ

```
Oracle ERP Database
├─ PCS_PRODUCT_MST (製品マスタ)
├─ M_品目_原糸 (原糸マスタ)
├─ M_品目_PS糸 (PS糸マスタ)
├─ M_品目_木管糸 (木管糸マスタ)
└─ BOM関連テーブル群
     ↓ (同期・連携)
BOM管理システム (SQLite)
├─ items (製品アイテム)
├─ raw_materials (原材料マスタ)
├─ oracle_sync_log (同期履歴)
└─ bom_components (BOM構成)
```

### Oracle連携スキーマ設計

#### 1. アイテムマスタ連携

```sql
-- items テーブル（Oracle連携強化版）
CREATE TABLE items (
    item_id TEXT PRIMARY KEY,                -- 内部ID
    oracle_product_code TEXT UNIQUE,         -- Oracle PRODUCT_CODE
    item_name TEXT NOT NULL,
    item_type TEXT NOT NULL,
    
    -- Oracle同期管理
    oracle_sync_status TEXT DEFAULT 'manual' CHECK (oracle_sync_status IN ('synced', 'manual', 'modified')),
    oracle_last_sync TIMESTAMP,
    
    -- 拡張属性（Oracle PCS_PRODUCT_MST 対応）
    yarn_composition TEXT,                   -- 糸構成
    series_name TEXT,                        -- シリーズ名
    length_m INTEGER,                        -- 標準長さ
    color TEXT,                             -- 色
    knit_type TEXT,                         -- 編み方
    -- その他の属性...
);
```

#### 2. Oracle製品マスタ同期履歴

```sql
-- Oracle同期履歴管理
CREATE TABLE oracle_sync_log (
    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL CHECK (sync_type IN ('products', 'materials', 'full')),
    sync_status TEXT NOT NULL CHECK (sync_status IN ('success', 'failed', 'partial')),
    records_processed INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_added INTEGER DEFAULT 0,
    error_message TEXT,
    sync_started_at TIMESTAMP NOT NULL,
    sync_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. 原材料マスタ連携

```sql
-- 原材料マスタ（Oracle M_品目_* 連携）
CREATE TABLE raw_materials (
    material_id INTEGER PRIMARY KEY AUTOINCREMENT,
    oracle_item_code TEXT UNIQUE,           -- Oracle 品目コード
    material_name TEXT,                     -- 品目名
    material_category TEXT CHECK (material_category IN ('原糸', 'PS糸', '木管糸')),
    yarn_type TEXT,                         -- 原糸種類
    ps_value REAL,                          -- PS値
    ps_yarn_value REAL,                     -- PS糸値
    twist_direction TEXT,                   -- SZ（撚り方向）
    winding_length INTEGER,                 -- 巻きM
    oracle_sync_status TEXT DEFAULT 'synced',
    oracle_last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Oracle連携データフロー

#### 1. 製品マスタ同期
```
Oracle PCS_PRODUCT_MST → items テーブル
- PRODUCT_CODE → oracle_product_code
- 製品名称 → item_name  
- 製品分類 → item_type（マッピング）
- シリーズ → series_name
- 色情報 → color
- 編み方 → knit_type
```

#### 2. 原材料マスタ同期
```
Oracle M_品目_原糸/PS糸/木管糸 → raw_materials テーブル
- 品目コード → oracle_item_code
- 品目名 → material_name
- 原糸種類 → yarn_type
- PS値 → ps_value
- 撚り方向 → twist_direction
```

#### 3. BOM構造連携
```
Oracle BOM関連テーブル → bom_components テーブル
- 親品目コード → parent_item_id (変換)
- 構成品目コード → component_item_id (変換)  
- 構成数量 → quantity
- 用途分類 → usage_type (マッピング)
```

### Oracle連携ツール群

#### 接続・スキーマ分析ツール
- `oracle_connection_test.py`: Oracle DB接続テスト
- `oracle_schema_analysis.py`: Oracle スキーマ構造分析
- `oracle_data_check.py`: データ整合性チェック
- `oracle_connector.py`: Oracle DB接続管理・統合ツール

#### データ分析・抽出ツール
- `oracle_bom_analysis.py`: Oracle BOM構造分析
- `oracle_bom_extraction.py`: Oracle BOM データ抽出
- `oracle_simplified_analysis.py`: Oracle 簡易データ分析
- `oracle_sample_data.py`: Oracle サンプルデータ生成

#### データ管理ツール
- `update_item_prefix_by_type.py`: アイテムタイプ別プレフィックス更新
- `update_item_prefix.py`: アイテムプレフィックス一括更新

### Oracle連携状態管理

#### 同期ステータス
- **synced**: Oracle DBと同期済み
- **manual**: 手動登録（Oracle未連携）
- **modified**: Oracle同期後に手動変更

#### 同期モード
- **products**: 製品マスタのみ同期
- **materials**: 原材料マスタのみ同期
- **full**: 全データ同期

### Oracle連携運用フロー

#### 1. 初期セットアップ
```bash
# Oracle接続テスト
python tools/oracle_connection_test.py

# スキーマ分析
python tools/oracle_schema_analysis.py

# BOMデータ抽出
python tools/oracle_bom_extraction.py
```

#### 2. データ分析・監視
```bash
# BOM構造分析
python tools/oracle_bom_analysis.py

# 簡易データ分析  
python tools/oracle_simplified_analysis.py

# サンプルデータ生成
python tools/oracle_sample_data.py
```

#### 3. データ検証
```bash
# 整合性チェック
python tools/oracle_data_check.py

# BOM構造分析
python tools/oracle_bom_analysis.py

# 簡易データ分析
python tools/oracle_simplified_analysis.py
```

### Oracle連携設定

#### 接続情報（環境変数）
```bash
export ORACLE_HOST="oracle-server.company.com"
export ORACLE_PORT="1521"
export ORACLE_SERVICE="ORCL"
export ORACLE_USERNAME="bom_user"
export ORACLE_PASSWORD="secure_password"
```

#### 接続管理（oracle_connector.py）
- 統合Oracle接続管理
- 接続プールとタイムアウト処理
- エラーハンドリングと再接続機能
- SQL実行ユーティリティ

### Oracle DBテーブルマッピング

| Oracle テーブル | SQLite テーブル | 目的 |
|----------------|----------------|------|
| PCS_PRODUCT_MST | items | 製品マスタ連携 |
| M_品目_原糸 | raw_materials | 原糸マスタ |
| M_品目_PS糸 | raw_materials | PS糸マスタ |
| M_品目_木管糸 | raw_materials | 木管糸マスタ |
| BOM関連テーブル | bom_components | BOM構成 |

### 注意事項とベストプラクティス

#### データ整合性
- Oracle DBからの同期データは読み取り専用として扱う
- 手動変更したデータは `oracle_sync_status = 'modified'` でマーク
- 同期前に必ずバックアップを取得

#### パフォーマンス
- 大量データ同期時はバッチ処理を使用
- インクリメンタル同期で差分のみ更新
- インデックスを適切に設定

#### セキュリティ
- Oracle接続情報は環境変数で管理
- 最小権限の原則でOracle userを作成
- 通信は暗号化接続（SSL/TLS）を使用

## 拡張可能性

このシステムは以下の機能拡張の基盤となります：

- **Oracle ERP システム連携** (実装済み)
- **ロット管理機能** (実装済み)
- **品質情報管理** (実装済み)
- 製造実績記録
- コスト計算
- 在庫管理
- 工程管理

## 📋 ロット管理システム

### ロット管理の位置づけ

釣り糸製造における各工程でのロット単位での品質管理、在庫管理、トレーサビリティを実現します。

### ロット管理アーキテクチャ

```
製造工程フロー
原糸投入 → PS工程 → Winder → Braid → Sensor → 染色 → 後PS → Spool → 完成品
   L1        L2      L3      L4      L5      L6      L7      L8      L9

各工程でのロット生成・追跡
├─ ロットID自動生成 (YY-MM-工程コード-連番)
├─ 品質グレード管理 (A/A0/B/S)
├─ 在庫数量管理
├─ 系統図管理 (親子関係)
└─ 品質検査履歴
```

### ロット管理スキーマ

#### 1. ロットマスタ

```sql
CREATE TABLE lots (
    lot_id TEXT PRIMARY KEY,              -- ロットID (2506P087形式)
    item_id TEXT NOT NULL,                -- アイテムID  
    process_code TEXT NOT NULL,           -- 工程コード (P/W/B/S/C/T/E/F)
    
    -- 基本情報
    production_date DATE NOT NULL,        -- 製造日
    planned_quantity REAL NOT NULL,       -- 計画数量
    actual_quantity REAL,                 -- 実績数量
    current_quantity REAL,                -- 現在数量
    
    -- 品質情報
    quality_grade TEXT NOT NULL,          -- 品質グレード (A/A0/B/S)
    inspection_status TEXT DEFAULT 'pending',  -- 検査状況
    
    -- 状態管理
    lot_status TEXT DEFAULT 'active',     -- ロット状態
    location TEXT,                        -- 保管場所
    
    -- 製造情報  
    equipment_id TEXT,                    -- 使用設備
    operator_id TEXT,                     -- 作業者
    measured_length REAL,                 -- 実測長(m)
    measured_weight REAL,                 -- 実測重量(kg)
    
    FOREIGN KEY (item_id) REFERENCES items(item_id),
    FOREIGN KEY (process_code) REFERENCES process_steps(process_code),
    FOREIGN KEY (quality_grade) REFERENCES quality_grades(grade_code)
);
```

#### 2. ロット系統図（トレーサビリティ）

```sql
CREATE TABLE lot_genealogy (
    genealogy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_lot_id TEXT NOT NULL,          -- 親ロット（投入される側）
    child_lot_id TEXT NOT NULL,           -- 子ロット（消費される側）
    
    consumed_quantity REAL NOT NULL,      -- 消費数量
    consumption_rate REAL,                -- 消費率(%)
    consumption_date TIMESTAMP NOT NULL,   -- 消費日時
    
    usage_type TEXT NOT NULL CHECK (usage_type IN (
        'Main Material',    -- 主原料
        'Core Thread',      -- 芯糸
        'Additive',        -- 添加材
        'Rework Input',    -- リワーク投入
        'Quality Upgrade'  -- 品質向上用
    )),
    
    FOREIGN KEY (parent_lot_id) REFERENCES lots(lot_id),
    FOREIGN KEY (child_lot_id) REFERENCES lots(lot_id)
);
```

#### 3. 在庫移動トランザクション

```sql
CREATE TABLE inventory_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL,
    
    transaction_type TEXT NOT NULL CHECK (transaction_type IN (
        'RECEIPT',      -- 入庫（製造完了）
        'CONSUMPTION',  -- 消費（次工程投入）
        'TRANSFER',     -- 移動（場所変更）
        'ADJUSTMENT',   -- 調整（棚卸等）
        'SCRAP',       -- 廃棄
        'REWORK'       -- リワーク
    )),
    
    quantity_before REAL NOT NULL,        -- 変更前数量
    quantity_change REAL NOT NULL,        -- 変更数量(±)
    quantity_after REAL NOT NULL,         -- 変更後数量
    
    transaction_date TIMESTAMP NOT NULL,   -- 実行日時
    operator_id TEXT,                     -- 実行者
    
    FOREIGN KEY (lot_id) REFERENCES lots(lot_id)
);
```

#### 4. 品質検査結果

```sql
CREATE TABLE lot_quality_inspections (
    inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL,
    
    inspection_type TEXT NOT NULL CHECK (inspection_type IN (
        'INCOMING',          -- 入荷検査
        'IN_PROCESS',        -- 工程内検査  
        'FINAL',             -- 最終検査
        'CUSTOMER_COMPLAINT' -- 顧客クレーム対応
    )),
    
    inspection_date TIMESTAMP NOT NULL,
    inspector_id TEXT,
    
    inspection_items TEXT,                -- 検査項目（JSON）
    inspection_results TEXT,              -- 検査結果（JSON）
    overall_judgment TEXT NOT NULL CHECK (overall_judgment IN ('PASS', 'FAIL', 'CONDITIONAL')),
    
    assigned_grade TEXT,                  -- 判定グレード
    defect_types TEXT,                    -- 不具合種類（JSON）
    
    FOREIGN KEY (lot_id) REFERENCES lots(lot_id)
);
```

### 工程・品質管理マスタ

#### 工程ステップマスタ
```sql
CREATE TABLE process_steps (
    process_code TEXT PRIMARY KEY,        -- P/W/B/S/C/T/E/F
    process_name TEXT NOT NULL,           -- 工程名
    process_level INTEGER NOT NULL,       -- 工程レベル(L1-L9)
    typical_unit TEXT NOT NULL,           -- 標準単位
    accuracy_type TEXT NOT NULL,          -- 確定度(概算/近似/実測)
    description TEXT                      -- 工程説明
);
```

#### 品質グレードマスタ
```sql
CREATE TABLE quality_grades (
    grade_code TEXT PRIMARY KEY,          -- A/A0/B/S
    grade_name TEXT NOT NULL,             -- 品質名称
    grade_description TEXT,               -- 品質説明
    processing_rule TEXT,                 -- 処理指針
    is_usable_for_next_process BOOLEAN DEFAULT TRUE  -- 次工程投入可否
);
```

### ロット管理機能

#### BOMManagerクラスのロット管理メソッド

```python
# ロット作成
lot_id = bom.create_lot(
    item_id="BRAID-PE-10",
    process_code="B",
    planned_quantity=1000.0,
    production_date="2025-06-11",
    quality_grade="A"
)

# ロット情報取得
lot = bom.get_lot(lot_id)

# ロット系統図追加（原料投入）
bom.add_lot_genealogy(
    parent_lot_id="2506B001",  # 製紐ロット
    child_lot_id="2506P087",   # PS糸ロット
    consumed_quantity=500.0,
    usage_type="Main Material"
)

# ロット系統図取得（トレーサビリティ）
forward_tree = bom.get_lot_genealogy_tree(lot_id, 'forward')   # 前方トレース
backward_tree = bom.get_lot_genealogy_tree(lot_id, 'backward') # 後方トレース
```

### ロットID体系

#### 命名規則
```
YY-MM-工程コード-連番3桁
例: 2506P087 (2025年6月、PS工程、87番目)
```

#### 工程コード
- **P**: PS工程 (L2)
- **W**: Winder工程 (L3)
- **B**: Braid工程 (L4)
- **S**: Sensor工程 (L5)
- **C**: 染色工程 (L6)
- **T**: 後PS工程 (L7)
- **E**: Spool工程 (L8)
- **F**: 完成品工程 (L9)

### 品質グレード体系

| コード | 名称 | 処理指針 | 次工程投入 |
|--------|------|----------|------------|
| A | 合格品 | 原則、下位工程へ投入可 | ✓ |
| A0 | 軽微難品 | 自社使用優先 | ✓ |
| B | 代用品 | 芯糸専用／要ラベル色替 | ✓ |
| S | 端下品 | 自動廃棄 or 指定回収ロット | ✗ |

### ロット系統図サンプル

```
製品ロット 2506F001 (完成品)
└─ 巻ロット 2506E045 (Spool)
   └─ 染色ロット 2506C112 (染色)
      ├─ センサーロット 2506S067 (Sensor)
      │  └─ 製紐ロット 2506B048 (Braid)
      │     ├─ Winderロット 2506W311 (Winder)
      │     │  └─ PSロット 2506P087 (Grade A)
      │     │     └─ 原糸ロット TY-210331-17
      │     └─ 芯糸ロット 2506P081 (Grade B 転用)
      │        └─ 原糸ロット TY-210228-03
      └─ 染料添加剤ロット DYE-2506-001
```

### Web UI機能

#### ロット管理画面
- **ロット一覧**: `/lots` - フィルタリング、検索機能付き
- **ロット詳細**: `/lots/{lot_id}` - 基本情報、在庫履歴
- **ロット作成**: `/lots/create` - 新規ロット作成フォーム
- **ロット系統図**: `/lots/{lot_id}/genealogy` - 前方・後方トレース
- **ロット投入**: `/lots/{lot_id}/consume` - 他ロットへの投入

#### APIエンドポイント
```bash
# ロット一覧取得
GET /api/lots?status=active&item_type=PS糸

# ロット詳細取得  
GET /api/lots/{lot_id}

# ロット系統図取得
GET /api/lots/{lot_id}/genealogy?direction=forward
```

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