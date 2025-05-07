# school_management_app/views.py

# ... (Keep all your existing imports at the top) ...
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse # Ensure reverse is imported

from school_management_app.EmailBackEnd import EmailBackEnd

# Create your views here.

def Logindon(request):
    return render(request, "login_page.html")

def Demopage(request):
    return render(request, "demo.html")

def doLogin(request):
    if request.method != "POST":
        # Consider rendering the login page with an error message instead of a simple HttpResponse
        return HttpResponse("<h2>Method Not Allowed</h2>", status=405)
    else:
        # Use authenticate from Django's auth system, potentially with your custom backend
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))

        if user is not None:
            # User is authenticated, log them in
            login(request, user)

            # Redirect based on user type
            if user.user_type == "1": # Admin
                messages.success(request, "Logged in as Admin") # Add a success message
                # Use reverse() to get the correct URL for the admin_home name
                return HttpResponseRedirect(reverse("admin_home")) # CORRECTED

            elif user.user_type == "2": # Staff
                messages.success(request, "Logged in as Staff") # Add a success message
                # Correctly using reverse()
                return HttpResponseRedirect(reverse("staff_home"))

            # Use elif for user_type "3" for clarity
            elif user.user_type == "3": # Student
                 messages.success(request, "Logged in as Student") # Add a success message
                # Correctly using reverse()
                 return HttpResponseRedirect(reverse("student_home"))
            else:
                # Handle unexpected user types
                messages.error(request, "Invalid User Type Assigned. Please contact the administrator.")
                logout(request) # Log out potentially invalid user
                return HttpResponseRedirect(reverse("Logindon")) # Redirect back to login

        else:
            # Authentication failed
            messages.error(request, "Invalid Login Details. Please check your username and password.")
            # Redirect back to the login page (use reverse for robustness)
            # Assuming your root URL '/' is mapped to the Logindon view
            return HttpResponseRedirect(reverse("Logindon"))

def GetUserDetails(request):
    if request.user.is_authenticated: # Check if user is logged in
        # Access user_type directly from the CustomUser instance
        return HttpResponse(f"User : {request.user.email} usertype : {request.user.user_type}") # Use f-string
    else:
        return HttpResponse("Please Login First")

# The StudentHome view seems to be separate from the main student home dashboard
# It might just be a base template rendering view.
# The actual student dashboard logic is likely in StudentViews.student_home
# def StudentHome(request):
#     return render(request, "student_template/base_template.html")


def logout_user(request):
    # Add a message before logging out
    messages.info(request, "You have been logged out.")
    logout(request)
    # Redirect to the login page (assuming Logindon is at '/')
    return HttpResponseRedirect(reverse("Logindon"))


# The showFirebaseJS function is correct for serving the service worker content
def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-app.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-messaging.js"); ' \
         'var firebaseConfig = {' \
         '        apiKey: "AIzaSyBcMOsGMY1ICaPu2XcPrzs2UzvMae1_REg",' \
         '        authDomain: "schoolmanagementsystem-ed016.firebaseapp.com",' \
         '        databaseURL: "https://schoolmanagementsystem-ed016-default-rtdb.firebaseio.com",' \
         '        projectId: "schoolmanagementsystem-ed016",' \
         '        storageBucket: "schoolmanagementsystem-ed016.appspot.com",' \
         '        messagingSenderId: "553673307471",' \
         '        appId: "1:553673307471:web:6522986dde31ccdad3813a",' \
         '        measurementId: "G-EHCB4PWFRK"' \
         '};' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.setBackgroundMessageHandler(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        icon:notification.icon' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'

    return HttpResponse(data, content_type="text/javascript")