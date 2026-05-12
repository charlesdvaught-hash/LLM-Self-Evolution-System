# Documentation Index

Welcome to **The Breeding Vat** documentation. All guides and technical references are organized below.

## 📍 Start Here

- **[README.md](../README.md)** - Project overview and quick start
- **[ADVISOR_KNOWLEDGE_BASE.md](guides/ADVISOR_KNOWLEDGE_BASE.md)** - For the 0.8B advisor model (and advanced users)

## 🎯 By Use Case

### I want to upload and use my own model
1. **Read**: [LOCAL_MODEL_UPLOAD_QUICKSTART.md](guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md) (5 min)
2. **Deep dive**: [LOCAL_MODEL_UPLOAD_GUIDE.md](guides/LOCAL_MODEL_UPLOAD_GUIDE.md) (20 min)

### I want to understand merge methods
1. **Quick overview**: [FUSIONBENCH_QUICKSTART.md](guides/FUSIONBENCH_QUICKSTART.md) (10 min)
2. **Complete reference**: [reference/MERGING_METHODS_INVENTORY.md](reference/MERGING_METHODS_INVENTORY.md) (30 min)

### I want to understand the system
- **Read**: [reference/Architecture.md](reference/Architecture.md) (30 min)

### I want to use specialized models
- **Available models**: [reference/SPECIALIZED_MODELS.md](reference/SPECIALIZED_MODELS.md)
- **Model storage**: [reference/MODEL_ZOO.md](reference/MODEL_ZOO.md)

### I want to analyze models with SAE
- **Quick intro**: [reference/SAE_GUIDE.md](reference/SAE_GUIDE.md)
- **Memory optimization**: [reference/SAE_MEMORY_OPTIMIZATION.md](reference/SAE_MEMORY_OPTIMIZATION.md)

### I want to build advanced MoE models
- **Read**: [guides/MOE_GUIDE.md](guides/MOE_GUIDE.md)

---

## 📚 All Documentation

### Guides (How-To & Tutorials)

| File | Purpose | Time |
|---|---|---|
| [guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md](guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md) | Quick start for uploading local models | 5 min |
| [guides/LOCAL_MODEL_UPLOAD_GUIDE.md](guides/LOCAL_MODEL_UPLOAD_GUIDE.md) | Complete local model integration guide | 20 min |
| [guides/FUSIONBENCH_QUICKSTART.md](guides/FUSIONBENCH_QUICKSTART.md) | Overview of 20+ merge methods | 10 min |
| [guides/MOE_GUIDE.md](guides/MOE_GUIDE.md) | Building Mixture-of-Experts models | 20 min |
| [guides/ADVISOR_KNOWLEDGE_BASE.md](guides/ADVISOR_KNOWLEDGE_BASE.md) | Knowledge base for 0.8B advisor (also useful for advanced users) | 15 min |

### Reference (Technical Details)

| File | Purpose | Depth |
|---|---|---|
| [reference/Architecture.md](reference/Architecture.md) | Complete system architecture and design | Deep |
| [reference/MERGING_METHODS_INVENTORY.md](reference/MERGING_METHODS_INVENTORY.md) | All 20+ merge methods with parameters | Reference |
| [reference/SPECIALIZED_MODELS.md](reference/SPECIALIZED_MODELS.md) | Available base models for merging | Reference |
| [reference/MODEL_ZOO.md](reference/MODEL_ZOO.md) | Model storage structure and preservation strategy | Reference |
| [reference/SAE_GUIDE.md](reference/SAE_GUIDE.md) | Sparse Autoencoder layer introspection | Technical |
| [reference/SAE_MEMORY_OPTIMIZATION.md](reference/SAE_MEMORY_OPTIMIZATION.md) | Memory-efficient SAE techniques | Technical |

---

## 🔍 Search by Topic

### Local Models
- [LOCAL_MODEL_UPLOAD_QUICKSTART.md](guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md) - How to upload
- [LOCAL_MODEL_UPLOAD_GUIDE.md](guides/LOCAL_MODEL_UPLOAD_GUIDE.md) - Complete guide
- [reference/MODEL_ZOO.md](reference/MODEL_ZOO.md) - Storage strategy

### Merge Methods & Merging
- [FUSIONBENCH_QUICKSTART.md](guides/FUSIONBENCH_QUICKSTART.md) - Overview
- [reference/MERGING_METHODS_INVENTORY.md](reference/MERGING_METHODS_INVENTORY.md) - All methods
- [reference/Architecture.md](reference/Architecture.md) - How merging works

