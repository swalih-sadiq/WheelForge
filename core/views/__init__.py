from .home_views import home_view

from .auth_views import (
    signup_view,
    login_view,
    logout_view,
)

from .otp_views import (
    verify_otp_view,
    resend_otp_view,
)

from .profile_views import (
    profile_view,
    upload_profile_image_view,
    edit_profile_view,
)

from .password_views import (
    forgot_password_view,
    verify_forgot_otp_view,
    reset_password_view,
)
