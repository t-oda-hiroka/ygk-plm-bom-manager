-- 釣り糸製造BOM管理システム データベーススキーマ


-- アイテムマスタテーブル
CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,
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
    
    -- 材料属性
    material_type TEXT,       -- EN, SK, AL等
    denier INTEGER,           -- デニール
    ps_ratio REAL,            -- PS値
    braid_structure TEXT,     -- x4, x8等の編み構造
    has_core BOOLEAN,         -- 芯糸有無
    color TEXT,               -- 色
    length_m INTEGER,         -- 標準長さ(m)
    twist_type TEXT CHECK (twist_type IN ('S', 'Z', NULL)), -- 撚り方向
    
    -- 追加属性をJSONで柔軟に格納
    additional_attributes TEXT, -- JSON形式で追加属性を保存
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BOM構成テーブル
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
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外部キー制約
    FOREIGN KEY (parent_item_id) REFERENCES items(item_id),
    FOREIGN KEY (component_item_id) REFERENCES items(item_id),
    
    -- ユニーク制約（同じ親に対して同じ構成部品が同じ用途で重複しないように）
    UNIQUE(parent_item_id, component_item_id, usage_type)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type);
CREATE INDEX IF NOT EXISTS idx_items_material ON items(material_type);
CREATE INDEX IF NOT EXISTS idx_bom_parent ON bom_components(parent_item_id);
CREATE INDEX IF NOT EXISTS idx_bom_component ON bom_components(component_item_id);

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