import re


FULL_NAME_REGEX = r'^[A-Za-z]+(?: [A-Za-z]+)*$'

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

PHONE_REGEX = r'^\d{10}$'

def validate_full_name(full_name):
    if not full_name:
        return 'Full name is required.'
    
    if not re.match(FULL_NAME_REGEX, full_name):
        return 'Full name must contain only letters and spaces (2-50 characters).'
    
    return None

def validate_email(email):
    if not email:
        return 'Email is required.'
    
    if len(email) >254:
        return 'Email is too long.'
    
    if not re.match(EMAIL_REGEX, email):
        return 'Enter a valid email address.'
    
    return None

def validate_password(password):
    if not password:
        return 'Password is required.'
    
    if not re.match(PASSWORD_REGEX, password):
        return (
            "Password must be at least 8 characters long and contain "
            "uppercase, lowercase, number and special character."
        )
    
    return None

def validate_phone(phone):
    if not phone:
        return 'Phone number is required.'
    
    if not re.match(PHONE_REGEX, phone):
        return 'Enter a valid 10-digit number.'
    
    return None

def validate_signup_data(data):
    errors = {}

    full_name = data.get('full_name', '').strip()
    full_name_error = validate_full_name(full_name)
    if full_name_error:
        errors['full_name'] = full_name_error

    email_error = validate_email(data.get('email', '').strip().lower())
    if email_error:
        errors['email'] = email_error 

    password_error = validate_password(data.get('password', ''))
    if password_error:
        errors['password'] = password_error

    confirm_password = data.get('confirm_password', '')
    if data.get('password') != confirm_password:
        errors['confirm_password'] = 'Passwords do not match'

    return errors

def validate_login_data(data):
    errors = {}

    email_error = validate_email(data.get('email', '').strip().lower())
    if email_error:
        errors['email'] = email_error 

    if not data.get('password'):
        errors['password'] = 'Password is required'

    return errors

def validate_forgot_password_data(data):
    errors = {}

    email_error = validate_email(data.get('email', '').strip().lower())
    if email_error:
        errors['email'] = email_error

    return errors

def validate_reset_password_data(data):
    errors = {}

    password_error = validate_password(data.get('password', ''))
    if password_error:
        errors['password'] = password_error

    if data.get('password') != data.get('confirm_password'):
        errors['confirm_password'] = 'Passwords do not match.'

    return errors

def validate_email_change_data(data, current_email):
    errors = {}

    email = data.get('email', '').strip().lower()
    email_error = validate_email(email)
    if email_error:
        errors['email'] = email_error
        return errors
    
    if email == current_email:
        errors['email'] = 'New email must be different.'

    return errors