#!/usr/bin/env python3
"""
Test script to verify template system functionality.
"""

def test_template_selection():
    """Test that template selection works correctly."""
    from Whatsapp_Chat_Exporter.utility import setup_template
    
    # Test default template (should be optimized)
    template = setup_template(None, False)
    assert "whatsapp_optimized.html" in str(template.filename)
    print("✅ Default template: optimized")
    
    # Test basic template
    template = setup_template("basic", False)
    assert "whatsapp.html" in str(template.filename)
    print("✅ Basic template selection works")
    
    # Test optimized template explicit
    template = setup_template("optimized", False)
    assert "whatsapp_optimized.html" in str(template.filename)
    print("✅ Optimized template selection works")
    
    # Test experimental template
    template = setup_template("whatsapp_new.html", False, experimental=True)
    assert "whatsapp_new.html" in str(template.filename)
    print("✅ Experimental template selection works")
    
    print("\n🎉 All template tests passed!")

def test_sanitize_function():
    """Test that sanitize_except handles None values."""
    from Whatsapp_Chat_Exporter.utility import sanitize_except
    
    # Test None input
    result = sanitize_except(None)
    assert str(result) == ""
    print("✅ sanitize_except handles None correctly")
    
    # Test normal string
    result = sanitize_except("Hello<br>World")
    assert "<br>" in str(result)
    print("✅ sanitize_except handles normal strings correctly")
    
    print("\n🎉 All sanitize tests passed!")

if __name__ == "__main__":
    print("🧪 Testing template system...")
    test_template_selection()
    test_sanitize_function()
    print("\n✨ All tests completed successfully!")