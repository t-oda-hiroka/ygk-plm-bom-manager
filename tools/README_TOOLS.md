# ツール・ユーティリティ

このフォルダには、BOM管理システムのメンテナンス・分析・管理用ツールが保存されています。

## プレフィックス管理ツール

### `update_item_prefix_by_type.py`
- **目的**: アイテムタイプ別の意味のあるプレフィックスに一括変更
- **使用例**: 
  ```bash
  python update_item_prefix_by_type.py
  ```
- **変更内容**:
  - 完成品 → `PRODUCT_`
  - 製紐糸 → `BRAID_`
  - PS糸 → `PS_`
  - 原糸 → `YARN_`
  - 芯糸 → `CORE_`
  - 成形品 → `FORM_`
  - 梱包資材 → `PACK_`

### `update_item_prefix.py`
- **目的**: 旧版プレフィックス更新ツール（参考用）
- **状況**: レガシー版、現在は`update_item_prefix_by_type.py`を使用

## Oracle関連ツール

### 接続・テスト
- `oracle_connection_test.py` - Oracle DB接続テスト
- `oracle_data_check.py` - Oracleデータ整合性チェック

### 分析ツール  
- `oracle_schema_analysis.py` - Oracleスキーマ構造分析
- `oracle_bom_analysis.py` - Oracle BOM構造分析
- `oracle_simplified_analysis.py` - 簡易分析レポート

### データ抽出・管理
- `oracle_bom_extraction.py` - Oracle BOMデータ抽出
- `oracle_sample_data.py` - Oracleサンプルデータ取得
- `oracle_connector.py` - Oracle接続管理クラス

## 使用方法

### 基本的な使用手順
1. **事前確認**: 対象データベースのバックアップを取得
2. **テスト実行**: 小規模データでツールをテスト
3. **本実行**: 本番データに適用
4. **結果確認**: 処理結果の検証

### 注意事項
- ⚠️ **データベース操作を伴うツールは必ずバックアップを取得してから実行**
- ⚠️ **本番環境では事前にステージング環境でテスト**
- ⚠️ **Oracle接続ツールは適切な認証情報が必要**

## ツール実行環境

これらのツールは以下の環境で実行してください：

```bash
# プロジェクトルートディレクトリで実行
cd /path/to/bom-manager
python tools/ツール名.py
```

## メンテナンス

定期的な実行が推奨されるツール：
- `oracle_data_check.py` - 月次
- `oracle_schema_analysis.py` - 四半期毎 