"""Конфигурация pytest и общие фикстуры."""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Временная директория для тестов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pbxproj_content():
    """Образец содержимого project.pbxproj файла."""
    return """
    MARKETING_VERSION = 1.0;
    CURRENT_PROJECT_VERSION = 1;
    INFOPLIST_KEY_CFBundleDisplayName = "TestApp";
    PRODUCT_BUNDLE_IDENTIFIER = com.test.app;
    """


@pytest.fixture
def sample_swift_content():
    """Образец содержимого Swift файла с датой активации."""
    return '''
    import Foundation
    
    let activationDate = formatter.date(from: "2026/01/31")
    '''

