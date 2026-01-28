"""Type-safe formula builder for Airtable filterByFormula parameter.

This is a key enhancement over the MCP - provides a Pythonic way to build
complex formulas without string manipulation or syntax errors.

Usage:
    from xwander_airtable.formula import Formula, F

    # Simple equality
    f = Formula.equals("Status", "Active")
    # Output: {Status} = "Active"

    # Combined conditions
    f = Formula.equals("Track", "Day Tours").and_(
        Formula.not_empty("Start Date")
    )
    # Output: AND({Track} = "Day Tours", {Start Date} != "")

    # Date comparisons
    f = Formula.is_after("Start Date", "2026-06-01")
    # Output: IS_AFTER({Start Date}, "2026-06-01")

    # Text search (FIND)
    f = Formula.contains("Notes", "Private")
    # Output: FIND("Private", {Notes}) > 0

    # OR with multiple values
    f = Formula.in_list("Track", ["Day Tours", "Academy", "Erasmus+"])
    # Output: OR({Track} = "Day Tours", {Track} = "Academy", {Track} = "Erasmus+")

    # Build and URL-encode
    query = f.build()
    encoded = f.encode()
"""

from typing import Union, List, Optional, Any
from urllib.parse import quote
from datetime import date, datetime

from .exceptions import FormulaError


