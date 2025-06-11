# 作業用・実験ファイル

このフォルダには、BOM管理システムの開発・実験・データ作成用のスクリプトが保存されています。

## BOM構造作成スクリプト

### `create_realistic_bom.py`
- **目的**: 実際の製造工程に基づいたリアルなBOM構造を作成
- **特徴**:
  - 3層構造（完成品 → 製紐糸 → 原糸）
  - X8編み = 8本の原糸（製造現実に基づく）
  - 基本的なBOM関係を20件作成
- **対象データ**: X-BRAID FULLDRAG X8シリーズ

### `create_advanced_bom.py`
- **目的**: 高度な多層BOM構造と補助材料を含む完全なBOM作成
- **特徴**:
  - 補助材料: スプール、梱包材、ラベル、芯糸
  - 長さベースのスプール選択ロジック
  - 45のBOM関係を36アイテム間で作成
  - より実際の製造に近い構造

## テストファイル

### `test_basic_functionality.py`
- **目的**: BOM管理システムの基本機能テスト
- **テスト内容**:
  - アイテム追加・取得
  - BOM構成の追加・取得
  - 多段階BOM展開
  - データベース操作の整合性

### `test_oracle_integration.py`
- **目的**: Oracle連携機能の基本テスト
- **テスト内容**:
  - Oracle接続テスト
  - 基本的なデータ取得
  - SQLite連携テスト

### `test_oracle_integration_diverse.py`
- **目的**: Oracle連携の多様なデータパターンテスト
- **テスト内容**:
  - 複数カテゴリのデータ取得
  - 大規模データセットの処理
  - エラーハンドリング

## 使用方法

### スクリプト実行
```bash
# プロジェクトルートから実行
cd /path/to/bom-manager

# BOM構造作成（基本版）
python working/create_realistic_bom.py

# BOM構造作成（高度版）
python working/create_advanced_bom.py

# 基本機能テスト
python working/test_basic_functionality.py

# Oracle連携テスト
python working/test_oracle_integration.py
```

### テスト実行手順
1. **環境確認**: 必要なデータベースファイルが存在することを確認
2. **依存関係**: Oracle接続テストには適切な認証情報が必要
3. **実行順序**: 基本テスト → Oracle連携テスト の順で実行推奨

## 注意事項

### 実行前の確認
- ⚠️ **データベースのバックアップを取得**
- ⚠️ **テスト環境で先に動作確認**
- ⚠️ **既存データの上書きに注意**

### スクリプトの性質
- これらは**実験的・開発用**スクリプトです
- 本番環境での直接実行は推奨されません
- 必要に応じて内容を調整・カスタマイズしてください

## 開発履歴

### BOM作成スクリプトの進化
1. **create_realistic_bom.py**: 基本的な3層BOM構造
2. **create_advanced_bom.py**: 補助材料を含む完全なBOM

### テストの発展
1. **test_basic_functionality.py**: 基本機能確認
2. **test_oracle_integration.py**: Oracle連携基本テスト
3. **test_oracle_integration_diverse.py**: 多様なパターンテスト

## 将来の拡張

これらのスクリプトは以下の機能拡張の基盤となります：
- より複雑な製造工程のモデル化
- 品質管理データの統合
- コスト計算の自動化
- 在庫管理との連携 