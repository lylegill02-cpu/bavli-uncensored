"""Check Sanhedrin 67a content on API."""
import json
import urllib.parse
import urllib.request
from pathlib import Path

ref = urllib.parse.quote("Sanhedrin.67a", safe=".")
data = json.load(
    urllib.request.urlopen(
        f"https://www.sefaria.org/api/texts/{ref}?context=0", timeout=120
    )
)
text = " ".join(data.get("he") or [])
Path("data/reports/sanhedrin_67a_api.txt").write_text(
    f"len={len(text)}\n"
    f"has שטada: {'שׁטָדָא' in text}\n"
    f"has pandera: {'פַּנְדֵּרָא' in text}\n"
    f"snippet: {text[2000:2800]}\n",
    encoding="utf-8",
)
print("done")
