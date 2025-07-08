<<<<<<< HEAD
"""
Utility functions to normalise and format telephone numbers found in VCARD
files.  Originally tailored for Brazilian numbers, the implementation now relies
on the :mod:`phonenumbers` package so it works for phone numbers from any
country.  For Brazilian mobile numbers an additional entry is added without the
extra ninth digit.

Contributed by @magpires
"""
import re
import argparse
from typing import Optional, Tuple

import phonenumbers
from phonenumbers import PhoneNumber, PhoneNumberFormat

def process_phone_number(raw_phone: str, default_region: str = "BR") -> Tuple[Optional[str], Optional[str]]:
    """Return international phone number formats.

    The function returns a tuple ``(original, modified)``. ``original`` is the
    international representation of ``raw_phone``. ``modified`` is only
    populated for Brazilian mobile numbers where the additional ninth digit is
    removed.  Both values are ``None`` if the number cannot be parsed.
    """

    try:
        parsed: PhoneNumber = phonenumbers.parse(raw_phone, default_region)
    except phonenumbers.NumberParseException:
        return None, None

    if not (phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed)):
        return None, None

    original_formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)

    modified_formatted: Optional[str] = None

    if phonenumbers.region_code_for_number(parsed) == "BR":
        digits = phonenumbers.national_significant_number(parsed)
        area = digits[:2]
        subscriber = digits[2:]

        # phonenumbers does not insert a hyphen for landline numbers, add one for consistency
        if len(subscriber) == 8:
            original_formatted = f"+55 {area} {subscriber[:4]}-{subscriber[4:]}"
        elif len(subscriber) == 9:
            original_formatted = f"+55 {area} {subscriber[:5]}-{subscriber[5:]}"
            mod_digits = subscriber[1:]
            mod_number = phonenumbers.parse(f"+55{area}{mod_digits}", "BR")
            modified_formatted = f"+55 {area} {mod_digits[:4]}-{mod_digits[4:]}"

    return original_formatted, modified_formatted

def process_vcard(input_vcard: str, output_vcard: str, default_region: str = "BR") -> None:
    """
    Process a VCARD file to standardize telephone entries and add a second TEL line
    with the modified number (removing the extra ninth digit) for contacts with 9-digit subscribers.
    """
    with open(input_vcard, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    output_lines = []
    
    # Regex to capture any telephone line.
    # It matches lines starting with "TEL:" or "TEL;TYPE=..." or with prefixes like "item1.TEL:".
    phone_pattern = re.compile(r'^(?P<prefix>.*TEL(?:;TYPE=[^:]+)?):(?P<number>.*)$')
    
    for line in lines:
        stripped_line = line.rstrip("\n")
        match = phone_pattern.match(stripped_line)
        if match:
            raw_phone = match.group("number").strip()
            orig_formatted, mod_formatted = process_phone_number(raw_phone, default_region)
            if orig_formatted:
                # Always output using the standardized prefix.
                output_lines.append(f"TEL;TYPE=CELL:{orig_formatted}\n")
            else:
                output_lines.append(line)
            if mod_formatted:
                output_lines.append(f"TEL;TYPE=CELL:{mod_formatted}\n")
        else:
            output_lines.append(line)
    
    with open(output_vcard, 'w', encoding='utf-8') as file:
        file.writelines(output_lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Process a VCARD file to standardise telephone entries. For Brazilian "
            "mobile numbers an extra TEL line without the ninth digit is added."
        )
    )
    parser.add_argument("input_vcard", type=str, help="Input VCARD file")
    parser.add_argument("output_vcard", type=str, help="Output VCARD file")
    parser.add_argument(
        "--region",
        default="BR",
        help="Default region for numbers without country code (ISO 3166-1 alpha-2)",
    )
    args = parser.parse_args()

    process_vcard(args.input_vcard, args.output_vcard, args.region)
