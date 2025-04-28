# test_i18n_fr.py
# ────────────────────────────────────────────────────────────────────
# Run with:  python test_i18n_fr.py
# Make sure your project tree is:
#
#   your_project/
#   ├─ data/
#   │   └─ translations/
#   │       └─ fr.json
#   └─ test_i18n_fr.py   ← this file
# ────────────────────────────────────────────────────────────────────

import pathlib
import json
import i18n
import sys

# 1.  Directory that holds fr.json  (adjust if needed)
BASE_DIR = pathlib.Path(__file__).parent
LOCALE_DIR = BASE_DIR / "data" / "translations"

# 2.  Configure python-i18n for JSON files called "<locale>.json"
i18n.load_path.clear()
i18n.load_path.append(str(LOCALE_DIR))
i18n.set("file_format", "json")                # we use JSON, not YAML
i18n.set("filename_format", "{locale}.{format}")  # look for fr.json, en.json …
i18n.set("locale", "fr")                       # active language
i18n.set("fallback", "en")                     # English fallback
i18n.set("deep_key_transformer", lambda k: k)  # keep keys verbatim

# 3.  Make sure the file exists
fr_file = LOCALE_DIR / "fr.json"
if not fr_file.exists():
    sys.exit(f"❌  File not found: {fr_file}")

# 4.  Force-load the translation file (first .t() does that)
i18n.t("dummy")

# 5.  Read keys from the JSON so we can iterate cleanly
with open(fr_file, encoding="utf-8") as fh:
    fr_dict = json.load(fh)

print(f"\n✅ Loaded {len(fr_dict)} keys from {fr_file}:\n")

# 6.  Print each key and its translated value
for key in fr_dict["fr"]:
    print(f"{key:45} →  {i18n.t(key)}")

print("\nFinished.")
