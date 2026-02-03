import time
import random

def generate_otp():
    return str(random.randint(100000, 999999))


def clear_email_change_session(request):
    keys = [
        'email_change_otp',
        'email_change_new_email',
        'email_change_time',
        'email_change_attempts',
    ]
    for key in keys:
        request.session.pop(key, None)
