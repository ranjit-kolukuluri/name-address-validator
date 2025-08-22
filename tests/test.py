# generate_test_csvs.py
"""
Generate 10 test CSV files with various address input formats to test the standardization process
"""

import pandas as pd
import os
from pathlib import Path
import random

def create_test_data_directory():
    """Create test data directory"""
    test_dir = Path("test_csv_files")
    test_dir.mkdir(exist_ok=True)
    return test_dir

def generate_file_1_standard_format(test_dir):
    """File 1: Standard format - should work perfectly"""
    data = {
        'first_name': ['John', 'Jane', 'Michael', 'Sarah', 'David'],
        'last_name': ['Smith', 'Johnson', 'Williams', 'Brown', 'Davis'],
        'street_address': ['1600 Pennsylvania Avenue NW', '350 Fifth Avenue', '1 Apple Park Way', '1 Microsoft Way', '410 Terry Avenue North'],
        'city': ['Washington', 'New York', 'Cupertino', 'Redmond', 'Seattle'],
        'state': ['DC', 'NY', 'CA', 'WA', 'WA'],
        'zip_code': ['20500', '10118', '95014', '98052', '98109']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "01_standard_format.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Standard format (should be 100% qualified)")
    return filepath

def generate_file_2_alternative_columns(test_dir):
    """File 2: Alternative column names"""
    data = {
        'fname': ['Robert', 'Lisa', 'Christopher', 'Amanda'],
        'lname': ['Garcia', 'Miller', 'Rodriguez', 'Martinez'],
        'addr': ['123 Main Street', '456 Oak Avenue', '789 Pine Road', '321 Elm Street'],
        'town': ['Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
        'st': ['CA', 'IL', 'TX', 'AZ'],
        'postal': ['90210', '60601', '77001', '85001']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "02_alternative_columns.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Alternative column names")
    return filepath

def generate_file_3_combined_addresses(test_dir):
    """File 3: Combined address in single field"""
    data = {
        'first': ['William', 'Jessica', 'James', 'Ashley', 'Matthew'],
        'last': ['Anderson', 'Thomas', 'Jackson', 'White', 'Harris'],
        'full_address': [
            '1600 Pennsylvania Avenue NW, Washington, DC 20500',
            '350 Fifth Avenue, New York, NY 10118',
            '1 Apple Park Way, Cupertino, CA 95014',
            '1 Microsoft Way, Redmond, WA 98052',
            '410 Terry Avenue North, Seattle, WA 98109'
        ],
        'customer_id': ['CUST001', 'CUST002', 'CUST003', 'CUST004', 'CUST005']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "03_combined_addresses.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Combined address format")
    return filepath

def generate_file_4_split_address_fields(test_dir):
    """File 4: Address split into multiple detailed fields"""
    data = {
        'given_name': ['Daniel', 'Emily', 'Anthony', 'Melissa'],
        'family_name': ['Moore', 'Taylor', 'Clark', 'Lewis'],
        'house_number': ['123', '456', '789', '321'],
        'street_name': ['Main Street', 'Oak Avenue', 'Pine Road', 'Elm Street'],
        'apartment': ['Apt 2A', '', 'Unit 5', 'Suite 100'],
        'city_name': ['Dallas', 'San Antonio', 'Austin', 'Fort Worth'],
        'state_code': ['TX', 'TX', 'TX', 'TX'],
        'zip5': ['75201', '78201', '73301', '76101'],
        'zip4': ['1234', '', '5678', '9012']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "04_split_address_fields.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Split address fields")
    return filepath

def generate_file_5_full_state_names(test_dir):
    """File 5: Full state names instead of abbreviations"""
    data = {
        'first_name': ['Mark', 'Nancy', 'Steven', 'Karen'],
        'last_name': ['Wilson', 'Garcia', 'Martinez', 'Anderson'],
        'street_address': ['987 Cedar Lane', '147 Birch Way', '258 Walnut Court', '369 Cherry Street'],
        'city': ['San Jose', 'San Diego', 'Sacramento', 'Fresno'],
        'state': ['California', 'California', 'California', 'California'],  # Full state names
        'zip_code': ['95101', '92101', '94203', '93701']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "05_full_state_names.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Full state names (should be converted to CA)")
    return filepath

def generate_file_6_mixed_quality_data(test_dir):
    """File 6: Mixed quality data - some good, some with issues"""
    data = {
        'first_name': ['Paul', 'Linda', 'Valid', 'Missing', 'Invalid'],
        'last_name': ['Johnson', 'Brown', 'Person', 'Address', 'State'],
        'street_address': ['741 Ash Boulevard', '852 Hickory Drive', '123 Good Street', '', '456 Bad Road'],
        'city': ['Jacksonville', 'Columbus', 'Valid City', 'Missing State', 'Invalid State'],
        'state': ['FL', 'OH', 'NY', '', 'XX'],  # Missing and invalid states
        'zip_code': ['32099', '43085', '10001', '12345', '00000']  # Last one is invalid
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "06_mixed_quality_data.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Mixed quality data (some will be disqualified)")
    return filepath

def generate_file_7_business_format(test_dir):
    """File 7: Business-style format with company names"""
    data = {
        'contact_first': ['John', '', 'Sarah', 'Michael'],
        'contact_last': ['Smith', 'ABC Corporation', 'Johnson', 'Williams'],
        'company_name': ['Tech Solutions Inc', 'ABC Corporation', 'Marketing Plus LLC', 'Business Services Co'],
        'mailing_address': ['100 Business Park Dr Suite 200', '250 Corporate Center', '500 Industrial Blvd', '750 Commerce Way'],
        'municipality': ['Atlanta', 'Denver', 'Memphis', 'Portland'],
        'province': ['GA', 'CO', 'TN', 'OR'],
        'postal': ['30309', '80202', '38103', '97201'],
        'business_type': ['Technology', 'Consulting', 'Marketing', 'Services']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "07_business_format.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Business format")
    return filepath

def generate_file_8_messy_formatting(test_dir):
    """File 8: Messy formatting with inconsistencies"""
    data = {
        'FirstName': ['  ROBERT  ', 'jane', 'MiChAeL', ''],  # Mixed case, extra spaces
        'LastName': ['  GARCIA  ', 'smith', 'JOHNSON', 'NoFirstName'],
        'StreetAddr': ['  123 Main Street  ', '456 oak avenue', '789 PINE ROAD', '321 Elm St Apt B'],
        'City': ['  LOS ANGELES  ', 'chicago', 'HOUSTON', 'phoenix'],
        'State': ['  ca  ', 'IL', 'tx', 'AZ'],  # Mixed case, extra spaces
        'PostalCode': ['90210-1234', '60601', '77001-5678', '85001'],
        'Notes': ['Good address', 'Needs cleaning', 'Upper case', 'Missing first name']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "08_messy_formatting.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Messy formatting (should be cleaned)")
    return filepath

def generate_file_9_po_boxes_and_special_cases(test_dir):
    """File 9: PO Boxes and special address cases"""
    data = {
        'first_name': ['Mary', 'James', 'Susan', 'Robert', 'Jennifer'],
        'last_name': ['Wilson', 'Rodriguez', 'Davis', 'Miller', 'Garcia'],
        'street_address': ['PO Box 12345', 'P.O. Box 67890', '123 Rural Route 1', 'General Delivery', '456 Highway 101'],
        'city': ['Rural Town', 'Small City', 'Farm Town', 'Remote Place', 'Highway City'],
        'state': ['MT', 'ND', 'SD', 'WY', 'NE'],
        'zip_code': ['59718', '58102', '57001', '82414', '68005']
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "09_po_boxes_special_cases.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - PO Boxes and special cases")
    return filepath

def generate_file_10_international_mixed(test_dir):
    """File 10: Mix of US and international addresses (internationals should be disqualified)"""
    data = {
        'first_name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Edward'],
        'last_name': ['Johnson', 'Smith', 'Brown', 'Wilson', 'Davis'],
        'street_address': ['123 Valid US Street', '45 Fake International Rd', '789 US Avenue', '12 London Street', '456 US Boulevard'],
        'city': ['New York', 'Toronto', 'Chicago', 'London', 'Boston'],
        'state': ['NY', 'ON', 'IL', 'UK', 'MA'],  # ON and UK are not US states
        'zip_code': ['10001', 'M5V 3A8', '60601', 'SW1A 1AA', '02101']  # Mixed US and international postal codes
    }
    
    df = pd.DataFrame(data)
    filepath = test_dir / "10_international_mixed.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ Created {filepath} - Mixed US/International (internationals should be disqualified)")
    return filepath

