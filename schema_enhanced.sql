-- 釣り糸製造BOM管理システム 拡張データベーススキーマ
-- Oracle DB連携対応版

-- アイテムマスタテーブル（Oracle PCS_PRODUCT_MST との連携強化）
CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,                    -- 内部ID
    oracle_product_code TEXT UNIQUE,             -- Oracle PRODUCT_CODE との連携キー
    item_name TEXT NOT NULL,
    item_type TEXT NOT NULL CHECK (item_type IN (
        '原糸',               -- 原糸
        'PS糸',               -- PS糸  
        '製紐糸',             -- 製紐糸
        '染色糸',             -- 染色糸
        '後PS糸',             -- 後PS糸
        '巻き取り糸',         -- 巻き取られた糸
        '完成品',             -- 完成品
        '芯糸',               -- 芯糸
        '梱包資材',           -- 梱包資材
        '成形品'              -- 成形品（スプール等）
    )),
    unit_of_measure TEXT NOT NULL CHECK (unit_of_measure IN ('KG', 'M', '個', '枚', 'セット', '本')),
    
    -- 基本材料属性
    material_type TEXT,       -- EN, SK, AL等
    denier INTEGER,           -- デニール
    ps_ratio REAL,            -- PS値
    twist_type TEXT CHECK (twist_type IN ('S', 'Z', NULL)), -- 撚り方向
    
    -- Oracle連携強化属性
    yarn_composition TEXT,    -- 糸構成（ナイロン等）
    series_name TEXT,         -- シリーズ名（X-BRAID等）
    length_m INTEGER,         -- 標準長さ(m)
    color TEXT,               -- 色
    knit_type TEXT,           -- 編み方（X8、X4等）
    yarn_type TEXT,           -- 糸種
    raw_num REAL,             -- 生糸号数
    production_num REAL,      -- 生産号数
    core_yarn_type TEXT,      -- 芯糸種類
    spool_type TEXT,          -- スプール種類
    
    -- 旧属性（互換性のため残す）
    braid_structure TEXT,     -- x4, x8等の編み構造
    has_core BOOLEAN,         -- 芯糸有無
    
    -- 追加属性をJSONで柔軟に格納
    additional_attributes TEXT, -- JSON形式で追加属性を保存
    
    -- Oracle同期関連
    oracle_sync_status TEXT DEFAULT 'manual' CHECK (oracle_sync_status IN ('synced', 'manual', 'modified')),
    oracle_last_sync TIMESTAMP,
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BOM構成テーブル（拡張版）
CREATE TABLE IF NOT EXISTS bom_components (
    bom_component_id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_item_id TEXT NOT NULL,
    component_item_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    usage_type TEXT NOT NULL CHECK (usage_type IN (
        'Main Material',      -- 主材料
        'Main Braid Thread',  -- 主編み糸
        'Core Thread',        -- 芯糸
        'Packaging',          -- 梱包材
        'Container',          -- 容器（スプール等）
        'Process Material'    -- 工程材料
    )),
    
    -- 工程情報追加
    process_step INTEGER,     -- 工程順序
    loss_ratio REAL DEFAULT 0.0, -- ロス率
    remarks TEXT,             -- 備考
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外部キー制約
    FOREIGN KEY (parent_item_id) REFERENCES items(item_id),
    FOREIGN KEY (component_item_id) REFERENCES items(item_id),
    
    -- ユニーク制約（同じ親に対して同じ構成部品が同じ用途で重複しないように）
    UNIQUE(parent_item_id, component_item_id, usage_type)
);

