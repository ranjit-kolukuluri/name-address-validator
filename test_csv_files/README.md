# Test CSV Files for Address Standardization

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
