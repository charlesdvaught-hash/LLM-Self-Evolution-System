# UI Selection on Launch

**Status**: Updated - run.bat now asks which UI to use

---

## What Changed

When you run `run.bat`, it now prompts you to choose which UI to launch:

```
[*] Choose UI version:

   1. NEW: Dual-Mode (Granular + Exploratory AI) - RECOMMENDED
      - Granular control OR AI orchestration
      - Resource transparency (see model count before running)
      - New cleanup tools

   2. Previous: Sleek Dark Theme
      - Broad-stroke calibration
      - Clean 5-tab layout

   3. Original: Classic Breeding Vat
      - Original version (app_original_backup.py)

Select (1-3, default=1):
```

---

## How It Works

1. **Default (1)**: Uses the new dual-mode app (`breeding_vat/ui/app.py`)
2. **Previous (2)**: Uses the sleek UI (`breeding_vat/ui/app_v2_revamped.py`)
3. **Original (3)**: Uses the original version (`breeding_vat/ui/app_original_backup.py`)

Just select a number or press Enter for default (new dual-mode).

---

## Files Modified

**run.bat**
- Added UI choice prompt
- Shows descriptions for each option
- Passes selected UI to manager.py

**scripts/manager.py**
- `run_ui()` function now accepts `ui_file` parameter
- Manager passes UI file to Docker via `STREAMLIT_APP_FILE` environment variable
- Works with existing container detection

**docker/Dockerfile.ui**
- Updated CMD to use `$STREAMLIT_APP_FILE` environment variable
- Falls back to default if not provided

---

## Usage

```bash
# Launch normally
run.bat

# Will ask you to choose:
# 1 = New dual-mode (default)
# 2 = Previous sleek version
# 3 = Original version
```

**That's it!** Select your preference each time you launch.

---

## Under the Hood

```
run.bat
  ↓ (asks for UI choice)
  ↓ (passes to manager.py)
scripts/manager.py run [ui_file]
  ↓ (sets STREAMLIT_APP_FILE env var)
  ↓ (docker run -e STREAMLIT_APP_FILE=...)
docker/Dockerfile.ui
  ↓ (uses env var in CMD)
  ↓ streamlit run /app/$STREAMLIT_APP_FILE
  ↓
Launches selected UI on http://localhost:8501
```

---

## Available UIs

| Name | File | Notes |
|------|------|-------|
| **NEW Dual-Mode** | `breeding_vat/ui/app.py` | Granular + Exploratory (default) |
| **Sleek v2** | `breeding_vat/ui/app_v2_revamped.py` | Dark theme, broad-stroke |
| **Original** | `breeding_vat/ui/app_original_backup.py` | Reference/fallback |

---

**All UIs use the same Docker container and infrastructure. Only the Streamlit app file changes.**
