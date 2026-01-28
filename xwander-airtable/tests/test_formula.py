"""Tests for the formula builder module."""

import pytest
from xwander_airtable.formula import Formula, F, FormulaBuilder


class TestFormulaBasics:
    """Test basic formula operations."""

    def test_equals(self):
        """Test equality formula."""
        formula = F.equals("Status", "Active")
        assert str(formula) == '{Status} = "Active"'

    def test_not_equals(self):
        """Test not equals formula."""
        formula = F.not_equals("Type", "Private")
        assert str(formula) == '{Type} != "Private"'

    def test_equals_numeric(self):
        """Test equality with numeric value."""
        formula = F.equals("Count", 10)
        assert str(formula) == "{Count} = 10"

    def test_greater_than(self):
        """Test greater than formula."""
        formula = F.greater_than("Price", 100)
        assert str(formula) == "{Price} > 100"

    def test_less_or_equal(self):
        """Test less than or equal formula."""
        formula = F.less_or_equal("Count", 50)
        assert str(formula) == "{Count} <= 50"


class TestTextFunctions:
    """Test text-based formula functions."""

    def test_contains(self):
        """Test FIND-based contains."""
        formula = F.contains("Notes", "urgent")
        assert str(formula) == 'FIND("urgent", {Notes}) > 0'

    def test_starts_with(self):
        """Test starts with formula."""
        formula = F.starts_with("Name", "Summer")
        assert str(formula) == 'FIND("Summer", {Name}) = 1'

    def test_not_empty(self):
        """Test not empty formula."""
        formula = F.not_empty("Description")
        assert str(formula) == '{Description} != ""'

    def test_is_empty(self):
        """Test is empty formula."""
        formula = F.is_empty("Notes")
        assert str(formula) == '{Notes} = ""'


class TestDateFunctions:
    """Test date-based formula functions."""

    def test_is_after(self):
        """Test IS_AFTER formula."""
        formula = F.is_after("Start Date", "2026-06-01")
        assert str(formula) == 'IS_AFTER({Start Date}, "2026-06-01")'

    def test_is_before(self):
        """Test IS_BEFORE formula."""
        formula = F.is_before("End Date", "2026-08-31")
        assert str(formula) == 'IS_BEFORE({End Date}, "2026-08-31")'

    def test_is_after_today(self):
        """Test IS_AFTER with TODAY()."""
        formula = F.is_after_today("Due Date")
        assert str(formula) == "IS_AFTER({Due Date}, TODAY())"

    def test_is_same(self):
        """Test IS_SAME formula."""
        formula = F.is_same("Created", "2026-01-28", "day")
        assert str(formula) == 'IS_SAME({Created}, "2026-01-28", "day")'


class TestCombinations:
    """Test combining formulas with AND/OR."""

    def test_and(self):
        """Test AND combination."""
        formula = F.equals("Status", "Active").and_(F.not_empty("Start Date"))
        assert str(formula) == 'AND({Status} = "Active", {Start Date} != "")'

    def test_or(self):
        """Test OR combination."""
        formula = F.equals("Status", "Active").or_(F.equals("Status", "Pending"))
        assert str(formula) == 'OR({Status} = "Active", {Status} = "Pending")'

    def test_in_list(self):
        """Test IN list (multiple OR)."""
        formula = F.in_list("Track", ["Day Tours", "Academy", "Erasmus+"])
        expected = 'OR({Track} = "Day Tours", {Track} = "Academy", {Track} = "Erasmus+")'
        assert str(formula) == expected

    def test_all_of(self):
        """Test ALL OF (multiple AND)."""
        formula = F.all_of(
            F.equals("Track", "Day Tours"),
            F.is_after("Start Date", "2026-06-01"),
            F.contains("Notes", "morning"),
        )
        expected = 'AND({Track} = "Day Tours", IS_AFTER({Start Date}, "2026-06-01"), FIND("morning", {Notes}) > 0)'
        assert str(formula) == expected

    def test_any_of(self):
        """Test ANY OF (multiple OR)."""
        formula = F.any_of(
            F.equals("Status", "Active"),
            F.equals("Status", "Pending"),
            F.equals("Status", "Review"),
        )
        expected = 'OR({Status} = "Active", {Status} = "Pending", {Status} = "Review")'
        assert str(formula) == expected


class TestFormulaBuilder:
    """Test the fluent FormulaBuilder."""

    def test_simple_where(self):
        """Test simple where clause."""
        formula = FormulaBuilder().where("Status", "Active").build()
        assert str(formula) == '{Status} = "Active"'

    def test_multiple_conditions(self):
        """Test multiple AND conditions."""
        formula = (
            FormulaBuilder()
            .where("Status", "Active")
            .and_where("Track", "Day Tours")
            .build()
        )
        assert str(formula) == 'AND({Status} = "Active", {Track} = "Day Tours")'

    def test_with_date(self):
        """Test with date condition."""
        formula = (
            FormulaBuilder()
            .where("Status", "Active")
            .after("Start Date", "2026-06-01")
            .build()
        )
        assert (
            str(formula)
            == 'AND({Status} = "Active", IS_AFTER({Start Date}, "2026-06-01"))'
        )

    def test_with_contains(self):
        """Test with contains condition."""
        formula = (
            FormulaBuilder().where("Track", "Day Tours").contains("Notes", "urgent").build()
        )
        assert str(formula) == 'AND({Track} = "Day Tours", FIND("urgent", {Notes}) > 0)'

    def test_with_not_empty(self):
        """Test with not empty condition."""
        formula = (
            FormulaBuilder().where("Status", "Active").not_empty("Location").build()
        )
        assert str(formula) == 'AND({Status} = "Active", {Location} != "")'

    def test_empty_builder(self):
        """Test empty builder raises error."""
        from xwander_airtable.exceptions import FormulaError
        with pytest.raises(FormulaError):
            FormulaBuilder().build()


class TestSpecialCases:
    """Test special characters and edge cases."""

    def test_escape_quotes(self):
        """Test escaping quotes in values."""
        formula = F.equals("Name", 'O\'Brien')
        assert str(formula) == "{Name} = \"O'Brien\""

    def test_field_with_space(self):
        """Test field name with spaces."""
        formula = F.equals("Start Date", "2026-06-01")
        assert str(formula) == '{Start Date} = "2026-06-01"'

    def test_url_encoding(self):
        """Test URL encoding for API calls."""
        formula = F.equals("Status", "Active")
        encoded = formula.encode()
        assert "%7B" in encoded or "{" not in encoded  # Should be URL encoded


class TestChaining:
    """Test method chaining."""

    def test_complex_chain(self):
        """Test complex formula chaining."""
        formula = (
            F.equals("Track", "Day Tours")
            .and_(F.is_after("Start Date", "2026-06-01"))
            .and_(F.is_before("End Date", "2026-08-31"))
            .and_(F.not_empty("Location"))
        )
        # Should be nested ANDs
        assert "AND(" in str(formula)
        assert "{Track}" in str(formula)
        assert "{Start Date}" in str(formula)
        assert "{End Date}" in str(formula)
        assert "{Location}" in str(formula)
