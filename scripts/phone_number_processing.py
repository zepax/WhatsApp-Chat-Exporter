"""
Utility functions to normalize and format telephone numbers found in VCARD
files. Uses the :mod:`phonenumbers` package to work with phone numbers from any
country. Primarily designed for Mexican (MX) and US phone numbers, with support
for international numbers including Brazilian legacy compatibility.

Originally contributed by @magpires, adapted for MX/US focus
"""

import argparse
import re
from typing import Optional, Tuple

import phonenumbers  # type: ignore
from phonenumbers import PhoneNumber, PhoneNumberFormat


def process_phone_number(
    raw_phone: str, default_region: str = "MX"
) -> Tuple[Optional[str], Optional[str]]:
    """Return international phone number formats for MX/US focused processing.

    The function returns a tuple ``(original, modified)``. ``original`` is the
    international representation of ``raw_phone``. ``modified`` is populated
    for special cases (Brazilian mobile numbers with ninth digit removal,
    or US numbers with extensions). Both values are ``None`` if the number
    cannot be parsed.

    Args:
        raw_phone: Raw phone number string to process
        default_region: Default region (MX for Mexico, US for United States)

    Returns:
        Tuple of (formatted_number, alternative_format) or (None, None)
    """

    try:
        parsed: PhoneNumber = phonenumbers.parse(raw_phone, default_region)
    except phonenumbers.NumberParseException:
        return None, None

    if not (
        phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed)
    ):
        return None, None

    original_formatted = phonenumbers.format_number(
        parsed, PhoneNumberFormat.INTERNATIONAL
    )

    modified_formatted: Optional[str] = None
    region = phonenumbers.region_code_for_number(parsed)

    # Region-specific formatting and processing
    if region == "MX":
        # Mexican numbers: +52 area subscriber
        # Standard format is already good from phonenumbers
        pass

    elif region == "US":
        # US numbers: +1 area subscriber
        # Standard format is already good from phonenumbers
        # Handle extensions if present
        if " ext" in raw_phone.lower() or " extension" in raw_phone.lower():
            # Keep the standard format as phonenumbers handles extensions
            pass

    elif region == "BR":
        # Brazilian-specific formatting and legacy support
        digits = phonenumbers.national_significant_number(parsed)
        area = digits[:2]
        subscriber = digits[2:]

        # phonenumbers does not insert a hyphen for landline numbers, add one for consistency
        if len(subscriber) == 8:
            original_formatted = f"+55 {area} {subscriber[:4]}-{subscriber[4:]}"
        elif len(subscriber) == 9:
            original_formatted = f"+55 {area} {subscriber[:5]}-{subscriber[5:]}"
            mod_digits = subscriber[1:]
            _mod_number = phonenumbers.parse(f"+55{area}{mod_digits}", "BR")
            modified_formatted = f"+55 {area} {mod_digits[:4]}-{mod_digits[4:]}"

    return original_formatted, modified_formatted


def process_vcard(
    input_vcard: str, output_vcard: str, default_region: str = "MX"
) -> None:
    """
    Process a VCARD file to standardize telephone entries for MX/US numbers.

    - Normalizes phone numbers to international format
    - Primarily designed for Mexican (+52) and US (+1) numbers
    - Adds legacy Brazilian number compatibility when needed
    - Standardizes TEL field formatting in vCard entries

    Args:
        input_vcard: Path to input vCard file
        output_vcard: Path to output processed vCard file
        default_region: Default region for numbers without country code (MX/US)
    """
    with open(input_vcard, "r", encoding="utf-8") as file:
        lines = file.readlines()

    output_lines = []

    # Regex to capture any telephone line.
    # It matches lines starting with "TEL:" or "TEL;TYPE=..." or with prefixes like "item1.TEL:".
    phone_pattern = re.compile(r"^(?P<prefix>.*TEL(?:;TYPE=[^:]+)?):(?P<number>.*)$")

    for line in lines:
        stripped_line = line.rstrip("\n")
        match = phone_pattern.match(stripped_line)
        if match:
            raw_phone = match.group("number").strip()
            orig_formatted, mod_formatted = process_phone_number(
                raw_phone, default_region
            )
            if orig_formatted:
                prefix = match.group("prefix")
                if "TYPE" in prefix:
                    output_prefix = prefix
                else:
                    output_prefix = "TEL;TYPE=CELL"
                output_lines.append(f"{output_prefix}:{orig_formatted}\n")
            else:
                output_lines.append(line)
            if mod_formatted:
                output_lines.append(f"TEL;TYPE=CELL:{mod_formatted}\n")
        else:
            output_lines.append(line)

    with open(output_vcard, "w", encoding="utf-8") as file:
        file.writelines(output_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Process a VCARD file to standardize telephone entries for international "
            "format. Primarily designed for Mexican (MX) and US phone numbers. "
            "Includes legacy Brazilian mobile number support when needed."
        )
    )
    parser.add_argument("input_vcard", type=str, help="Input VCARD file")
    parser.add_argument("output_vcard", type=str, help="Output VCARD file")
    parser.add_argument(
        "--region",
        default="MX",
        help="Default region for numbers without country code (MX=Mexico, US=United States, or any ISO 3166-1 alpha-2 code)",
    )
    args = parser.parse_args()

    process_vcard(args.input_vcard, args.output_vcard, args.region)
    print(f"VCARD processed and saved to {args.output_vcard}")
