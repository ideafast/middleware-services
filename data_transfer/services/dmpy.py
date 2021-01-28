from pathlib import Path
import shutil


def zip_folder(path: Path) -> Path:
    return Path(shutil.make_archive(path, 'zip', path))


def upload(path: Path) -> bool:
    return True


def rm_local_data(zip_path: Path) -> None:
    zip_path.unlink()
    shutil.rmtree(zip_path.with_suffix(''))