def generate_summary_file(test_dir, file_paths):
    """Generate a summary of all test files"""
    
    summary_data = []
    
    for i, filepath in enumerate(file_paths, 1):
        df = pd.read_csv(filepath)
        
        summary_data.append({
            'file_number': i,
            'filename': filepath.name,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': ', '.join(df.columns),
            'test_scenario': get_test_scenario_description(i),
            'expected_qualification': get_expected_qualification(i)
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_path = test_dir / "00_TEST_SUMMARY.csv"
    summary_df.to_csv(summary_path, index=False)
    
    print(f"\n📋 Created test summary: {summary_path}")
    return summary_path

def get_test_scenario_description(file_number):
    """Get description of what each test file tests"""
    descriptions = {
        1: "Standard format - perfect data",
        2: "Alternative column names (fname, lname, addr, etc.)",
        3: "Combined addresses in single field",
        4: "Split address fields (house_number, street_name, etc.)",
        5: "Full state names (California instead of CA)",
        6: "Mixed quality data (some missing/invalid fields)",
        7: "Business format with company names",
        8: "Messy formatting (case, spaces, inconsistencies)",
        9: "PO Boxes and special address cases",
        10: "Mixed US/International addresses"
    }
    return descriptions.get(file_number, "Unknown")

def get_expected_qualification(file_number):
    """Get expected qualification rate for each file"""
    expectations = {
        1: "100% qualified",
        2: "100% qualified",
        3: "100% qualified",
        4: "100% qualified",
        5: "100% qualified (after state conversion)",
        6: "60% qualified (3/5 - missing state, invalid state, invalid ZIP)",
        7: "100% qualified",
        8: "75% qualified (3/4 - one missing first name but address OK)",
        9: "100% qualified (PO Boxes are valid US addresses)",
        10: "60% qualified (3/5 - invalid states ON, UK)"
    }
    return expectations.get(file_number, "Unknown")

def create_readme_file(test_dir):
    """Create README with instructions"""
    
    readme_content = """# Test CSV Files for Address Standardization

This directory contains 10 test CSV files with various address input formats to test the enhanced address standardization and qualification process.

## Test Files Overview:

1. **01_standard_format.csv** - Perfect standard format (should be 100% qualified)
2. **02_alternative_columns.csv** - Alternative column names (fname, lname, addr, etc.)
3. **03_combined_addresses.csv** - Combined addresses in single field
4. **04_split_address_fields.csv** - Address split into detailed fields
5. **05_full_state_names.csv** - Full state names instead of abbreviations
6. **06_mixed_quality_data.csv** - Mixed quality with some invalid data
7. **07_business_format.csv** - Business-style format
8. **08_messy_formatting.csv** - Inconsistent formatting and case
9. **09_po_boxes_special_cases.csv** - PO Boxes and rural addresses
10. **10_international_mixed.csv** - Mix of US and international addresses

## How to Test:

1. Start your Streamlit app:
   ```bash
   streamlit run src/name_address_validator/app.py
   ```

2. Go to the "Enhanced Multi-File Processing" tab

3. Upload all 10 CSV files at once (or test individual files)

4. Click "Generate Standardization & Qualification Preview" to see:
   - How different formats are standardized
   - Which addresses qualify for USPS validation
   - What errors are found in problematic data

5. Click "Complete Processing Pipeline" to run full validation

## Expected Results:

- **Files 1-5**: Should have high qualification rates (90-100%)
- **File 6**: Mixed results (~60% qualified due to missing/invalid data)
- **Files 7-9**: Should handle special formats well
- **File 10**: Should disqualify international addresses

## What to Look For:

✅ **Column Mapping**: Different column names correctly mapped to standard format
✅ **Address Parsing**: Combined addresses split into components
✅ **State Conversion**: Full state names converted to 2-letter codes
✅ **Data Cleaning**: Messy formatting cleaned up
✅ **Qualification Logic**: Invalid addresses properly identified
✅ **Error Reporting**: Clear error messages for disqualified addresses

## Troubleshooting:

If you see unexpected results, check:
- File column mappings in the preview
- Qualification error messages
- Debug logs in the monitoring tab
"""
    
    readme_path = test_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"📖 Created README: {readme_path}")
    return readme_path

def main():
    """Generate all test files"""
    
    print("🚀 Generating 10 test CSV files with various address formats...\n")
    
    # Create test directory
    test_dir = create_test_data_directory()
    
    # Generate all test files
    file_paths = []
    
    file_paths.append(generate_file_1_standard_format(test_dir))
    file_paths.append(generate_file_2_alternative_columns(test_dir))
    file_paths.append(generate_file_3_combined_addresses(test_dir))
    file_paths.append(generate_file_4_split_address_fields(test_dir))
    file_paths.append(generate_file_5_full_state_names(test_dir))
    file_paths.append(generate_file_6_mixed_quality_data(test_dir))
    file_paths.append(generate_file_7_business_format(test_dir))
    file_paths.append(generate_file_8_messy_formatting(test_dir))
    file_paths.append(generate_file_9_po_boxes_and_special_cases(test_dir))
    file_paths.append(generate_file_10_international_mixed(test_dir))
    
    # Generate summary and documentation
    generate_summary_file(test_dir, file_paths)
    create_readme_file(test_dir)
    
    print(f"\n🎉 Successfully generated {len(file_paths)} test CSV files!")
    print(f"📁 All files saved in: {test_dir.absolute()}")
    
    print("\n📋 Test Files Summary:")
    for i, filepath in enumerate(file_paths, 1):
        df = pd.read_csv(filepath)
        scenario = get_test_scenario_description(i)
        expected = get_expected_qualification(i)
        print(f"   {i:2d}. {filepath.name:<35} - {df.shape[0]} rows, {df.shape[1]} cols - {scenario}")
        print(f"       Expected: {expected}")
    
    print(f"\n🧪 How to Test:")
    print(f"1. Start your app: streamlit run src/name_address_validator/app.py")
    print(f"2. Go to 'Enhanced Multi-File Processing' tab")
    print(f"3. Upload all files from: {test_dir.absolute()}")
    print(f"4. Test the standardization and qualification process")
    
    print(f"\n📖 See {test_dir}/README.md for detailed testing instructions")

if __name__ == "__main__":
    main()