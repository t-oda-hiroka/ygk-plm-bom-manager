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