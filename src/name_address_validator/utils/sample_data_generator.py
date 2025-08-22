# src/name_address_validator/utils/sample_data_generator.py
"""
Sample CSV data generator for testing various address formats
"""

import pandas as pd
import random
from typing import Dict, List
import os


class SampleDataGenerator:
    """Generate sample CSV files with various address formats for testing"""
    
    def __init__(self):
        self.sample_names = [
            ('John', 'Smith'), ('Jane', 'Doe'), ('Michael', 'Johnson'), ('Sarah', 'Williams'),
            ('David', 'Brown'), ('Emily', 'Jones'), ('Robert', 'Garcia'), ('Lisa', 'Miller'),
            ('William', 'Davis'), ('Jessica', 'Rodriguez'), ('James', 'Martinez'), ('Ashley', 'Hernandez'),
            ('Christopher', 'Lopez'), ('Amanda', 'Gonzalez'), ('Matthew', 'Wilson'), ('Melissa', 'Anderson')
        ]
        
        self.sample_addresses = [
            ('123 Main Street', 'New York', 'NY', '10001'),
            ('456 Oak Avenue', 'Los Angeles', 'CA', '90210'),
            ('789 Pine Road', 'Chicago', 'IL', '60601'),
            ('321 Elm Street', 'Houston', 'TX', '77001'),
            ('654 Maple Drive', 'Phoenix', 'AZ', '85001'),
            ('987 Cedar Lane', 'Philadelphia', 'PA', '19101'),
            ('147 Birch Way', 'San Antonio', 'TX', '78201'),
            ('258 Walnut Court', 'San Diego', 'CA', '92101'),
            ('369 Cherry Street', 'Dallas', 'TX', '75201'),
            ('741 Ash Boulevard', 'San Jose', 'CA', '95101'),
            ('852 Hickory Drive', 'Austin', 'TX', '73301'),
            ('963 Willow Lane', 'Jacksonville', 'FL', '32099'),
            ('159 Poplar Avenue', 'Fort Worth', 'TX', '76101'),
            ('357 Spruce Road', 'Columbus', 'OH', '43085'),
            ('486 Sycamore Street', 'Charlotte', 'NC', '28201')
        ]
        
        self.apartment_suffixes = ['Apt 1A', 'Unit 205', 'Suite 300', '#4B', 'Floor 2', 'Apt B']
    
    def generate_standard_format(self, num_records: int = 50) -> pd.DataFrame:
        """Generate CSV with standard column names"""
        
        data = []
        for i in range(num_records):
            first_name, last_name = random.choice(self.sample_names)
            street, city, state, zip_code = random.choice(self.sample_addresses)
            
            # Sometimes add apartment
            if random.random() < 0.3:
                street += f" {random.choice(self.apartment_suffixes)}"
            
            # Sometimes add ZIP+4
            if random.random() < 0.4:
                zip_code += f"-{random.randint(1000, 9999)}"
            
            data.append({
                'first_name': first_name,
                'last_name': last_name,
                'street_address': street,
                'city': city,
                'state': state,
                'zip_code': zip_code
            })
        
        return pd.DataFrame(data)
    
    def generate_alternative_columns(self, num_records: int = 50) -> pd.DataFrame:
        """Generate CSV with alternative column names"""
        
        data = []
        for i in range(num_records):
            first_name, last_name = random.choice(self.sample_names)
            street, city, state, zip_code = random.choice(self.sample_addresses)
            
            if random.random() < 0.3:
                street += f" {random.choice(self.apartment_suffixes)}"
            
            if random.random() < 0.4:
                zip_code += f"-{random.randint(1000, 9999)}"
            
            data.append({
                'fname': first_name,
                'lname': last_name,
                'addr': street,
                'town': city,
                'st': state,
                'postal': zip_code
            })
        
        return pd.DataFrame(data)
    
    def generate_split_address_format(self, num_records: int = 50) -> pd.DataFrame:
        """Generate CSV with address split into multiple columns"""
        
        data = []
        for i in range(num_records):
            first_name, last_name = random.choice(self.sample_names)
            street, city, state, zip_code = random.choice(self.sample_addresses)
            
            # Split street into number and name
            street_parts = street.split(' ', 2)
            street_number = street_parts[0] if street_parts else ''
            street_name = ' '.join(street_parts[1:]) if len(street_parts) > 1 else street
            
            apartment = random.choice(self.apartment_suffixes) if random.random() < 0.3 else ''
            
            if random.random() < 0.4:
                zip_code += f"-{random.randint(1000, 9999)}"
            
            data.append({
                'given_name': first_name,
                'family_name': last_name,
                'house_number': street_number,
                'street_name': street_name,
                'apartment': apartment,
                'city_name': city,
                'state_code': state,
                'zip5': zip_code.split('-')[0],
                'zip4': zip_code.split('-')[1] if '-' in zip_code else ''
            })
        
        return pd.DataFrame(data)
    
    def generate_combined_address_format(self, num_records: int = 50) -> pd.DataFrame:
        """Generate CSV with combined address in single field"""
        
        data = []
        for i in range(num_records):
            first_name, last_name = random.choice(self.sample_names)
            street, city, state, zip_code = random.choice(self.sample_addresses)
            
            if random.random() < 0.3:
                street += f" {random.choice(self.apartment_suffixes)}"
            
            if random.random() < 0.4:
                zip_code += f"-{random.randint(1000, 9999)}"
            
            # Create combined address with different formats
            format_choice = random.choice([
                f"{street}, {city}, {state} {zip_code}",
                f"{street} {city}, {state} {zip_code}",
                f"{street}, {city} {state} {zip_code}"
            ])
            
            data.append({
                'first': first_name,
                'last': last_name,
                'full_address': format_choice,
                'customer_id': f"CUST{1000 + i}"
            })
        
        return pd.DataFrame(data)
    
    def generate_messy_format(self, num_records: int = 50) -> pd.DataFrame:
        """Generate CSV with inconsistent and messy formatting"""
        
        data = []
        for i in range(num_records):
            first_name, last_name = random.choice(self.sample_names)
            street, city, state, zip_code = random.choice(self.sample_addresses)
            
            # Add some inconsistencies
            if random.random() < 0.2:
                first_name = first_name.upper()
            if random.random() < 0.2:
                last_name = last_name.lower()
            if random.random() < 0.2:
                city = city.upper()
            if random.random() < 0.2:
                state = state.lower()
            
            # Sometimes add extra spaces
            if random.random() < 0.3:
                street = f"  {street}  "
                city = f"  {city}  "
            
            # Sometimes add apartment in different ways
            if random.random() < 0.3:
                street += f" {random.choice(self.apartment_suffixes)}"
            
            # Mix ZIP formats
            if random.random() < 0.3:
                zip_code = f"{zip_code}-{random.randint(1000, 9999)}"
            elif random.random() < 0.1:
                zip_code = f"{zip_code[:3]} {zip_code[3:]}"  # Malformed
            
            data.append({
                'FirstName': first_name,
                'LastName': last_name,
                'StreetAddr': street,
                'City': city,
                'State': state,
                'PostalCode': zip_code,
                'Notes': f"Record {i+1}"
            })
        
        return pd.DataFrame(data)
    
    def generate_business_format(self, num_records: int = 50) -> pd.DataFrame:
        """Generate CSV with business-style formatting"""
        
        business_names = [
            'Acme Corporation', 'Global Industries Inc', 'TechStart LLC', 'Metro Services',
            'Prime Solutions', 'Advanced Systems', 'Quality Products Inc', 'First National',
            'Central Office', 'Modern Enterprises', 'Professional Services', 'Elite Group'
        ]
        
        business_addresses = [
            ('100 Business Park Dr', 'Atlanta', 'GA', '30309'),
            ('250 Corporate Center', 'Denver', 'CO', '80202'),
            ('500 Industrial Blvd', 'Memphis', 'TN', '38103'),
            ('750 Commerce Way', 'Portland', 'OR', '97201'),
            ('1000 Executive Plaza', 'Nashville', 'TN', '37201'),
            ('1250 Technology Dr', 'Austin', 'TX', '78701'),
            ('1500 Professional Ct', 'Seattle', 'WA', '98101')
        ]
        
        data = []
        for i in range(num_records):
            # Mix of business contacts and individual names
            if random.random() < 0.7:
                first_name, last_name = random.choice(self.sample_names)
                company = random.choice(business_names)
            else:
                first_name = ''
                last_name = random.choice(business_names)
                company = ''
            
            street, city, state, zip_code = random.choice(business_addresses)
            
            # Business addresses often have suite numbers
            if random.random() < 0.6:
                suite_num = random.randint(100, 999)
                street += f" Suite {suite_num}"
            
            if random.random() < 0.5:
                zip_code += f"-{random.randint(1000, 9999)}"
            
            data.append({
                'contact_first': first_name,
                'contact_last': last_name,
                'company_name': company,
                'mailing_address': street,
                'municipality': city,
                'province': state,
                'postal': zip_code,
                'business_type': random.choice(['Office', 'Retail', 'Warehouse', 'Medical'])
            })
        
        return pd.DataFrame(data)
    
    def generate_all_sample_files(self, output_dir: str = "sample_csvs") -> Dict[str, str]:
        """Generate all sample CSV files and save them"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        files_created = {}
        
        # Generate different format samples
        formats = {
            'standard_format.csv': self.generate_standard_format(30),
            'alternative_columns.csv': self.generate_alternative_columns(25),
            'split_address.csv': self.generate_split_address_format(20),
            'combined_address.csv': self.generate_combined_address_format(35),
            'messy_format.csv': self.generate_messy_format(40),
            'business_format.csv': self.generate_business_format(25)
        }
        
        for filename, df in formats.items():
            filepath = os.path.join(output_dir, filename)
            df.to_csv(filepath, index=False)
            files_created[filename] = filepath
            print(f"Created {filename} with {len(df)} records")
        
        return files_created
    
    def generate_validation_test_set(self, output_dir: str = "test_csvs") -> Dict[str, str]:
        """Generate test files with known good and bad addresses for validation testing"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Known good addresses (real, deliverable addresses)
        good_addresses = [
            ('John', 'Doe', '1600 Pennsylvania Avenue NW', 'Washington', 'DC', '20500'),
            ('Jane', 'Smith', '350 Fifth Avenue', 'New York', 'NY', '10118'),
            ('Michael', 'Johnson', '1 Apple Park Way', 'Cupertino', 'CA', '95014'),
            ('Sarah', 'Williams', '1 Microsoft Way', 'Redmond', 'WA', '98052'),
            ('David', 'Brown', '410 Terry Avenue North', 'Seattle', 'WA', '98109')
        ]
        
        # Known problematic addresses for testing error handling
        bad_addresses = [
            ('Test', 'User', '123 Fake Street', 'Nowhere', 'XX', '00000'),
            ('Invalid', 'Address', '999 Nonexistent Blvd', 'Faketown', 'ZZ', '99999'),
            ('Bad', 'Data', '', '', '', ''),
            ('Incomplete', 'Info', '456 Partial St', '', 'CA', ''),
            ('Wrong', 'Format', '789 Street Name Without Number', 'City', 'California', 'InvalidZip')
        ]
        
        files_created = {}
        
        # Good addresses file
        good_df = pd.DataFrame(good_addresses, columns=['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code'])
        good_file = os.path.join(output_dir, 'known_good_addresses.csv')
        good_df.to_csv(good_file, index=False)
        files_created['known_good_addresses.csv'] = good_file
        
        # Bad addresses file
        bad_df = pd.DataFrame(bad_addresses, columns=['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code'])
        bad_file = os.path.join(output_dir, 'known_bad_addresses.csv')
        bad_df.to_csv(bad_file, index=False)
        files_created['known_bad_addresses.csv'] = bad_file
        
        # Mixed file
        mixed_data = good_addresses + bad_addresses
        random.shuffle(mixed_data)
        mixed_df = pd.DataFrame(mixed_data, columns=['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code'])
        mixed_file = os.path.join(output_dir, 'mixed_validation_test.csv')
        mixed_df.to_csv(mixed_file, index=False)
        files_created['mixed_validation_test.csv'] = mixed_file
        
        print(f"Created validation test files in {output_dir}")
        return files_created


def main():
    """CLI interface for generating sample data"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample CSV files for address validation testing')
    parser.add_argument('--output-dir', default='sample_csvs', help='Output directory for sample files')
    parser.add_argument('--test-files', action='store_true', help='Generate validation test files')
    parser.add_argument('--all-formats', action='store_true', help='Generate all format samples')
    
    args = parser.parse_args()
    
    generator = SampleDataGenerator()
    
    if args.test_files:
        test_files = generator.generate_validation_test_set()
        print("Validation test files created:")
        for filename, path in test_files.items():
            print(f"  {filename}: {path}")
    
    if args.all_formats:
        sample_files = generator.generate_all_sample_files(args.output_dir)
        print("Sample files created:")
        for filename, path in sample_files.items():
            print(f"  {filename}: {path}")
    
    if not args.test_files and not args.all_formats:
        print("No action specified. Use --test-files or --all-formats")
        print("Example: python sample_data_generator.py --all-formats --output-dir my_samples")


if __name__ == "__main__":
    main()