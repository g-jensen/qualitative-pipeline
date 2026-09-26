from . import env as sut
import pytest

def test__not_in_production(monkeypatch):
    monkeypatch.setenv("RUN_MODE", "")

    assert sut.in_production() == False


def test__in_production(monkeypatch):
    monkeypatch.setenv("RUN_MODE", "production")

    assert sut.in_production() == True
