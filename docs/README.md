# Documentation - The Breeding Vat

Welcome to the complete documentation for **The Breeding Vat** LLM evolution engine.

## 🚀 Quick Start

- **New user?** → Start with `../README.md` then go to `guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md`
- **0.8B Advisor?** → Start with `guides/ADVISOR_KNOWLEDGE_BASE.md`
- **Looking for something?** → See `INDEX.md` for complete navigation

## 📂 Structure

```
docs/
├── INDEX.md                          # Complete navigation & search
├── KNOWLEDGE_BASE_MANIFEST.json      # Machine-readable index (for advisor)
├── advisor_kb_loader.py              # Python API for advisor to access docs
├── guides/                           # How-to guides
│   ├── LOCAL_MODEL_UPLOAD_QUICKSTART.md
│   ├── LOCAL_MODEL_UPLOAD_GUIDE.md
│   ├── FUSIONBENCH_QUICKSTART.md
│   ├── MOE_GUIDE.md
│   └── ADVISOR_KNOWLEDGE_BASE.md     # Knowledge base guide (for advisor/advanced users)
└── reference/                        # Technical references
    ├── Architecture.md
    ├── MERGING_METHODS_INVENTORY.md
    ├── SPECIALIZED_MODELS.md
    ├── MODEL_ZOO.md
    ├── SAE_GUIDE.md
    └── SAE_MEMORY_OPTIMIZATION.md
```

## 📖 Documentation Overview

### Guides (How-To)
- **LOCAL_MODEL_UPLOAD_QUICKSTART.md** - Get started uploading models in 5 minutes
- **LOCAL_MODEL_UPLOAD_GUIDE.md** - Complete integration guide with technical details
- **FUSIONBENCH_QUICKSTART.md** - Overview of all 20+ merge methods
- **MOE_GUIDE.md** - Advanced: Building Mixture-of-Experts models
- **ADVISOR_KNOWLEDGE_BASE.md** - Navigation guide for the advisor system

### Reference (Technical)
- **Architecture.md** - Complete system design, components, and data flow
- **MERGING_METHODS_INVENTORY.md** - All 20+ methods with parameters
- **SPECIALIZED_MODELS.md** - Available base models for merging
- **MODEL_ZOO.md** - Model storage strategy and preservation
- **SAE_GUIDE.md** - Sparse Autoencoder layer analysis
- **SAE_MEMORY_OPTIMIZATION.md** - Memory efficiency techniques

## 🤖 For the 0.8B Advisor Model

The advisor can access documentation via:

1. **KNOWLEDGE_BASE_MANIFEST.json** - Machine-readable index with:
   - Topic-to-file mappings
   - Quick answer lookups
   - Search index by topic
   - Advisor prompt guidance

2. **advisor_kb_loader.py** - Python API:
   ```python
   from docs.advisor_kb_loader import get_kb
   
   kb = get_kb()
   
   # Find a guide
   path = kb.get_guide('local_models')[0]
   
   # Get quick answer
   answer = kb.get_quick_answer('how_to_upload_model')
   
   # Search by topic
   files = kb.search_by_topic('merge')
   
   # Read file content
   content = kb.read_file('guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md')
   ```

3. **ADVISOR_KNOWLEDGE_BASE.md** - Navigation guide with:
   - Decision tree for finding information
   - Common questions and where to find answers
   - Best practices for recommendations

## 🔍 Find What You Need

**By topic:**
- Local models → `guides/LOCAL_MODEL_UPLOAD_*.md` + `reference/MODEL_ZOO.md`
- Merge methods → `guides/FUSIONBENCH_QUICKSTART.md` + `reference/MERGING_METHODS_INVENTORY.md`
- System design → `reference/Architecture.md`
- Available models → `reference/SPECIALIZED_MODELS.md`
- Advanced SAE → `reference/SAE_*.md`
- Advanced MoE → `guides/MOE_GUIDE.md`

**By audience:**
- Users → Start in `guides/` (how-to documents)
- Developers → See `reference/` (technical documents)
- Advisor → See `ADVISOR_KNOWLEDGE_BASE.md` + `KNOWLEDGE_BASE_MANIFEST.json`

**By task:**
- Upload model → `guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md`
- Choose merge method → `guides/FUSIONBENCH_QUICKSTART.md`
- Understand system → `reference/Architecture.md`
- Analyze layers → `reference/SAE_GUIDE.md`

## 📋 Complete Index

See **INDEX.md** for:
- All documents with descriptions
- Use-case navigation
- Topic-based search
- Time estimates per document

## ✅ What's Here

✅ **5 How-To Guides** - From quickstart to advanced  
✅ **6 Technical References** - Complete system documentation  
✅ **Machine-readable Index** - For programmatic access  
✅ **Python API** - Easy access for the advisor model  
✅ **Navigation Guide** - For finding specific information  

## 📞 Need Help?

1. **Start here:** See `INDEX.md` for navigation
2. **Quick lookup:** Use `KNOWLEDGE_BASE_MANIFEST.json` (machine-readable)
3. **Python access:** Use `advisor_kb_loader.py` (programmatic)
4. **Manual search:** Browse `guides/` for how-to, `reference/` for technical

---

**Status**: Complete and organized  
**Last Updated**: January 15, 2025  
**Total Files**: 11 + manifest + loader API
