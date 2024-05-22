"""
BaSec - Basically Secure

This module contains the basic security functions for the application.
"""

import string
import secrets
import random
import hashlib
import uuid

def clamp(value, min_value, max_value):
    """
    Clamp a value between a minimum and maximum value.

    :param value: The value to clamp
    :type value: int
    :param min_value: The minimum value
    :type min_value: int
    :param max_value: The maximum value
    :type max_value: int
    :return: The clamped value
    :rtype: int
    """
    return max(min(value, max_value), min_value)



def generate_number(length):
    """
    Generate a random number of a given length.

    :param length: The length of the number to generate
    :type length: int
    :return: The generated number
    :rtype: int
    """
    return clamp(random.randint(10 ** (length - 1), 10 ** length - 1), 2**31, 2**63-1)

def generate_string(length):
    """
    Generate a random string of a given length.

    :param length: The length of the string to generate
    :type length: int
    :return: The generated string
    :rtype: str
    """
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(length))

def generate_uuid():
    """
    Generate a UUID.

    :return: The generated UUID
    :rtype: str
    """
    return str(uuid.uuid4())

def hashpw(password):
    """
    Hash a password 1000 times using SHA256.

    :param password: The password to hash
    :type password: str
    :return: The hashed password
    :rtype: str
    """
    for i in range(1000):
        password = hashlib.sha256(password.encode()).hexdigest()

    return password