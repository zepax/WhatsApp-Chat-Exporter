import os
import subprocess
import tempfile
import unittest

from phone_number_processing import process_phone_number, process_vcard


class TestVCardProcessor(unittest.TestCase):
    def test_process_phone_number(self) -> None:
        """Test the process_phone_number function with various inputs."""

        # Test cases for Mexican numbers (10 digits)
        test_cases_mexican = [
            # Standard Mexican mobile number
            ("6623402020", "+52 662 340 2020", None),
            # With country code prefix
            ("526623402020", "+52 662 340 2020", None),
            # With plus in country code
            ("+526623402020", "+52 662 340 2020", None),
            # With spaces and formatting
            ("+52 662 340 2020", "+52 662 340 2020", None),
            # Invalid Mexican numbers
            ("99927912345678", None, None),
            # With extra non-digit characters (invalid)
            ("+52-662-340.2020", "+52 662 340 2020", None),
        ]

        # Test cases for US numbers (10 digits)
        test_cases_us = [
            # US numbers with explicit country code
            ("+1 650 253 0000", "+1 650-253-0000", None),
            ("+16502530000", "+1 650-253-0000", None),
            # US numbers with extension
            ("+1 650-253-0000 ext123", "+1 650-253-0000 ext. 123", None),
        ]

        # Test cases for Brazilian numbers (legacy support when explicitly specified)
        test_cases_brazilian = [
            # Brazilian numbers should work when country code is provided
            ("+5527912345678", "+55 27 91234-5678", "+55 27 1234-5678"),
            # Without country code, might be interpreted as Mexican numbers
            (
                "2712345678",
                "+52 271 234 5678",
                None,
            ),  # This becomes a valid Mexican number
        ]

        # International numbers and extension handling
        international_cases = [
            ("+1 650-253-0000", "+1 650-253-0000", None),
            ("+44 20 7031 3000", "+44 20 7031 3000", None),
            ("+1 650-253-0000 ext123", "+1 650-253-0000 ext. 123", None),
            # Mexican numbers
            ("+52 662 340 2020", "+52 662 340 2020", None),
            ("52 662 340 2020", "+52 662 340 2020", None),
            # Spanish numbers
            ("+34 91 123 45 67", "+34 911 23 45 67", None),
            # Colombian numbers
            ("+57 1 234 5678", None, None),
        ]

        # Edge cases
        edge_cases = [
            # Too few digits
            ("271234567", None, None),
            # Empty string
            ("", None, None),
            # Non-numeric characters only
            ("abc-def+ghi", None, None),
            # Single digit
            ("1", None, None),
            # Unusual formatting but valid number
            ("(+55) [27] 9.1234_5678", None, None),
        ]

        # Run tests for all cases
        all_cases = (
            test_cases_mexican
            + test_cases_us
            + test_cases_brazilian
            + international_cases
            + edge_cases
        )

        for raw_phone, expected_orig, expected_mod in all_cases:
            with self.subTest(raw_phone=raw_phone):
                orig, mod = process_phone_number(raw_phone)
                self.assertEqual(orig, expected_orig)
                self.assertEqual(mod, expected_mod)

    def test_process_vcard(self) -> None:
        """Test the process_vcard function with various VCARD formats."""

        # Test case 1: Standard TEL entries with Mexican numbers
        vcard1 = """BEGIN:VCARD
VERSION:3.0
N:Doe;John;;;
FN:John Doe
TEL:6623402020
TEL:+526623402021
END:VCARD
"""
        expected1 = """BEGIN:VCARD
VERSION:3.0
N:Doe;John;;;
FN:John Doe
TEL;TYPE=CELL:+52 662 340 2020
TEL;TYPE=CELL:+52 662 340 2021
END:VCARD
"""

        # Test case 2: TEL entries with TYPE attributes
        vcard2 = """BEGIN:VCARD
VERSION:3.0
N:Smith;Jane;;;
FN:Jane Smith
TEL;TYPE=CELL:6623402020
TEL;TYPE=HOME:+526623402021
END:VCARD
"""
        expected2 = """BEGIN:VCARD
VERSION:3.0
N:Smith;Jane;;;
FN:Jane Smith
TEL;TYPE=CELL:+52 662 340 2020
TEL;TYPE=HOME:+52 662 340 2021
END:VCARD
"""

        # Test case 3: Complex TEL entries with prefixes
        vcard3 = """BEGIN:VCARD
VERSION:3.0
N:Brown;Robert;;;
FN:Robert Brown
item1.TEL:+526623402020
item2.TEL;TYPE=CELL:6623402021
END:VCARD
"""
        expected3 = """BEGIN:VCARD
VERSION:3.0
N:Brown;Robert;;;
FN:Robert Brown
TEL;TYPE=CELL:+52 662 340 2020
item2.TEL;TYPE=CELL:+52 662 340 2021
END:VCARD
"""

        # Test case 4: Mixed valid and invalid phone numbers
        vcard4 = """BEGIN:VCARD
VERSION:3.0
N:White;Alice;;;
FN:Alice White
TEL:123
TEL:+526623402020
END:VCARD
"""
        expected4 = """BEGIN:VCARD
VERSION:3.0
N:White;Alice;;;
FN:Alice White
TEL:123
TEL;TYPE=CELL:+52 662 340 2020
END:VCARD
"""

        # Test case 5: Multiple contacts with different formats
        vcard5 = """BEGIN:VCARD
VERSION:3.0
N:Johnson;Mike;;;
FN:Mike Johnson
TEL:6623402020
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Williams;Sarah;;;
FN:Sarah Williams
TEL;TYPE=CELL:6623402021
END:VCARD
"""
        expected5 = """BEGIN:VCARD
VERSION:3.0
N:Johnson;Mike;;;
FN:Mike Johnson
TEL;TYPE=CELL:+52 662 340 2020
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Williams;Sarah;;;
FN:Sarah Williams
TEL;TYPE=CELL:+52 662 340 2021
END:VCARD
"""

        # Test case 7: International numbers (Mexican, US, Spanish)
        vcard7 = """BEGIN:VCARD
VERSION:3.0
N:Garcia;Juan;;;
FN:Juan Garcia
TEL:+52 662 340 2020
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Smith;John;;;
FN:John Smith
TEL:+1 650 253 0000
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Rodriguez;Maria;;;
FN:Maria Rodriguez
  TEL:+34 91 123 45 67
END:VCARD
"""
        expected7 = """BEGIN:VCARD
VERSION:3.0
N:Garcia;Juan;;;
FN:Juan Garcia
TEL;TYPE=CELL:+52 662 340 2020
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Smith;John;;;
FN:John Smith
TEL;TYPE=CELL:+1 650-253-0000
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Rodriguez;Maria;;;
FN:Maria Rodriguez
TEL;TYPE=CELL:+34 911 23 45 67
END:VCARD
"""

        # Test case 6: VCARD with no phone numbers
        vcard6 = """BEGIN:VCARD
VERSION:3.0
N:Davis;Tom;;;
FN:Tom Davis
EMAIL:tom@example.com
END:VCARD
"""
        expected6 = """BEGIN:VCARD
VERSION:3.0
N:Davis;Tom;;;
FN:Tom Davis
EMAIL:tom@example.com
END:VCARD
"""

        test_cases = [
            (vcard1, expected1),
            (vcard2, expected2),
            (vcard3, expected3),
            (vcard4, expected4),
            (vcard5, expected5),
            (vcard6, expected6),
            (vcard7, expected7),
        ]

        for i, (input_vcard, expected_output) in enumerate(test_cases):
            with self.subTest(case=i + 1):
                # Create temporary files for input and output
                with tempfile.NamedTemporaryFile(
                    mode="w+", delete=False, encoding="utf-8"
                ) as input_file:
                    input_file.write(input_vcard)
                    input_path = input_file.name

                output_path = input_path + ".out"

                try:
                    # Process the VCARD
                    process_vcard(input_path, output_path)

                    # Read and verify the output
                    with open(output_path, "r", encoding="utf-8") as output_file:
                        actual_output = output_file.read()

                    self.assertEqual(actual_output, expected_output)

                finally:
                    # Clean up temporary files
                    if os.path.exists(input_path):
                        os.unlink(input_path)
                    if os.path.exists(output_path):
                        os.unlink(output_path)

    def test_script_argument_handling(self) -> None:
        """Test the script's command-line argument handling."""

        test_input = """BEGIN:VCARD
VERSION:3.0
N:Test;User;;;
FN:User Test
TEL:+5527912345678
END:VCARD
"""

        # Create a temporary input file
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, encoding="utf-8"
        ) as input_file:
            input_file.write(test_input)
            input_path = input_file.name

        output_path = input_path + ".out"

        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "phone_number_processing.py"
            )
            test_args = [
                "python" if os.name == "nt" else "python3",
                script_path,
                input_path,
                output_path,
                "--region",
                "MX",
            ]
            # We're just testing that the argument parsing works
            subprocess.call(
                test_args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
            )
            # Check if the output file was created
            self.assertTrue(os.path.exists(output_path))

        finally:
            # Clean up temporary files
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == "__main__":
    unittest.main()
