## Local Model Upload - Quick Start

### One-Sentence Summary
Users can now upload local models to the model zoo via the Streamlit UI, and they'll be automatically available for evolution alongside HuggingFace models.

### How It Works

**In the Streamlit UI:**

1. **Navigate to:** Evolution tab → Base Models section
2. **Expand:** "📤 Upload Local Model" expander
3. **Fill in:**
   - **Local path:** `/path/to/your/model/` (must contain `config.json`)
   - **Display name:** `my-model-name` (shows in dropdown)
   - **Description:** Optional metadata
4. **Click:** "🚀 Transfer Model"
5. **Result:** Model copied to `breeding_vat/data/model_zoo/` and available immediately

### File Structure Requirements

Your local model must have:
```
my-finetuned-model/
├── config.json              (REQUIRED)
├── model.safetensors        (or .bin file)
├── tokenizer.json
├── tokenizer_config.json
└── ...other files
```

### What Happens

1. **Transfer:** Model copied to `breeding_vat/data/model_zoo/my-model-name/`
2. **Metadata:** Creates `.model_metadata.json` with source, size, timestamp
3. **Preservation:** Original model on disk never modified
4. **Availability:** Appears in "Base Models" dropdown immediately
5. **Evolution:** Can be mixed with HuggingFace models in merges

### Example Flow

```
Sidebar → New Mission
├─ Goal: "Merge my-finetuned with Qwen"
└─ Initialize

Evolution Tab → Base Models
├─ Upload Local Model:
│  ├─ Path: /Users/me/finetuned-7b/
│  ├─ Name: my-7b-finetuned
│  └─ Transfer → Success!
│
├─ Select models:
│  ├─ my-7b-finetuned (local)
│  └─ Qwen/Qwen2.5-3B-Instruct (HF)
│
└─ Start Evolution
   └─ Creates: mutant_c1_p0_sl
      (merged from both)
```

### Key Features

✅ **Local models preserved** - Original never modified  
✅ **Mixed merges** - Local + HuggingFace in same experiment  
✅ **Full lineage** - Genealogy tracks local model origins  
✅ **Real-time validation** - Path check before transfer  
✅ **Size tracking** - Metadata records model size (GB)  
✅ **Reusable** - Once uploaded, available for all future experiments  

### Troubleshooting

| Problem | Fix |
|---------|-----|
| Upload fails - "Path not found" | Check the directory exists and path is correct |
| Validation shows "No model config found" | Ensure `config.json` exists in the directory |
| Model not appearing in dropdown | Refresh the page or check permissions on model zoo |
| Transfer seems stuck | Large models (7B+) may take 1-5 min depending on storage speed |

### For Developers

**Classes used:**
- `ModelTransfer` - Handles registration and validation
- `ModelPathResolver` - Converts model names/IDs to paths
- Integrated into existing `AdvancedMerger` via resolver

**No changes needed** to merge engines - path resolution is transparent.

---

**Merged into:** `breeding_vat/ui/app.py` Evolution tab  
**Data stored in:** `breeding_vat/data/model_zoo/`  
**Metadata:** `.model_metadata.json` per model  
**Original:** Never modified (safe for comparison)