-- Oracle製品マスタ同期履歴テーブル
CREATE TABLE IF NOT EXISTS oracle_sync_log (
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

-- 原材料マスタテーブル（Oracle M_品目_* との連携）
CREATE TABLE IF NOT EXISTS raw_materials (
    material_id INTEGER PRIMARY KEY AUTOINCREMENT,
    oracle_item_code TEXT UNIQUE,    -- Oracle 品目コード
    material_name TEXT,              -- 品目名
    material_category TEXT CHECK (material_category IN ('原糸', 'PS糸', '木管糸')),
    yarn_type TEXT,                  -- 原糸種類
    ps_value REAL,                   -- PS値
    ps_yarn_value REAL,              -- PS糸値
    twist_direction TEXT,            -- SZ（撚り方向）
    winding_length INTEGER,          -- 巻きM
    oracle_sync_status TEXT DEFAULT 'synced',
    oracle_last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type);
CREATE INDEX IF NOT EXISTS idx_items_material ON items(material_type);
CREATE INDEX IF NOT EXISTS idx_items_oracle_code ON items(oracle_product_code);
CREATE INDEX IF NOT EXISTS idx_items_knit_type ON items(knit_type);
CREATE INDEX IF NOT EXISTS idx_items_series ON items(series_name);
CREATE INDEX IF NOT EXISTS idx_bom_parent ON bom_components(parent_item_id);
CREATE INDEX IF NOT EXISTS idx_bom_component ON bom_components(component_item_id);
CREATE INDEX IF NOT EXISTS idx_raw_materials_oracle ON raw_materials(oracle_item_code);
CREATE INDEX IF NOT EXISTS idx_sync_log_type ON oracle_sync_log(sync_type);

-- 更新日時の自動更新トリガー
CREATE TRIGGER update_items_timestamp 
    AFTER UPDATE ON items
    BEGIN
        UPDATE items SET updated_at = CURRENT_TIMESTAMP WHERE item_id = NEW.item_id;
    END;

CREATE TRIGGER update_bom_timestamp 
    AFTER UPDATE ON bom_components
    BEGIN
        UPDATE bom_components SET updated_at = CURRENT_TIMESTAMP WHERE bom_component_id = NEW.bom_component_id;
    END;

CREATE TRIGGER update_materials_timestamp 
    AFTER UPDATE ON raw_materials
    BEGIN
        UPDATE raw_materials SET updated_at = CURRENT_TIMESTAMP WHERE material_id = NEW.material_id;
    END;

-- Oracle同期ステータス更新トリガー
CREATE TRIGGER update_oracle_sync_status 
    AFTER UPDATE ON items
    WHEN NEW.oracle_product_code IS NOT NULL AND OLD.item_name != NEW.item_name
    BEGIN
        UPDATE items SET oracle_sync_status = 'modified' WHERE item_id = NEW.item_id;
    END; 

-- =============================================================================
-- ロット管理システム - 追加テーブル群
-- =============================================================================

-- 工程ステップマスタテーブル
CREATE TABLE IF NOT EXISTS process_steps (
    process_code TEXT PRIMARY KEY,              -- 工程コード (P, W, B, S, C, E, F)
    process_name TEXT NOT NULL,                 -- 工程名
    process_level INTEGER NOT NULL,             -- 工程レベル (L1-L9)
    typical_unit TEXT NOT NULL CHECK (typical_unit IN ('KG', 'M', '個')), -- 標準単位
    accuracy_type TEXT NOT NULL CHECK (accuracy_type IN ('概算', '近似', '実測')), -- 確定度
    description TEXT,                           -- 工程説明
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 品質グレードマスタテーブル
CREATE TABLE IF NOT EXISTS quality_grades (
    grade_code TEXT PRIMARY KEY,               -- 品質コード (A, A0, B, S)
    grade_name TEXT NOT NULL,                  -- 品質名称
    grade_description TEXT,                    -- 品質説明
    processing_rule TEXT,                      -- 処理指針
    is_usable_for_next_process BOOLEAN DEFAULT TRUE, -- 次工程投入可否
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ロットマスタテーブル
CREATE TABLE IF NOT EXISTS lots (
    lot_id TEXT PRIMARY KEY,                   -- ロットID (YY-MM-工程コード-連番3桁)
    item_id TEXT NOT NULL,                     -- アイテムID
    process_code TEXT NOT NULL,                -- 工程コード
    
    -- ロット基本情報
    lot_name TEXT,                             -- ロット名称
    production_date DATE NOT NULL,             -- 製造日
    expiry_date DATE,                          -- 有効期限
    
    -- 数量情報
    planned_quantity REAL NOT NULL,            -- 計画数量
    actual_quantity REAL,                      -- 実績数量
    current_quantity REAL,                     -- 現在数量
    unit_of_measure TEXT NOT NULL,             -- 数量単位
    accuracy_type TEXT NOT NULL CHECK (accuracy_type IN ('概算', '近似', '実測')), -- 確定度
    
    -- 品質情報
    quality_grade TEXT NOT NULL,               -- 品質グレード
    quality_notes TEXT,                        -- 品質メモ
    inspection_status TEXT DEFAULT 'pending' CHECK (inspection_status IN ('pending', 'passed', 'failed', 'conditional')),
    
    -- 製造情報
    equipment_id TEXT,                         -- 使用設備ID
    operator_id TEXT,                          -- 作業者ID
    shift_info TEXT,                           -- シフト情報
    
    -- ロット状態
    lot_status TEXT DEFAULT 'active' CHECK (lot_status IN ('active', 'consumed', 'scrapped', 'reworked', 'transferred')),
    location TEXT,                             -- 保管場所
    
    -- 特殊属性
    is_rework BOOLEAN DEFAULT FALSE,           -- リワーク品フラグ
    is_byproduct BOOLEAN DEFAULT FALSE,        -- 副産物フラグ
    usage_restriction TEXT,                    -- 用途制限（芯糸専用等）
    
    -- 実測情報（センサー測定値等）
    measured_length REAL,                      -- 実測長(m)
    measured_weight REAL,                      -- 実測重量(kg)
    measurement_notes TEXT,                    -- 測定メモ
    
    -- 外部システム連携
    oracle_lot_id TEXT,                        -- Oracle側ロットID
    barcode_data TEXT,                         -- バーコード/QRコードデータ
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外部キー制約
    FOREIGN KEY (item_id) REFERENCES items(item_id),
    FOREIGN KEY (process_code) REFERENCES process_steps(process_code),
    FOREIGN KEY (quality_grade) REFERENCES quality_grades(grade_code)
);

-- ロット系統図テーブル（Lot Genealogy）
CREATE TABLE IF NOT EXISTS lot_genealogy (
    genealogy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_lot_id TEXT NOT NULL,               -- 親ロットID（投入される側）
    child_lot_id TEXT NOT NULL,                -- 子ロットID（消費される側）
    
    -- 消費情報
    consumed_quantity REAL NOT NULL,           -- 消費数量
    consumption_rate REAL,                     -- 消費率（子ロット総量に対する％）
    
    -- 工程情報
    process_code TEXT NOT NULL,                -- 投入工程
    consumption_date TIMESTAMP NOT NULL,       -- 消費日時
    
    -- 用途・目的
    usage_type TEXT NOT NULL CHECK (usage_type IN (
        'Main Material',      -- 主原料
        'Core Thread',        -- 芯糸
        'Additive',          -- 添加材
        'Rework Input',      -- リワーク投入
        'Quality Upgrade'    -- 品質向上用
    )),
    
    -- 備考
    notes TEXT,                                -- 備考
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外部キー制約
    FOREIGN KEY (parent_lot_id) REFERENCES lots(lot_id),
    FOREIGN KEY (child_lot_id) REFERENCES lots(lot_id),
    FOREIGN KEY (process_code) REFERENCES process_steps(process_code),
    
    -- ユニーク制約（同じ親子組み合わせの重複防止）
    UNIQUE(parent_lot_id, child_lot_id, usage_type)
);

-- 在庫移動トランザクションテーブル
CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL,                      -- 対象ロットID
    
    -- トランザクション基本情報
    transaction_type TEXT NOT NULL CHECK (transaction_type IN (
        'RECEIPT',           -- 入庫（製造完了、購入等）
        'CONSUMPTION',       -- 消費（次工程投入）
        'TRANSFER',          -- 移動（場所変更）
        'ADJUSTMENT',        -- 調整（棚卸等）
        'SCRAP',            -- 廃棄
        'REWORK',           -- リワーク
        'QUALITY_CHANGE'    -- 品質変更
    )),
    
    -- 数量情報
    quantity_before REAL NOT NULL,             -- 変更前数量
    quantity_change REAL NOT NULL,             -- 変更数量（±）
    quantity_after REAL NOT NULL,              -- 変更後数量
    
    -- 移動情報
    location_from TEXT,                        -- 移動元
    location_to TEXT,                          -- 移動先
    
    -- 関連情報
    related_lot_id TEXT,                       -- 関連ロットID（投入先等）
    related_process TEXT,                      -- 関連工程
    reference_document TEXT,                   -- 参照伝票番号
    
    -- 実行情報
    transaction_date TIMESTAMP NOT NULL,       -- 実行日時
    operator_id TEXT,                          -- 実行者ID
    equipment_id TEXT,                         -- 使用設備ID
    
    -- 備考
    notes TEXT,                                -- 備考
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外部キー制約
    FOREIGN KEY (lot_id) REFERENCES lots(lot_id),
    FOREIGN KEY (related_lot_id) REFERENCES lots(lot_id)
);

-- ロット品質検査結果テーブル
CREATE TABLE IF NOT EXISTS lot_quality_inspections (
    inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id TEXT NOT NULL,                      -- 対象ロットID
    
    -- 検査基本情報
    inspection_type TEXT NOT NULL CHECK (inspection_type IN (
        'INCOMING',          -- 入荷検査
        'IN_PROCESS',        -- 工程内検査
        'FINAL',             -- 最終検査
        'CUSTOMER_COMPLAINT' -- 顧客クレーム対応
    )),
    inspection_date TIMESTAMP NOT NULL,        -- 検査日時
    inspector_id TEXT,                         -- 検査者ID
    
    -- 検査項目・結果
    inspection_items TEXT,                     -- 検査項目（JSON形式）
    inspection_results TEXT,                   -- 検査結果（JSON形式）
    overall_judgment TEXT NOT NULL CHECK (overall_judgment IN ('PASS', 'FAIL', 'CONDITIONAL')),
    
    -- 品質判定
    assigned_grade TEXT,                       -- 判定グレード
    defect_types TEXT,                         -- 不具合種類（JSON形式）
    corrective_actions TEXT,                   -- 是正措置
    
    -- 備考
    notes TEXT,                                -- 備考
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外部キー制約
    FOREIGN KEY (lot_id) REFERENCES lots(lot_id),
    FOREIGN KEY (assigned_grade) REFERENCES quality_grades(grade_code)
);

-- =============================================================================
-- ロット管理用インデックス
-- =============================================================================

-- lotsテーブル用インデックス
CREATE INDEX IF NOT EXISTS idx_lots_item_id ON lots(item_id);
CREATE INDEX IF NOT EXISTS idx_lots_process_code ON lots(process_code);
CREATE INDEX IF NOT EXISTS idx_lots_production_date ON lots(production_date);
CREATE INDEX IF NOT EXISTS idx_lots_quality_grade ON lots(quality_grade);
CREATE INDEX IF NOT EXISTS idx_lots_status ON lots(lot_status);
CREATE INDEX IF NOT EXISTS idx_lots_barcode ON lots(barcode_data);

-- lot_genealogyテーブル用インデックス
CREATE INDEX IF NOT EXISTS idx_genealogy_parent ON lot_genealogy(parent_lot_id);
CREATE INDEX IF NOT EXISTS idx_genealogy_child ON lot_genealogy(child_lot_id);
CREATE INDEX IF NOT EXISTS idx_genealogy_process ON lot_genealogy(process_code);
CREATE INDEX IF NOT EXISTS idx_genealogy_date ON lot_genealogy(consumption_date);

-- inventory_transactionsテーブル用インデックス
CREATE INDEX IF NOT EXISTS idx_transactions_lot_id ON inventory_transactions(lot_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON inventory_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON inventory_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_related_lot ON inventory_transactions(related_lot_id);

-- lot_quality_inspectionsテーブル用インデックス
CREATE INDEX IF NOT EXISTS idx_inspections_lot_id ON lot_quality_inspections(lot_id);
CREATE INDEX IF NOT EXISTS idx_inspections_type ON lot_quality_inspections(inspection_type);
CREATE INDEX IF NOT EXISTS idx_inspections_date ON lot_quality_inspections(inspection_date);
CREATE INDEX IF NOT EXISTS idx_inspections_grade ON lot_quality_inspections(assigned_grade);

-- =============================================================================
-- ロット管理用トリガー
-- =============================================================================

-- lotsテーブル更新日時自動更新
CREATE TRIGGER IF NOT EXISTS update_lots_timestamp 
    AFTER UPDATE ON lots
    BEGIN
        UPDATE lots SET updated_at = CURRENT_TIMESTAMP WHERE lot_id = NEW.lot_id;
    END;

-- 在庫数量整合性チェック（在庫移動時）
CREATE TRIGGER IF NOT EXISTS validate_inventory_transaction 
    BEFORE INSERT ON inventory_transactions
    BEGIN
        -- 変更後数量の整合性チェック
        SELECT CASE 
            WHEN NEW.quantity_before + NEW.quantity_change != NEW.quantity_after THEN
                RAISE(ABORT, '数量計算が一致しません: before + change != after')
        END;
        
        -- 負の在庫チェック
        SELECT CASE 
            WHEN NEW.quantity_after < 0 AND NEW.transaction_type != 'ADJUSTMENT' THEN
                RAISE(ABORT, '在庫数量が負になります')
        END;
    END;

-- ロット消費時の自動在庫更新
CREATE TRIGGER IF NOT EXISTS auto_update_lot_quantity 
    AFTER INSERT ON inventory_transactions
    WHEN NEW.transaction_type IN ('CONSUMPTION', 'SCRAP', 'TRANSFER')
    BEGIN
        UPDATE lots 
        SET current_quantity = NEW.quantity_after,
            lot_status = CASE 
                WHEN NEW.quantity_after <= 0 THEN 'consumed'
                ELSE lot_status
            END
        WHERE lot_id = NEW.lot_id;
    END;

-- =============================================================================
-- 基本マスタデータの挿入
-- =============================================================================

-- 工程ステップマスタデータ
INSERT OR IGNORE INTO process_steps (process_code, process_name, process_level, typical_unit, accuracy_type, description) VALUES
('P', 'PS工程', 2, 'KG', '概算', '原糸の延伸・配向処理'),
('W', 'Winder工程', 3, 'M', '近似', '木管への巻き取り'),
('B', 'Braid工程', 4, 'M', '近似', '製紐・編み込み'),
('S', 'Sensor工程', 5, 'M', '実測', 'センサーによる長さ測定'),
('C', '染色工程', 6, 'M', '近似', '染色処理'),
('T', '後PS工程', 7, 'M', '近似', '染色後の延伸処理'),
('E', 'Spool工程', 8, 'M', '実測', 'スプールへの巻き取り'),
('F', '完成品工程', 9, '個', '実測', '最終製品化・梱包');

-- 品質グレードマスタデータ
INSERT OR IGNORE INTO quality_grades (grade_code, grade_name, grade_description, processing_rule, is_usable_for_next_process) VALUES
('A', '合格品', '規格内の標準品質', '原則、下位工程へ投入可', TRUE),
('A0', '軽微難品', '軽微な品質問題があるが使用可能', '自社使用優先', TRUE),
('B', '代用品', 'グレードダウンしたが特定用途で使用可能', '芯糸専用／要ラベル色替', TRUE),
('S', '端下品', '規格外品・副産物', '自動廃棄 or 指定回収ロット', FALSE); 