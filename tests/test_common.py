"""Unit tests for common.py utilities."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add tools to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from common import extract_link_targets, iter_requirement_files, load_trace


class TestLoadTrace:
    """Tests for load_trace() function."""

    def test_load_trace_success(self, tmp_path):
        """Test loading valid trace.json."""
        # Create test trace.json
        trace_data = {
            "requirements": {"BR-001": {"title": "Test"}},
            "links": []
        }
        trace_file = tmp_path / "outputs" / "trace.json"
        trace_file.parent.mkdir(parents=True)
        trace_file.write_text(json.dumps(trace_data))

        # Mock the TRACE_JSON_PATH
        with patch("common.TRACE_JSON_PATH", trace_file):
            result = load_trace()
            assert result == trace_data
            assert "requirements" in result

    def test_load_trace_missing_file(self, tmp_path):
        """Test handling of missing trace.json."""
        missing_file = tmp_path / "missing.json"
        
        with patch("common.TRACE_JSON_PATH", missing_file):
            with pytest.raises(SystemExit) as exc_info:
                load_trace()
            assert exc_info.value.code == 1

    def test_load_trace_malformed_json(self, tmp_path):
        """Test handling of malformed JSON."""
        trace_file = tmp_path / "bad.json"
        trace_file.write_text("{invalid json")
        
        with patch("common.TRACE_JSON_PATH", trace_file):
            with pytest.raises(SystemExit) as exc_info:
                load_trace()
            assert exc_info.value.code == 1


class TestExtractLinkTargets:
    """Tests for extract_link_targets() function."""

    def test_extract_from_dict(self):
        """Test extracting links from dict format."""
        links = {"derives": ["BR-001", "BR-002"]}
        result = extract_link_targets(links, "derives")
        assert result == ["BR-001", "BR-002"]

    def test_extract_from_list_of_dicts(self):
        """Test extracting links from list of dicts format."""
        links = [
            {"derives": ["BR-001"]},
            {"satisfies": ["SR-001"]}
        ]
        result = extract_link_targets(links, "derives")
        assert result == ["BR-001"]

    def test_extract_single_value(self):
        """Test extracting single non-list value."""
        links = {"derives": "BR-001"}
        result = extract_link_targets(links, "derives")
        assert result == ["BR-001"]

    def test_extract_none_input(self):
        """Test handling None input."""
        result = extract_link_targets(None, "derives")
        assert result == []

    def test_extract_missing_key(self):
        """Test extracting key that doesn't exist."""
        links = {"derives": ["BR-001"]}
        result = extract_link_targets(links, "satisfies")
        assert result == []

    def test_extract_filters_empty_strings(self):
        """Test that empty strings are filtered out."""
        links = {"derives": ["BR-001", "", "BR-002", None]}
        result = extract_link_targets(links, "derives")
        assert result == ["BR-001", "BR-002"]


class TestIterRequirementFiles:
    """Tests for iter_requirement_files() function."""

    def test_iter_files_in_directory(self, tmp_path):
        """Test iterating over markdown files."""
        # Create test files
        req_dir = tmp_path / "requirements"
        req_dir.mkdir()
        (req_dir / "BR-001.md").write_text("test")
        (req_dir / "BR-002.md").write_text("test")
        (req_dir / "README.txt").write_text("ignore")
        
        files = list(iter_requirement_files([req_dir]))
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)

    def test_iter_excludes_backup_files(self, tmp_path):
        """Test that .bak files are excluded."""
        req_dir = tmp_path / "requirements"
        req_dir.mkdir()
        (req_dir / "BR-001.md").write_text("test")
        (req_dir / "BR-002.md.bak").write_text("backup")
        
        files = list(iter_requirement_files([req_dir]))
        assert len(files) == 1
        assert files[0].name == "BR-001.md"

    def test_iter_missing_directory(self, tmp_path):
        """Test handling of missing directory."""
        missing_dir = tmp_path / "missing"
        files = list(iter_requirement_files([missing_dir]))
        assert files == []

    def test_iter_sorted_output(self, tmp_path):
        """Test that files are returned in sorted order."""
        req_dir = tmp_path / "requirements"
        req_dir.mkdir()
        (req_dir / "BR-003.md").write_text("test")
        (req_dir / "BR-001.md").write_text("test")
        (req_dir / "BR-002.md").write_text("test")
        
        files = list(iter_requirement_files([req_dir]))
        names = [f.name for f in files]
        assert names == ["BR-001.md", "BR-002.md", "BR-003.md"]
