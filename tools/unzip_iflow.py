import argparse
import zipfile
from pathlib import Path

INPUT_DIR = Path(__file__).parent.parent / "input"
TMP_DIR = Path(__file__).parent.parent / "tmp"


def unzip_iflow(filename: str) -> None:
    zip_path = INPUT_DIR / filename
    if not zip_path.exists():
        raise FileNotFoundError(f"Not found in input/: {filename}")

    extract_dir = TMP_DIR / zip_path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
        extracted = zf.namelist()

    print(f"Extracted to tmp/{zip_path.stem}/")
    for name in extracted:
        print(f"  {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unzip an iFlow export from input/ into tmp/")
    parser.add_argument("filename", help="Zip filename inside input/ (e.g. MyFlow.zip)")
    args = parser.parse_args()
    unzip_iflow(args.filename)
