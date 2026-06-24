"""Verify Sanhedrin 43a Yeshu in export vs API after alignment fix."""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib.sefaria import export_gemara_hebrew


def flat(node) -> str:
    if isinstance(node, list):
        return " ".join(str(x) for x in node)
    return str(node)


def main() -> None:
    data = export_gemara_hebrew("Seder Nezikin", "Sanhedrin")
    idx = 84  # 43a with header offset 2
    exp = flat(data["text"][idx])
    ref = urllib.parse.quote("Sanhedrin.43a", safe=".")
    api = json.load(
        urllib.request.urlopen(
            f"https://www.sefaria.org/api/texts/{ref}?context=0", timeout=120
        )
    )
    api_text = " ".join(api.get("he") or [])
    out = Path(__file__).resolve().parents[1] / "data/reports/sanhedrin_43a.txt"
    out.write_text(
        f"export[84] has Yeshu: {'יֵשׁוּ' in exp}\n"
        f"API 43a has Yeshu: {'יֵשׁוּ' in api_text}\n"
        f"export len: {len(exp)}\n"
        f"api len: {len(api_text)}\n"
        f"same start: {exp[:200] == api_text[:200]}\n",
        encoding="utf-8",
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
