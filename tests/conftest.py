import importlib

import pytest

import core

webapp_module = importlib.import_module('webapp.app')
webapp_module.app._prepare(is_prod=False)


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(webapp_module, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(core, '_dir_cache', {})
    return tmp_path
