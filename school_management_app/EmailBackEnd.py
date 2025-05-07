# school_management_app/EmailBackEnd.py

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q # Import Q objects for OR query


class EmailBackEnd(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Try to find the user by username OR email
            # Use Q objects for an OR query
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username)) # Use __iexact for case-insensitive match
        except UserModel.DoesNotExist:
            # If user not found by username or email, return None
            return None
        except Exception as e:
            # Catch other potential database errors
            print(f"Error in EmailBackEnd authentication: {e}")
            return None

        # If a user was found, check the password
        if user.check_password(password):
            # If password matches, return the user object
            return user
        else:
            # If password does not match, return None
            return None

    # It's also good practice to implement the get_user method if you override authenticate
    # Although ModelBackend provides a default get_user that works with the default user model,
    # explicitly defining it can be clearer and necessary with custom user models or backends.
    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None