"""
PHN Blockchain Test Suite

Comprehensive testing infrastructure for PHN blockchain.

Test Categories:
    unit/: Unit tests for individual components
    integration/: Integration tests for system workflows
    performance/: Performance and benchmarking tests
    fixtures/: Test fixtures and helper utilities
    tools/: Testing and verification tools
    utilities/: Test utility scripts

Usage:
    # Run all tests
    pytest
    
    # Run specific category
    pytest test/unit/
    pytest test/integration/
    pytest test/performance/
    
    # Run with coverage
    pytest --cov=app --cov-report=html
    
    # Run test runner
    python test/run_all_tests.py
"""

__version__ = "1.0.0"
__all__ = ["unit", "integration", "performance", "fixtures", "tools", "utilities"]
