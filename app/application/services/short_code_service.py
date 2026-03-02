"""
Short code generation strategies: Base62, Snowflake ID, etc.
"""

import random
import string
import time
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


class Base62Encoder:
    """Base62 encoding/decoding utilities."""

    ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    @classmethod
    def encode(cls, number: int) -> str:
        """Encode number to base62."""
        if number == 0:
            return cls.ALPHABET[0]

        digits = []
        while number > 0:
            digits.append(cls.ALPHABET[number % 62])
            number //= 62

        return "".join(reversed(digits))

    @classmethod
    def decode(cls, text: str) -> int:
        """Decode base62 to number."""
        result = 0
        for char in text:
            result = result * 62 + cls.ALPHABET.index(char)
        return result


class SnowflakeIDGenerator:
    """
    Distributed ID generation using Snowflake-like algorithm.
    
    Architecture:
    - 64-bit integer
    - 41 bits: timestamp (milliseconds since epoch)
    - 10 bits: machine/datacenter ID
    - 12 bits: sequence number
    
    Supports:
    - 1024 machines (2^10)
    - 4096 IDs per millisecond per machine
    - Until year 2081 (~70 years from 1970)
    """

    EPOCH = 1609459200000  # 2021-01-01 00:00:00 UTC

    def __init__(self, machine_id: int = 0):
        """
        Initialize ID generator.
        
        Args:
            machine_id: Machine/datacenter ID (0-1023)
        """
        if not 0 <= machine_id < 1024:
            raise ValueError("machine_id must be between 0 and 1023")

        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = 0

    def next_id(self) -> int:
        """Generate next ID."""
        timestamp = int(time.time() * 1000)

        if timestamp < self.last_timestamp:
            raise Exception("Clock moved backwards")

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits
            if self.sequence == 0:
                # Sequence overflow, wait for next millisecond
                while timestamp <= self.last_timestamp:
                    timestamp = int(time.time() * 1000)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        # Build 64-bit ID
        id_value = (
            ((timestamp - self.EPOCH) << 22)
            | (self.machine_id << 12)
            | self.sequence
        )

        return id_value


class ShortCodeGenerator:
    """Generate short codes using different strategies."""

    def __init__(self):
        """Initialize generator."""
        self.snowflake = SnowflakeIDGenerator(machine_id=0)
        self.code_length = settings.SHORT_CODE_LENGTH

    def generate_random(self) -> str:
        """Generate random short code (collision-prone, needs DB dedup)."""
        return "".join(
            random.choices(
                string.ascii_letters + string.digits,
                k=self.code_length,
            )
        )

    def generate_sequential(self, counter: int) -> str:
        """Generate sequential short code from counter."""
        return Base62Encoder.encode(counter).rjust(self.code_length, "0")

    def generate_snowflake(self) -> str:
        """Generate short code from Snowflake ID (guaranteed unique)."""
        snowflake_id = self.snowflake.next_id()
        return Base62Encoder.encode(snowflake_id)

    def generate(self) -> str:
        """Generate short code (uses Snowflake for production scalability)."""
        return self.generate_snowflake()
