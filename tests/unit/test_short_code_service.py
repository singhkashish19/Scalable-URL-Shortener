"""
Unit tests for short code generation.
"""

import pytest

from app.application.services.short_code_service import (
    Base62Encoder,
    ShortCodeGenerator,
    SnowflakeIDGenerator,
)


class TestBase62Encoder:
    """Test Base62 encoding/decoding."""

    def test_encode_zero(self):
        """Test encoding zero."""
        assert Base62Encoder.encode(0) == "0"

    def test_encode_one(self):
        """Test encoding one."""
        assert Base62Encoder.encode(1) == "1"

    def test_encode_large_number(self):
        """Test encoding large number."""
        encoded = Base62Encoder.encode(12345678)
        decoded = Base62Encoder.decode(encoded)
        assert decoded == 12345678

    def test_decode(self):
        """Test decoding."""
        assert Base62Encoder.decode("0") == 0
        assert Base62Encoder.decode("1") == 1
        assert Base62Encoder.decode("Z") == 61


class TestSnowflakeIDGenerator:
    """Test Snowflake ID generation."""

    def test_init_valid_machine_id(self):
        """Test initialization with valid machine ID."""
        generator = SnowflakeIDGenerator(machine_id=1)
        assert generator.machine_id == 1

    def test_init_invalid_machine_id(self):
        """Test initialization with invalid machine ID."""
        with pytest.raises(ValueError):
            SnowflakeIDGenerator(machine_id=2000)

    def test_next_id_increments(self):
        """Test that IDs increment."""
        generator = SnowflakeIDGenerator(machine_id=0)
        id1 = generator.next_id()
        id2 = generator.next_id()
        assert id2 > id1

    def test_next_id_uniqueness(self):
        """Test ID uniqueness within machine."""
        generator = SnowflakeIDGenerator(machine_id=0)
        ids = [generator.next_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    def test_machine_id_in_id(self):
        """Test that machine ID is encoded in ID."""
        generator1 = SnowflakeIDGenerator(machine_id=1)
        generator2 = SnowflakeIDGenerator(machine_id=2)

        # IDs should differ due to machine ID
        id1 = generator1.next_id()
        id2 = generator2.next_id()

        # Extract machine ID portion
        machine1 = (id1 >> 12) & 0x3FF
        machine2 = (id2 >> 12) & 0x3FF

        assert machine1 == 1
        assert machine2 == 2


class TestShortCodeGenerator:
    """Test short code generation."""

    def test_generate_random(self):
        """Test random generation."""
        generator = ShortCodeGenerator()
        code = generator.generate_random()
        assert len(code) == 6
        assert code.isalnum()

    def test_generate_sequential(self):
        """Test sequential generation."""
        generator = ShortCodeGenerator()
        code1 = generator.generate_sequential(0)
        code2 = generator.generate_sequential(1)
        assert len(code1) == 6
        assert code1 != code2

    def test_generate_snowflake(self):
        """Test Snowflake ID generation."""
        generator = ShortCodeGenerator()
        code = generator.generate_snowflake()
        assert len(code) > 0
        assert code.isalnum()

    def test_generate(self):
        """Test default generation."""
        generator = ShortCodeGenerator()
        codes = [generator.generate() for _ in range(10)]
        assert len(set(codes)) == 10  # All unique
        assert all(len(code) > 0 for code in codes)
