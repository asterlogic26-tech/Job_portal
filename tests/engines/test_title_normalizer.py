"""Unit tests for engines.normalization.title_normalizer"""
import pytest
from engines.normalization.title_normalizer import normalize_title


class TestNormalizeTitle:
    def test_sr_expansion(self):
        result = normalize_title("Sr. Python Engineer")
        assert "Senior" in result

    def test_jr_expansion(self):
        result = normalize_title("Jr. Developer")
        assert "Junior" in result

    def test_swe_expansion(self):
        result = normalize_title("SWE II")
        assert "Software Engineer" in result

    def test_frontend_variants(self):
        for raw in ["Frontend Engineer", "front-end Engineer", "Front End Engineer"]:
            result = normalize_title(raw)
            assert "Frontend" in result

    def test_backend_variants(self):
        for raw in ["Backend Developer", "back-end Developer", "Back End Developer"]:
            result = normalize_title(raw)
            assert "Backend" in result

    def test_full_stack_variants(self):
        for raw in ["Full-Stack Developer", "Fullstack Engineer", "Full Stack Engineer"]:
            result = normalize_title(raw)
            assert "Full Stack" in result

    def test_strip_whitespace(self):
        result = normalize_title("  Software Engineer  ")
        assert result == normalize_title("Software Engineer")

    def test_capitalize_words(self):
        result = normalize_title("senior software engineer")
        assert result[0].isupper()

    def test_passthrough_unknown_title(self):
        result = normalize_title("Quantum Flux Technician")
        assert "Quantum" in result
        assert "Flux" in result
        assert "Technician" in result

    def test_empty_string_does_not_raise(self):
        result = normalize_title("")
        assert isinstance(result, str)
