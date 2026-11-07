"""Ашық деректер жиындарын жүктеу көмекшісі (интернет қажет).

Жұмыс істемесе, сілтемелерден қолмен жүктеп, data/raw/ ішіне салыңыз:
  SMS:  https://archive.ics.uci.edu/dataset/228/sms+spam+collection
  URL:  https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset

Пайдалану:  python -m ml.data.download_datasets sms|url
"""
import sys
import urllib.request
import zipfile
from datetime import date

from .paths import RAW

SOURCES = {
    "sms": "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
    "url": "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip",
}


def download(kind: str) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    url = SOURCES[kind]
    target = RAW / f"{kind}_dataset.zip"
    print(f"Жүктеу: {url}")
    urllib.request.urlretrieve(url, target)
    with zipfile.ZipFile(target) as zf:
        zf.extractall(RAW)
        print("Шығарылды:", ", ".join(zf.namelist()))
    print(f"Жүктелген күні (паспортқа жазыңыз): {date.today().isoformat()}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SOURCES:
        sys.exit(__doc__)
    download(sys.argv[1])
