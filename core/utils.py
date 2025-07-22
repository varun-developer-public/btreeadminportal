import os
import time

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