class Formula:
    """Chainable formula builder for Airtable filterByFormula."""

    def __init__(self, expression: str):
        """Initialize with raw expression string."""
        self._expression = expression

    def __str__(self) -> str:
        return self._expression

    def __repr__(self) -> str:
        return f"Formula({self._expression!r})"

    def build(self) -> str:
        """Return the formula string."""
        return self._expression

    def encode(self) -> str:
        """Return URL-encoded formula for API requests."""
        return quote(self._expression, safe="")

    # ============ Logical Operators ============

    def and_(self, other: "Formula") -> "Formula":
        """Combine with AND."""
        return Formula(f"AND({self._expression}, {other._expression})")

    def or_(self, other: "Formula") -> "Formula":
        """Combine with OR."""
        return Formula(f"OR({self._expression}, {other._expression})")

    def not_(self) -> "Formula":
        """Negate the formula."""
        return Formula(f"NOT({self._expression})")

    # ============ Comparison Builders (Class Methods) ============

    @classmethod
    def field(cls, name: str) -> str:
        """Format a field reference."""
        # Escape field names with special characters
        if any(c in name for c in [" ", "{", "}", '"', "'"]):
            return f"{{{name}}}"
        return f"{{{name}}}"

    @classmethod
    def value(cls, val: Any) -> str:
        """Format a value for the formula."""
        if val is None:
            return "BLANK()"
        if isinstance(val, bool):
            return "TRUE()" if val else "FALSE()"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, (date, datetime)):
            return f'"{val.isoformat()}"'
        # String - escape quotes
        escaped = str(val).replace('"', '\\"')
        return f'"{escaped}"'

    @classmethod
    def equals(cls, field_name: str, value: Any) -> "Formula":
        """Create equality comparison: {field} = value"""
        return cls(f"{cls.field(field_name)} = {cls.value(value)}")

    @classmethod
    def not_equals(cls, field_name: str, value: Any) -> "Formula":
        """Create inequality: {field} != value"""
        return cls(f"{cls.field(field_name)} != {cls.value(value)}")

    @classmethod
    def greater_than(cls, field_name: str, value: Union[int, float]) -> "Formula":
        """Create greater than: {field} > value"""
        return cls(f"{cls.field(field_name)} > {value}")

    @classmethod
    def less_than(cls, field_name: str, value: Union[int, float]) -> "Formula":
        """Create less than: {field} < value"""
        return cls(f"{cls.field(field_name)} < {value}")

    @classmethod
    def greater_or_equal(cls, field_name: str, value: Union[int, float]) -> "Formula":
        """Create greater or equal: {field} >= value"""
        return cls(f"{cls.field(field_name)} >= {value}")

    @classmethod
    def less_or_equal(cls, field_name: str, value: Union[int, float]) -> "Formula":
        """Create less or equal: {field} <= value"""
        return cls(f"{cls.field(field_name)} <= {value}")

    # ============ Empty/Blank Checks ============

    @classmethod
    def is_empty(cls, field_name: str) -> "Formula":
        """Check if field is empty/blank."""
        return cls(f'{cls.field(field_name)} = ""')

    @classmethod
    def not_empty(cls, field_name: str) -> "Formula":
        """Check if field is not empty."""
        return cls(f'{cls.field(field_name)} != ""')

    @classmethod
    def is_blank(cls, field_name: str) -> "Formula":
        """Check if field is BLANK()."""
        return cls(f"{cls.field(field_name)} = BLANK()")

    # ============ Text Functions ============

    @classmethod
    def contains(cls, field_name: str, search_text: str) -> "Formula":
        """Check if field contains text using FIND()."""
        escaped = search_text.replace('"', '\\"')
        return cls(f'FIND("{escaped}", {cls.field(field_name)}) > 0')

    @classmethod
    def starts_with(cls, field_name: str, prefix: str) -> "Formula":
        """Check if field starts with text."""
        escaped = prefix.replace('"', '\\"')
        return cls(f'FIND("{escaped}", {cls.field(field_name)}) = 1')

    @classmethod
    def regex_match(cls, field_name: str, pattern: str) -> "Formula":
        """Match field against regex pattern."""
        escaped = pattern.replace('"', '\\"')
        return cls(f'REGEX_MATCH({cls.field(field_name)}, "{escaped}")')

    # ============ Date Functions ============

    @classmethod
    def is_after(cls, field_name: str, date_value: Union[str, date, datetime]) -> "Formula":
        """Check if date field is after given date."""
        if isinstance(date_value, (date, datetime)):
            date_str = date_value.isoformat()
        else:
            date_str = date_value
        return cls(f'IS_AFTER({cls.field(field_name)}, "{date_str}")')

    @classmethod
    def is_before(cls, field_name: str, date_value: Union[str, date, datetime]) -> "Formula":
        """Check if date field is before given date."""
        if isinstance(date_value, (date, datetime)):
            date_str = date_value.isoformat()
        else:
            date_str = date_value
        return cls(f'IS_BEFORE({cls.field(field_name)}, "{date_str}")')

    @classmethod
    def is_same(cls, field_name: str, date_value: Union[str, date, datetime], unit: str = "day") -> "Formula":
        """Check if date field is same as given date (day/month/year)."""
        if isinstance(date_value, (date, datetime)):
            date_str = date_value.isoformat()
        else:
            date_str = date_value
        return cls(f'IS_SAME({cls.field(field_name)}, "{date_str}", "{unit}")')

    @classmethod
    def today(cls) -> "Formula":
        """Return TODAY() function."""
        return cls("TODAY()")

    @classmethod
    def is_after_today(cls, field_name: str) -> "Formula":
        """Check if date is after today."""
        return cls(f"IS_AFTER({cls.field(field_name)}, TODAY())")

    @classmethod
    def is_before_today(cls, field_name: str) -> "Formula":
        """Check if date is before today."""
        return cls(f"IS_BEFORE({cls.field(field_name)}, TODAY())")

    # ============ Multi-Value Helpers ============

    @classmethod
    def in_list(cls, field_name: str, values: List[Any]) -> "Formula":
        """Check if field equals any value in list (OR)."""
        if not values:
            raise FormulaError("in_list requires at least one value")
        conditions = [f"{cls.field(field_name)} = {cls.value(v)}" for v in values]
        if len(conditions) == 1:
            return cls(conditions[0])
        return cls(f"OR({', '.join(conditions)})")

    @classmethod
    def not_in_list(cls, field_name: str, values: List[Any]) -> "Formula":
        """Check if field doesn't equal any value in list (AND of !=)."""
        if not values:
            raise FormulaError("not_in_list requires at least one value")
        conditions = [f"{cls.field(field_name)} != {cls.value(v)}" for v in values]
        if len(conditions) == 1:
            return cls(conditions[0])
        return cls(f"AND({', '.join(conditions)})")

    # ============ Linked Records ============

    @classmethod
    def linked_record_id(cls, field_name: str, record_id: str) -> "Formula":
        """Check if linked record field contains specific record ID."""
        return cls(f'FIND("{record_id}", ARRAYJOIN(RECORD_ID({cls.field(field_name)}))) > 0')

    # ============ Combining Multiple Formulas ============

    @classmethod
    def all_of(cls, *formulas: "Formula") -> "Formula":
        """Combine multiple formulas with AND."""
        if not formulas:
            raise FormulaError("all_of requires at least one formula")
        if len(formulas) == 1:
            return formulas[0]
        expressions = [f._expression for f in formulas]
        return cls(f"AND({', '.join(expressions)})")

    @classmethod
    def any_of(cls, *formulas: "Formula") -> "Formula":
        """Combine multiple formulas with OR."""
        if not formulas:
            raise FormulaError("any_of requires at least one formula")
        if len(formulas) == 1:
            return formulas[0]
        expressions = [f._expression for f in formulas]
        return cls(f"OR({', '.join(expressions)})")

    @classmethod
    def raw(cls, expression: str) -> "Formula":
        """Create formula from raw expression string."""
        return cls(expression)


