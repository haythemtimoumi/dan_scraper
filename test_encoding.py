#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify encoding fixes work properly
"""

import sys

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_encoding():
    """Test that we can print various characters without encoding errors"""
    print("Testing encoding fixes...")
    print("Regular ASCII text: OK")
    print("Unicode characters: ✓ ✗ ⚠ ℹ")
    print("Emojis: 🔍 📄 ✅ ❌ ⚠️")
    print("Special characters: àáâãäåæçèéêë")
    print("All tests completed successfully!")

if __name__ == "__main__":
    test_encoding()