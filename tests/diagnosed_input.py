# diagnostic_import_check.py
"""
Diagnostic script to identify and fix the ValidationService import error
Run this script to check what's wrong with your imports
"""

import sys
import os
from pathlib import Path

def check_file_structure():
    """Check if all required files exist with correct structure"""
    print("🔍 Checking file structure...")
    
    # Expected file paths
    expected_files = [
        'src/name_address_validator/__init__.py',
        'src/name_address_validator/services/__init__.py', 
        'src/name_address_validator/services/validation_service.py',
        'src/name_address_validator/utils/__init__.py',
        'src/name_address_validator/utils/config.py',
        'src/name_address_validator/utils/logger.py',
        'src/name_address_validator/validators/__init__.py',
        'src/name_address_validator/validators/name_validator.py',
        'src/name_address_validator/validators/address_validator.py'
    ]
    
    missing_files = []
    found_files = []
    
    for file_path in expected_files:
        if os.path.exists(file_path):
            found_files.append(file_path)
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path}")
    
    print(f"\n📊 File check: {len(found_files)}/{len(expected_files)} files found")
    
    if missing_files:
        print("⚠️ Missing files detected. These may cause import errors:")
        for file in missing_files:
            print(f"   • {file}")
    
    return len(missing_files) == 0

def check_validation_service_file():
    """Check the contents of validation_service.py for syntax errors"""
    print("\n🔍 Checking validation_service.py...")
    
    file_path = 'src/name_address_validator/services/validation_service.py'
    
    if not os.path.exists(file_path):
        print(f"   ❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if ValidationService class is defined
        if 'class ValidationService' in content:
            print("   ✅ ValidationService class found in file")
        else:
            print("   ❌ ValidationService class NOT found in file")
            print("   💡 The class may be named differently or missing")
            return False
        
        # Try to compile the file to check for syntax errors
        try:
            compile(content, file_path, 'exec')
            print("   ✅ File syntax is valid")
            return True
        except SyntaxError as e:
            print(f"   ❌ Syntax error in file: {e}")
            print(f"   📍 Line {e.lineno}: {e.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return False

def check_python_path():
    """Check Python path configuration"""
    print("\n🔍 Checking Python path...")
    
    current_dir = os.getcwd()
    print(f"   📂 Current directory: {current_dir}")
    
    # Check if src directory exists
    src_path = os.path.join(current_dir, 'src')
    if os.path.exists(src_path):
        print(f"   ✅ src directory found: {src_path}")
        
        # Check if src is in Python path
        if src_path in sys.path:
            print("   ✅ src directory is in Python path")
        else:
            print("   ⚠️ src directory is NOT in Python path")
            print("   💡 This may cause import issues")
            return False
    else:
        print(f"   ❌ src directory not found: {src_path}")
        return False
    
    return True

def test_manual_import():
    """Try to manually import and diagnose the issue"""
    print("\n🧪 Testing manual import...")
    
    # First, ensure src is in path
    current_dir = os.getcwd()
    src_path = os.path.join(current_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"   🔧 Added to Python path: {src_path}")
    
    # Try different import approaches
    import_tests = [
        ("Direct import", "from name_address_validator.services.validation_service import ValidationService"),
        ("Module import", "import name_address_validator.services.validation_service"),
        ("Package import", "import name_address_validator"),
    ]
    
    for test_name, import_stmt in import_tests:
        print(f"   🧪 Testing {test_name}: {import_stmt}")
        try:
            exec(import_stmt)
            print(f"      ✅ Success")
            
            # If direct import worked, check if class exists
            if test_name == "Direct import":
                print("      ✅ ValidationService imported successfully")
                return True
            elif test_name == "Module import":
                # Check if class exists in module
                import name_address_validator.services.validation_service as vs_module
                if hasattr(vs_module, 'ValidationService'):
                    print("      ✅ ValidationService class found in module")
                    return True
                else:
                    print("      ❌ ValidationService class NOT found in module")
                    print("      🔍 Available attributes:", [attr for attr in dir(vs_module) if not attr.startswith('_')])
                    
        except Exception as e:
            print(f"      ❌ Failed: {e}")
    
    return False

def check_init_files():
    """Check if __init__.py files are properly configured"""
    print("\n🔍 Checking __init__.py files...")
    
    init_files = [
        'src/name_address_validator/__init__.py',
        'src/name_address_validator/services/__init__.py',
        'src/name_address_validator/utils/__init__.py',
        'src/name_address_validator/validators/__init__.py'
    ]
    
    all_good = True
    
    for init_file in init_files:
        if os.path.exists(init_file):
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    print(f"   ✅ {init_file} (has content)")
                else:
                    print(f"   ⚠️ {init_file} (empty - this is okay)")
                    
            except Exception as e:
                print(f"   ❌ {init_file} (error reading: {e})")
                all_good = False
        else:
            print(f"   ❌ {init_file} (missing)")
            all_good = False
    
    return all_good

def provide_solutions():
    """Provide step-by-step solutions"""
    print("\n" + "="*60)
    print("🔧 SOLUTIONS")
    print("="*60)
    
    print("\n1. **Quick Fix - Try this first:**")
    print("   Create a minimal ValidationService if the original is corrupted:")
    
    quick_fix_code = '''
# Create: src/name_address_validator/services/validation_service_minimal.py
class ValidationService:
    def __init__(self, debug_callback=None):
        print("ValidationService initialized")
    
    def validate_single_record(self, first_name, last_name, street_address, city, state, zip_code):
        return {
            'timestamp': 'test',
            'name_result': {'valid': True},
            'address_result': {'deliverable': True},
            'overall_valid': True,
            'overall_confidence': 0.8
        }
'''
    print(quick_fix_code)
    
    print("\n2. **Path Fix:**")
    print("   Add this to the top of your script:")
    
    path_fix_code = '''
import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).resolve().parent
src_path = current_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now try the import
from name_address_validator.services.validation_service import ValidationService
'''
    print(path_fix_code)
    
    print("\n3. **Create Missing __init__.py Files:**")
    print("   Run these commands:")
    
    init_commands = '''
# Create missing __init__.py files
touch src/name_address_validator/__init__.py
touch src/name_address_validator/services/__init__.py
touch src/name_address_validator/utils/__init__.py  
touch src/name_address_validator/validators/__init__.py

# Or on Windows:
echo. > src\\name_address_validator\\__init__.py
echo. > src\\name_address_validator\\services\\__init__.py
echo. > src\\name_address_validator\\utils\\__init__.py
echo. > src\\name_address_validator\\validators\\__init__.py
'''
    print(init_commands)
    
    print("\n4. **Check for File Conflicts:**")
    print("   Make sure you don't have any files named:")
    print("   • validation_service.py in your current directory")
    print("   • name_address_validator.py in your current directory")
    print("   These would shadow the real modules")
    
    print("\n5. **Run with Explicit Path:**")
    print("   Try running your script like this:")
    print("   cd /path/to/your/project")
    print("   PYTHONPATH=./src streamlit run src/name_address_validator/enhanced_app.py")

def main():
    """Run all diagnostic checks"""
    print("🚀 Import Error Diagnostic Tool")
    print("="*60)
    print("This tool will help identify why ValidationService cannot be imported")
    
    checks = [
        ("File Structure", check_file_structure),
        ("ValidationService File", check_validation_service_file), 
        ("Python Path", check_python_path),
        ("__init__.py Files", check_init_files),
        ("Manual Import Test", test_manual_import)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results[check_name] = result
        except Exception as e:
            print(f"   ❌ Error during {check_name}: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY") 
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} {check}")
    
    print(f"\n📊 Overall: {passed}/{total} checks passed")
    
    if passed < total:
        print("\n⚠️ Issues detected. See solutions below:")
        provide_solutions()
    else:
        print("\n🎉 All checks passed! The import should work.")
        print("If you're still having issues, try restarting your Python environment.")

if __name__ == "__main__":
    main()