# Alias for shorter imports
F = Formula


class FormulaBuilder:
    """Fluent builder for complex formulas.

    Usage:
        builder = FormulaBuilder()
        formula = (
            builder
            .where("Status", "Active")
            .and_where("Track", "Day Tours")
            .or_where_in("Type", ["Public", "Shared"])
            .after("Start Date", "2026-06-01")
            .build()
        )
    """

    def __init__(self):
        self._conditions: List[Formula] = []
        self._operator: str = "AND"

    def where(self, field: str, value: Any) -> "FormulaBuilder":
        """Add equality condition."""
        self._conditions.append(Formula.equals(field, value))
        return self

    def where_not(self, field: str, value: Any) -> "FormulaBuilder":
        """Add inequality condition."""
        self._conditions.append(Formula.not_equals(field, value))
        return self

    def and_where(self, field: str, value: Any) -> "FormulaBuilder":
        """Add AND equality condition."""
        self._operator = "AND"
        return self.where(field, value)

    def or_where(self, field: str, value: Any) -> "FormulaBuilder":
        """Add OR equality condition (switches to OR mode)."""
        self._operator = "OR"
        return self.where(field, value)

    def where_in(self, field: str, values: List[Any]) -> "FormulaBuilder":
        """Add IN list condition."""
        self._conditions.append(Formula.in_list(field, values))
        return self

    def or_where_in(self, field: str, values: List[Any]) -> "FormulaBuilder":
        """Add OR IN list condition."""
        self._operator = "OR"
        return self.where_in(field, values)

    def not_empty(self, field: str) -> "FormulaBuilder":
        """Add not empty condition."""
        self._conditions.append(Formula.not_empty(field))
        return self

    def is_empty(self, field: str) -> "FormulaBuilder":
        """Add empty condition."""
        self._conditions.append(Formula.is_empty(field))
        return self

    def contains(self, field: str, text: str) -> "FormulaBuilder":
        """Add contains condition."""
        self._conditions.append(Formula.contains(field, text))
        return self

    def after(self, field: str, date_value: Union[str, date, datetime]) -> "FormulaBuilder":
        """Add is_after date condition."""
        self._conditions.append(Formula.is_after(field, date_value))
        return self

    def before(self, field: str, date_value: Union[str, date, datetime]) -> "FormulaBuilder":
        """Add is_before date condition."""
        self._conditions.append(Formula.is_before(field, date_value))
        return self

    def after_today(self, field: str) -> "FormulaBuilder":
        """Add is_after_today condition."""
        self._conditions.append(Formula.is_after_today(field))
        return self

    def greater_than(self, field: str, value: Union[int, float]) -> "FormulaBuilder":
        """Add greater than condition."""
        self._conditions.append(Formula.greater_than(field, value))
        return self

    def less_than(self, field: str, value: Union[int, float]) -> "FormulaBuilder":
        """Add less than condition."""
        self._conditions.append(Formula.less_than(field, value))
        return self

    def raw(self, expression: str) -> "FormulaBuilder":
        """Add raw formula expression."""
        self._conditions.append(Formula.raw(expression))
        return self

    def build(self) -> Formula:
        """Build the final formula."""
        if not self._conditions:
            raise FormulaError("No conditions added to builder")
        if len(self._conditions) == 1:
            return self._conditions[0]
        if self._operator == "AND":
            return Formula.all_of(*self._conditions)
        return Formula.any_of(*self._conditions)

    def build_str(self) -> str:
        """Build and return formula string."""
        return self.build().build()

    def encode(self) -> str:
        """Build and return URL-encoded formula."""
        return self.build().encode()
