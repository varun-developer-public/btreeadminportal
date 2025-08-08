import os
import time
import pycountry
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

def timestamp_upload_to(instance, filename):
    """
    Appends a timestamp to the filename for payment proofs.
    """
    path = "payment_proofs/"
    timestamp = str(int(time.time()))
    return os.path.join(path, f"{timestamp}_{filename}")

def profile_pics_upload_to(instance, filename):
    """
    Generates a unique filename for profile pictures using a timestamp.
    """
    path = "profile_pics/"
    timestamp = str(int(time.time()))
    base, extension = os.path.splitext(filename)
    new_filename = f"{base}_{timestamp}{extension}"
    return os.path.join(path, new_filename)

def get_country_codes():
    countries = []
    for code, region_codes in COUNTRY_CODE_TO_REGION_CODE.items():
        for region_code in region_codes:
            try:
                country = pycountry.countries.get(alpha_2=region_code)
                if country:
                    countries.append((f"+{code}", f"{country.name} (+{code})", country.alpha_2.lower()))
            except (KeyError, AttributeError):
                continue
    return sorted(list(set(countries)), key=lambda x: x[1])

def get_country_code_choices():
    country_codes = get_country_codes()
    return [(code, name) for code, name, flag in country_codes]