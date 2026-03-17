import os
import sqlite3
import time
from datetime import datetime, timedelta
from PIL import Image
import tempfile
import shutil

import pytest
import streamlit

# ensure project path
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from download_module import (
    prepare_image_for_download,
    save_download_metadata,
    delete_old_files,
    DB_NAME,
)


def make_image(size=(50, 40), color=(123, 222, 100)):
    return Image.new("RGB", size, color)


def test_prepare_png_with_watermark_and_session(tmp_path, monkeypatch):
    img = make_image()
    # clear session state
    monkeypatch.setattr('streamlit.session_state', {}, raising=False)
    result = prepare_image_for_download(
        img,
        user_id=5,
        image_id=42,
        style="test",
        original_filename="photo.png",
        format_type="PNG",
        quality_mode="high",
        is_premium_user=False,
    )
    assert result["success"] is True
    path = result["path"]
    assert os.path.isfile(path)
    # check extension
    assert path.endswith(".png")
    # watermark should have been added; file should be non-empty
    with Image.open(path) as out_img:
        assert out_img.size == img.size
    # session path set
    assert "download_path" in streamlit.session_state
    assert streamlit.session_state["download_path"] == path

    # cleanup - remove file only
    try:
        os.remove(path)
    except Exception:
        pass


def test_prepare_jpg_quality_modes(tmp_path):
    img = make_image()
    # call twice with different quality modes
    result_high = prepare_image_for_download(
        img,
        user_id=1,
        image_id=1,
        style="s",
        original_filename="name.jpg",
        format_type="JPG",
        quality_mode="high",
        is_premium_user=True,
    )
    assert result_high['success']
    path_high = result_high['path']
    assert path_high.endswith('.jpg')

    result_opt = prepare_image_for_download(
        img,
        user_id=1,
        image_id=1,
        style="s",
        original_filename="name.jpg",
        format_type="JPG",
        quality_mode="optimized",
        is_premium_user=True,
    )
    assert result_opt['success']
    path_opt = result_opt['path']
    assert path_opt.endswith('.jpg')

    # cleanup created files - remove the two jpgs
    try:
        os.remove(path_high)
    except Exception:
        pass
    try:
        os.remove(path_opt)
    except Exception:
        pass


def test_numpy_array_input(tmp_path):
    # ensure numpy arrays are accepted as image input
    import numpy as np

    array = np.zeros((20, 30, 3), dtype=np.uint8) + 50
    result = prepare_image_for_download(
        array,
        user_id=7,
        image_id=8,
        style="test",
        original_filename="arr.png",
        format_type="PNG",
        quality_mode="high",
        is_premium_user=True,
    )
    assert result["success"]
    assert os.path.isfile(result["path"])
    # cleanup
    os.remove(result["path"])


def test_save_download_metadata_creates_table(tmp_path):
    # ensure fresh db
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    save_download_metadata(2, 3, "style", "file.png")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, image_id, style, filename FROM ImageHistory")
    row = cur.fetchone()
    assert row[0] == 2
    assert row[1] == 3
    assert row[2] == "style"
    assert row[3] == "file.png"
    conn.close()


def test_delete_old_files(tmp_path):
    folder = tmp_path / "downloads"
    folder.mkdir()
    old = folder / "old.png"
    new = folder / "new.png"
    old.write_text("data")
    new.write_text("data")
    # set modification times
    old_time = datetime.now() - timedelta(hours=25)
    os.utime(old, (old_time.timestamp(), old_time.timestamp()))
    # new remains current

    delete_old_files(str(folder))
    assert not old.exists()
    assert new.exists()
