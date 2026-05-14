-- Experimental Evolution Schema

CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    goal TEXT,
    base_models TEXT, -- JSON list
    merge_methods TEXT, -- JSON list
    num_cycles_planned INTEGER,
    cycles_completed INTEGER DEFAULT 0,
    best_score REAL DEFAULT 0.0,
    best_model TEXT,
    status TEXT DEFAULT 'active', -- active, completed, paused, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata TEXT -- JSON blob
);

CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    base_models TEXT, -- JSON list of parents
    recipe_path TEXT,
    lineage_parent_id INTEGER,
    method TEXT,
    score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'pending', -- pending, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    experiment_id INTEGER,
    anomalies TEXT, -- JSON list
    FOREIGN KEY (lineage_parent_id) REFERENCES models(id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    content TEXT, -- JSON recipe
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sae_discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER,
    layer_index INTEGER,
    discovery_type TEXT, -- specialized, sparse, variance_peak
    metadata TEXT, -- JSON results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id)
);
