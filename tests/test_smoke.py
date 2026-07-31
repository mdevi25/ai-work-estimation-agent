import ast
from pathlib import Path

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_app_file_exists():
    assert APP_PATH.exists()


def test_app_is_valid_python():
    source = APP_PATH.read_text(encoding="utf-8")
    ast.parse(source)
