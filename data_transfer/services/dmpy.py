from pathlib import Path
import shutil


def zip_folder(path: Path) -> str:
    return shutil.make_archive(path, 'zip', path)


def upload(path: Path) -> bool:
    return False


def rm_local_data(path: Path):
    pass