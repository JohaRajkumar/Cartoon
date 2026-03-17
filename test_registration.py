
import os
import sqlite3
import pytest

from registration import register_user, login_user
from database import DB_NAME, create_tables


def setup_module(module):
    # ensure a fresh database for tests
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    create_tables()


def test_register_success():
    success, msg = register_user(
        username="testuser1",
        email="testuser1@gmail.com",
        password="Strong@123"
    )
    assert success
    assert "successful" in msg.lower()


def test_duplicate_email():
    # second registration with same email should fail
    success, msg = register_user(
        username="testuser2",
        email="testuser1@gmail.com",
        password="Strong@123"
    )
    assert not success
    assert "already exists" in msg.lower()


def test_weak_password():
    # now weak passwords are rejected
    success, msg = register_user(
        username="weakuser",
        email="weak@gmail.com",
        password="123"
    )
    assert not success
    assert "password must" in msg.lower()


def test_invalid_email_format():
    # registration should reject malformed emails
    success, msg = register_user(
        username="mailuser",
        email="invalidemail",
        password="Strong@123"
    )
    assert not success
    assert "valid email" in msg.lower()


def test_login_success():
    # previous successful user should be able to login
    success, data = login_user("testuser1@gmail.com", "Strong@123")
    assert success
    assert isinstance(data, dict)
    assert data.get("username") == "testuser1"


def test_login_wrong_password():
    success, msg = login_user("testuser1@gmail.com", "wrongpass")
    assert not success
    assert "invalid email" in msg.lower()


def test_login_nonexistent():
    success, msg = login_user("noone@example.com", "whatever")
    assert not success
    assert "invalid email" in msg.lower()
