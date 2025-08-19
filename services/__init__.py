# src/name_address_validator/services/__init__.py
"""
Validation services module

This module provides high-level validation services that coordinate
between different validators and provide unified interfaces.
"""

from .validation_service import ValidationService

__all__ = ['ValidationService']