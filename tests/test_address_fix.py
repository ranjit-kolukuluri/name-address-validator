#!/usr/bin/env python3
"""
FINAL TEST SCRIPT - Verify the combined address parsing fix works
Run this after replacing both files to confirm everything works
"""

import sys
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_combined_address_fix():
    """Test the complete fix end-to-end"""
    
    print("🧪 TESTING COMBINED ADDRESS FIX")
    print("=" * 60)
    
    # Create test data that matches your CSV
    test_data = {
        'first': ['William', 'Jessica', 'James'],
        'last': ['Anderson', 'Thomas', 'Jackson'],
        'full_address': [
            "1600 Pennsylvania Avenue NW, Washington, DC 20500",
            "350 Fifth Avenue, New York, NY 10118", 
            "1 Apple Park Way, Cupertino, CA 95014"
        ],
        'customer_id': ['CUST001', 'CUST002', 'CUST003']
    }
    
    df = pd.DataFrame(test_data)
    print(f"📄 Test data created: {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Sample address: '{df.iloc[0]['full_address']}'")
    
    try:
        from name_address_validator.services.validation_service import ValidationService
        
        def debug_print(msg, cat="TEST"):
            print(f"  [{cat}] {msg}")
        
        print(f"\n🔧 TESTING VALIDATION SERVICE")
        print("-" * 50)
        
        # Initialize ValidationService
        validation_service = ValidationService(debug_callback=debug_print)
        print("✅ ValidationService initialized")
        
        # Test the standardization process
        file_data_list = [(df, "test_combined_addresses.csv")]
        
        print(f"\n📋 TESTING STANDARDIZATION AND QUALIFICATION")
        print("-" * 50)
        
        result = validation_service.standardize_and_qualify_csv_files(file_data_list)
        
        if result['success']:
            print(f"\n✅ STANDARDIZATION SUCCESS!")
            print(f"   Total rows: {result['total_rows']}")
            print(f"   Qualified rows: {result['qualified_rows']}")
            print(f"   Disqualified rows: {result['disqualified_rows']}")
            print(f"   Qualification rate: {result['qualification_summary']['qualification_rate']:.1%}")
            
            # Check qualified data
            qualified_df = result['qualified_data']
            if len(qualified_df) > 0:
                print(f"\n📊 SAMPLE QUALIFIED ADDRESS:")
                sample = qualified_df.iloc[0]
                street = sample.get('street_address', 'MISSING')
                city = sample.get('city', 'MISSING')
                state = sample.get('state', 'MISSING')
                zip_code = sample.get('zip_code', 'MISSING')
                
                print(f"   Street: '{street}'")
                print(f"   City: '{city}'")
                print(f"   State: '{state}'")
                print(f"   ZIP: '{zip_code}'")
                
                # Verify parsing worked
                if street and city and state and zip_code:
                    if ',' not in street or len(street) < 20:
                        print("✅ PARSING WORKED: Address components properly separated!")
                        success = True
                    else:
                        print("❌ PARSING FAILED: Street still contains full address")
                        success = False
                else:
                    print("❌ PARSING FAILED: Missing components")
                    success = False
            else:
                print("❌ NO QUALIFIED ADDRESSES - parsing completely failed")
                success = False
                
            # Check disqualified data
            disqualified_df = result['disqualified_data']
            if len(disqualified_df) > 0:
                sample_bad = disqualified_df.iloc[0]
                errors = sample_bad.get('qualification_errors', '')
                print(f"\n⚠️ SAMPLE DISQUALIFIED ADDRESS:")
                print(f"   Errors: '{errors}'")
                
                if 'Missing city' in errors or 'Missing state' in errors:
                    print("❌ CRITICAL: Still seeing 'Missing city/state' - parsing failed!")
                    success = False
        else:
            print(f"❌ STANDARDIZATION FAILED: {result.get('error')}")
            success = False
            
        # Test preview generation
        if result['success']:
            print(f"\n📋 TESTING PREVIEW GENERATION")
            print("-" * 40)
            
            preview = validation_service.generate_comprehensive_preview(result)
            if preview['success']:
                overview = preview['overview']
                print(f"✅ Preview generated successfully")
                print(f"   Qualification rate: {overview['qualification_rate']:.1%}")
                print(f"   Ready for USPS: {overview['ready_for_usps']}")
                
                if overview['ready_for_usps'] and overview['qualification_rate'] > 0.9:
                    print("🎉 PREVIEW TEST PASSED!")
                else:
                    print("❌ Preview shows poor qualification rate")
                    success = False
            else:
                print(f"❌ Preview failed: {preview.get('error')}")
                success = False
        
        return success
        
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete test"""
    
    print("🚀 FINAL VERIFICATION TEST")
    print("Testing that combined address parsing works correctly")
    print("=" * 60)
    
    success = test_combined_address_fix()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Combined address parsing is working correctly")
        print("✅ Your CSV files should now process successfully")
        print("\nNext steps:")
        print("1. Run: streamlit run src/name_address_validator/app.py")
        print("2. Upload test_csv_files/03_combined_addresses.csv")
        print("3. You should see 100% qualification rate")
    else:
        print("❌ TESTS FAILED!")
        print("The fix may need additional debugging")
        print("Check the error messages above for details")

if __name__ == "__main__":
    main()