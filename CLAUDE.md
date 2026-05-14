# Breeding Vat — CLAUDE.md
## Session Notes & Standing Instructions

---

## 📚 Documentation Index & Current State

**Most Up-To-Date References** (as of May 14, 2026):

| Document | Version | Freshness | Scope |
|----------|---------|-----------|-------|
| `SOURCE_OF_TRUTH.md` | 2.0 | ✅ FINAL | Authoritative spine, simulation mode, handoff guide. |
| `Map.json` | 3.0 | ✅ Current | Complete file inventory + recent changes. |
| `DESIGN_PHILOSOPHY.md` | 1.0 | ✅ Stable | Fabricator lab aesthetic and intent. |
| `docs/developer_handover/` | 1.0 | ✅ NEW | Emulation guide and codebase knowledge mapping. |

---

## Hard Constraints (never override without explicit user confirmation)

- **Options-first**: every new feature is opt-in, never a new default. Checkboxes, not auto-behaviors.
- **Code out of sight**: \`setup.bat\` installs, \`run.bat\` starts, everything else via Streamlit UI + AI assistants.
- **GPU work via Docker-out-of-Docker**: UI container is CPU-oriented; heavy inference hits a GPU container.
- **Simulation Mode**: Set \`SIMULATION_MODE=true\` to debug logic on low-end hardware.
- **Model Linking**: Use symlinks (\`use_symlink=True\`) in ModelTransfer to avoid drive duplication.

---

## SYSTEM STATUS: CLEAN & VERIFIED

### Functional Core
- **Evolution Loop**: Verified via simulated smoke test (2 cycles, full genealogy tracking).
- **Merge Engines**: MergeKit and FusionBench backends verified.
- **Advanced Toggles**: All 11 toggles verified functional in MergekitConfigBuilder.
- **ML Stack**: Real micro-merge verified functional with Pydantic patch.

---

## Pending Work — HANDOFF PRIORITIES

### PHASE 1: UI Polish
- [ ] Implement progress bars for individual merge tasks in the UI.
- [ ] Add visualization for the "Second Chances" culling logic.

### PHASE 2: Containerization
- [ ] Build and verify \`vat-finetune\` image with the provided \`finetune_runner.py\` stub.
- [ ] Test container-to-host symlink following for linked models.

---

## ⚠️ Important Note for Local Agents
- The \`TaskRunner\` is the single point of entry for container orchestration.
- Use \`scripts/mergekit_wrapper.py\` to apply the Pydantic patch if running MergeKit outside the official Docker image.
