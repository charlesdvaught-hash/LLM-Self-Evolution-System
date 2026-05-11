CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    base_models TEXT, -- JSON list of base model names/paths
    recipe_path TEXT,
    benchmark_results TEXT, -- JSON blob of scores
    lineage_parent_id INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lineage_parent_id) REFERENCES models(id)
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER,
    method TEXT,
    config TEXT, -- JSON blob of merge/mutation parameters
    notes TEXT,
    FOREIGN KEY (model_id) REFERENCES models(id)
);

CREATE TABLE IF NOT EXISTS sae_discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER,
    layer_index INTEGER,
    feature_description TEXT,
    geometric_shape TEXT,
    importance_score REAL,
    FOREIGN KEY (model_id) REFERENCES models(id)
);
