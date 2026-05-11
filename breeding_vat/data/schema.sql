-- Experiments: Top-level grouping for runs
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    goal TEXT,
    base_models TEXT, -- JSON array
    merge_methods TEXT, -- JSON array
    num_cycles_planned INTEGER,
    cycles_completed INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress', -- in_progress, completed, paused, failed
    best_model_id INTEGER,
    best_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (best_model_id) REFERENCES models(id)
);

-- Models: Individual merged models within an experiment
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER,
    name TEXT NOT NULL,
    base_models TEXT, -- JSON list of base model names/paths
    recipe_path TEXT,
    benchmark_results TEXT, -- JSON blob of scores
    lineage_parent_id INTEGER,
    status TEXT DEFAULT 'pending',
    cycle_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id),
    FOREIGN KEY (lineage_parent_id) REFERENCES models(id)
);

-- Recipes: Merge configurations
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER,
    experiment_id INTEGER,
    method TEXT,
    config TEXT, -- JSON blob of merge/mutation parameters
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

-- SAE Discoveries: Interpretability findings
CREATE TABLE IF NOT EXISTS sae_discoveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER,
    experiment_id INTEGER,
    layer_index INTEGER,
    feature_description TEXT,
    geometric_shape TEXT,
    importance_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);