=======
"""
Utility functions to normalise and format telephone numbers found in VCARD
files.  Originally tailored for Brazilian numbers, the implementation now relies
on the :mod:`phonenumbers` package so it works for phone numbers from any
country.  For Brazilian mobile numbers an additional entry is added without the
extra ninth digit.

Contributed by @magpires
"""
import re
import argparse
from typing import Optional, Tuple

import phonenumbers
from phonenumbers import PhoneNumber, PhoneNumberFormat

def process_phone_number(raw_phone: str, default_region: str = "BR") -> Tuple[Optional[str], Optional[str]]:
    """Return international phone number formats.

    The function returns a tuple ``(original, modified)``. ``original`` is the
    international representation of ``raw_phone``. ``modified`` is only
    populated for Brazilian mobile numbers where the additional ninth digit is
    removed.  Both values are ``None`` if the number cannot be parsed.
    """

    try:
        parsed: PhoneNumber = phonenumbers.parse(raw_phone, default_region)
    except phonenumbers.NumberParseException:
        return None, None

    if not (phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed)):
        return None, None

    original_formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)

    modified_formatted: Optional[str] = None

    if phonenumbers.region_code_for_number(parsed) == "BR":
        digits = phonenumbers.national_significant_number(parsed)
        area = digits[:2]
        subscriber = digits[2:]

        # phonenumbers does not insert a hyphen for landline numbers, add one for consistency
        if len(subscriber) == 8:
            original_formatted = f"+55 {area} {subscriber[:4]}-{subscriber[4:]}"
        elif len(subscriber) == 9:
            original_formatted = f"+55 {area} {subscriber[:5]}-{subscriber[5:]}"
            mod_digits = subscriber[1:]
            mod_number = phonenumbers.parse(f"+55{area}{mod_digits}", "BR")
            modified_formatted = f"+55 {area} {mod_digits[:4]}-{mod_digits[4:]}"

    return original_formatted, modified_formatted

def process_vcard(input_vcard: str, output_vcard: str, default_region: str = "BR") -> None:
    """
    Process a VCARD file to standardize telephone entries and add a second TEL line
    with the modified number (removing the extra ninth digit) for contacts with 9-digit subscribers.
    """
    with open(input_vcard, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    output_lines = []
    
    # Regex to capture any telephone line.
    # It matches lines starting with "TEL:" or "TEL;TYPE=..." or with prefixes like "item1.TEL:".
    phone_pattern = re.compile(r'^(?P<prefix>.*TEL(?:;TYPE=[^:]+)?):(?P<number>.*)$')
    
    for line in lines:
        stripped_line = line.rstrip("\n")
        match = phone_pattern.match(stripped_line)
        if match:
            raw_phone = match.group("number").strip()
            orig_formatted, mod_formatted = process_phone_number(raw_phone, default_region)
            if orig_formatted:
                # Always output using the standardized prefix.
                output_lines.append(f"TEL;TYPE=CELL:{orig_formatted}\n")
            else:
                output_lines.append(line)
            if mod_formatted:
                output_lines.append(f"TEL;TYPE=CELL:{mod_formatted}\n")
        else:
            output_lines.append(line)
    
    with open(output_vcard, 'w', encoding='utf-8') as file:
        file.writelines(output_lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Process a VCARD file to standardise telephone entries. For Brazilian "
            "mobile numbers an extra TEL line without the ninth digit is added."
        )
    )
    parser.add_argument("input_vcard", type=str, help="Input VCARD file")
    parser.add_argument("output_vcard", type=str, help="Output VCARD file")
    parser.add_argument(
        "--region",
        default="BR",
        help="Default region for numbers without country code (ISO 3166-1 alpha-2)",
    )
    args = parser.parse_args()

    process_vcard(args.input_vcard, args.output_vcard, args.region)
>>>>>>> 0b087d242fb332e1e94c87caa74b2b5dc3ef79a0
    print(f"VCARD processed and saved to {args.output_vcard}")