### Models & Selection
- [reference/SPECIALIZED_MODELS.md](reference/SPECIALIZED_MODELS.md) - Available models
- [reference/MODEL_ZOO.md](reference/MODEL_ZOO.md) - Model management
- [LOCAL_MODEL_UPLOAD_GUIDE.md](guides/LOCAL_MODEL_UPLOAD_GUIDE.md) - Custom models

### System & Architecture
- [reference/Architecture.md](reference/Architecture.md) - Complete system design
- [reference/MODEL_ZOO.md](reference/MODEL_ZOO.md) - Data organization
- [ADVISOR_KNOWLEDGE_BASE.md](guides/ADVISOR_KNOWLEDGE_BASE.md) - System overview

### Advanced Topics
- [guides/MOE_GUIDE.md](guides/MOE_GUIDE.md) - Mixture of Experts
- [reference/SAE_GUIDE.md](reference/SAE_GUIDE.md) - Layer analysis
- [reference/SAE_MEMORY_OPTIMIZATION.md](reference/SAE_MEMORY_OPTIMIZATION.md) - Optimization

---

## 📂 File Structure

```
docs/
├── INDEX.md                                  ← You are here
├── KNOWLEDGE_BASE_MANIFEST.json              ← Machine-readable index
├── guides/
│   ├── ADVISOR_KNOWLEDGE_BASE.md             ← For 0.8B advisor model
│   ├── LOCAL_MODEL_UPLOAD_QUICKSTART.md
│   ├── LOCAL_MODEL_UPLOAD_GUIDE.md
│   ├── FUSIONBENCH_QUICKSTART.md
│   └── MOE_GUIDE.md
└── reference/
    ├── Architecture.md
    ├── MERGING_METHODS_INVENTORY.md
    ├── SPECIALIZED_MODELS.md
    ├── MODEL_ZOO.md
    ├── SAE_GUIDE.md
    └── SAE_MEMORY_OPTIMIZATION.md
```

---

## 🤖 For the 0.8B Advisor Model

The advisor uses:
1. **[KNOWLEDGE_BASE_MANIFEST.json](KNOWLEDGE_BASE_MANIFEST.json)** - Machine-readable index
2. **[guides/ADVISOR_KNOWLEDGE_BASE.md](guides/ADVISOR_KNOWLEDGE_BASE.md)** - Decision tree and reference guide

The manifest provides:
- Topic-to-file mapping
- Quick answer lookups
- Search index by topic
- Advisor prompts for recommendations

---

## 🚀 Quick Navigation

**Just want to get started?**
→ [LOCAL_MODEL_UPLOAD_QUICKSTART.md](guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md)

**Want a detailed guide?**
→ [LOCAL_MODEL_UPLOAD_GUIDE.md](guides/LOCAL_MODEL_UPLOAD_GUIDE.md)

**Need merge method options?**
→ [FUSIONBENCH_QUICKSTART.md](guides/FUSIONBENCH_QUICKSTART.md)

**Want to understand everything?**
→ [reference/Architecture.md](reference/Architecture.md)

**Are you the 0.8B advisor?**
→ [guides/ADVISOR_KNOWLEDGE_BASE.md](guides/ADVISOR_KNOWLEDGE_BASE.md)

---

## 📋 Document Metadata

| File | Type | Audience | Length |
|---|---|---|---|
| LOCAL_MODEL_UPLOAD_QUICKSTART.md | Guide | Users | ~3KB |
| LOCAL_MODEL_UPLOAD_GUIDE.md | Guide | Users/Devs | ~9KB |
| FUSIONBENCH_QUICKSTART.md | Guide | Users | ~5KB |
| MOE_GUIDE.md | Guide | Advanced Users | ~7KB |
| ADVISOR_KNOWLEDGE_BASE.md | Guide | Advisor/Advanced | ~9KB |
| Architecture.md | Reference | Developers | ~15KB |
| MERGING_METHODS_INVENTORY.md | Reference | Reference | ~10KB |
| SPECIALIZED_MODELS.md | Reference | Users | ~5KB |
| MODEL_ZOO.md | Reference | Reference | ~5KB |
| SAE_GUIDE.md | Reference | Advanced | ~6KB |
| SAE_MEMORY_OPTIMIZATION.md | Reference | Advanced | ~7KB |

---

**Last Updated**: January 15, 2025  
**Total Documentation**: 11 guides + references + manifest  
**Status**: Complete and organized
