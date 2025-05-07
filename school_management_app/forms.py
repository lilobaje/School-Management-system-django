from django import forms
from django.forms import ChoiceField # Keep ChoiceField if needed for dynamic choices
from school_management_app.models import Courses, SessionYearModel, Subjects, Staffs, Students # Import necessary models

# Keep ChoiceNoValidation if you intend to dynamically populate a select field via JS
class ChoiceNoValidation(ChoiceField):
    def validate(self, value):
        pass

class DateInput(forms.DateInput):
    input_type = "date"

class AddStudentForm(forms.Form):
    # Move choice population to __init__
    def __init__(self, *args, **kwargs):
        super(AddStudentForm, self).__init__(*args, **kwargs)
        # Populate choices dynamically here
        self.fields['course'].choices = self.get_course_choices()
        self.fields['session_year'].choices = self.get_session_year_choices()

    # Helper method to get course choices
    def get_course_choices(self):
        course_list = []
        try:
            courses = Courses.objects.all()
            for course in courses:
                small_course = (course.id, course.course_name)
                course_list.append(small_course)
        except Exception: # Use a general exception or more specific ones if needed
            course_list = [] # Ensure it's always a list
        return course_list

    # Helper method to get session year choices
    def get_session_year_choices(self):
        session_list = []
        try:
            sessions = SessionYearModel.objects.all()
            for ses in sessions:
                # Use f-string for cleaner formatting
                small_ses = (ses.id, f"{ses.session_start_year.year} TO {ses.session_end_year.year}")
                session_list.append(small_ses)
        except Exception: # Use a general exception or more specific ones if needed
            session_list = [] # Ensure it's always a list
        return session_list

    # Fields for CustomUser attributes (first_name, last_name, username, email, password)
    email = forms.EmailField(label="Email", max_length=254, widget=forms.EmailInput(attrs={"class":"form-control","autocomplete":"off"})) # Use 254 max_length for email
    password = forms.CharField(label="Password", max_length=128, widget=forms.PasswordInput(attrs={"class":"form-control"})) # Use 128 max_length for password hash
    first_name = forms.CharField(label="First Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"})) # Use 150 max_length for name
    last_name = forms.CharField(label="Last Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"})) # Use 150 max_length for name
    username = forms.CharField(label="Username", max_length=150, widget=forms.TextInput(attrs={"class":"form-control","autocomplete":"off"})) # Use 150 max_length for username

    # Fields for Students model attributes (address, gender, age, profile_pic, course, session_year)
    address = forms.CharField(label="Address", max_length=255, widget=forms.TextInput(attrs={"class":"form-control"})) # Increased max_length for address
    gender_choice = (
        ("Male", "Male"),
        ("Female", "Female")
        # Consider adding "Other" or leaving flexibility
    )
    sex = forms.ChoiceField(label="Sex", choices=gender_choice, widget=forms.Select(attrs={"class":"form-control"}))

    # Changed age to IntegerField to match model
    age = forms.IntegerField(label="Age", widget=forms.NumberInput(attrs={"class": "form-control"}), required=False) # Use NumberInput, age can be optional

    # Use ChoiceField for course and session_year, choices populated in __init__
    course = forms.ChoiceField(label="Course", widget=forms.Select(attrs={"class":"form-control"}))
    # Renamed field to match model: session_year instead of session_year_id
    session_year = forms.ChoiceField(label="Session Year", widget=forms.Select(attrs={"class":"form-control"}))

    # Profile pic is a FileField
    profile_pic = forms.FileField(label="Profile Pic", widget=forms.FileInput(attrs={"class":"form-control"}), required=False) # Made not required


class EditStudentForm(forms.Form):
     # Move choice population to __init__
    def __init__(self, *args, **kwargs):
        super(EditStudentForm, self).__init__(*args, **kwargs)
        # Populate choices dynamically here
        self.fields['course'].choices = self.get_course_choices()
        self.fields['session_year'].choices = self.get_session_year_choices()
        # Ensure current values are selected in the template based on initial data

    # Helper method to get course choices (can reuse from AddStudentForm if needed)
    def get_course_choices(self):
        course_list = []
        try:
            courses = Courses.objects.all()
            for course in courses:
                small_course = (course.id, course.course_name)
                course_list.append(small_course)
        except Exception:
            course_list = []
        return course_list

    # Helper method to get session year choices (can reuse from AddStudentForm if needed)
    def get_session_year_choices(self):
        session_list = []
        try:
            sessions = SessionYearModel.objects.all()
            for ses in sessions:
                 # Use f-string for cleaner formatting
                small_ses = (ses.id, f"{ses.session_start_year.year} TO {ses.session_end_year.year}")
                session_list.append(small_ses)
        except Exception:
            session_list = []
        return session_list

    # Fields for CustomUser attributes (email, first_name, last_name, username)
    email = forms.EmailField(label="Email", max_length=254, widget=forms.EmailInput(attrs={"class":"form-control"}))
    first_name = forms.CharField(label="First Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name = forms.CharField(label="Last Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))
    username = forms.CharField(label="Username", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))

    # Fields for Students model attributes (address, gender, age, profile_pic, course, session_year)
    address = forms.CharField(label="Address", max_length=255, widget=forms.TextInput(attrs={"class":"form-control"}))
    gender_choice = (
        ("Male", "Male"),
        ("Female", "Female")
    )
    sex = forms.ChoiceField(label="Sex", choices=gender_choice, widget=forms.Select(attrs={"class":"form-control"}))

     # Changed age to IntegerField to match model
    age = forms.IntegerField(label="Age", widget=forms.NumberInput(attrs={"class": "form-control"}), required=False) # Use NumberInput, age can be optional


    # Use ChoiceField for course and session_year, choices populated in __init__
    course = forms.ChoiceField(label="Course", widget=forms.Select(attrs={"class":"form-control"}))
    # Renamed field to match model: session_year instead of session_year_id
    session_year = forms.ChoiceField(label="Session Year", widget=forms.Select(attrs={"class":"form-control"}))

    # Profile pic is a FileField, required=False for editing
    profile_pic = forms.FileField(label="Profile Pic", widget=forms.FileInput(attrs={"class":"form-control"}), required=False)


class EditResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.staff_id = kwargs.pop("staff_id", None) # Use .pop with default None
        super(EditResultForm, self).__init__(*args, **kwargs)

        # Populate Subject choices based on staff_id
        subject_list = []
        if self.staff_id is not None: # Only try filtering if staff_id is provided
            try:
                # Filter subjects taught by this staff using the new field name 'staff'
                subjects = Subjects.objects.filter(staff__user__id=self.staff_id) # Link Subjects to Staffs via CustomUser ID
                for subject in subjects:
                    subject_single = (subject.id, subject.subject_name)
                    subject_list.append(subject_single)
            except Exception:
                subject_list = []
        self.fields['subject'].choices = subject_list # Use new field name 'subject'


        # Populate Session Year choices
        session_list = []
        try:
            sessions = SessionYearModel.objects.all()
            for session in sessions:
                 # Use f-string for cleaner formatting
                session_single = (session.id, f"{session.session_start_year.year} TO {session.session_end_year.year}")
                session_list.append(session_single)
        except Exception:
            session_list = []
        self.fields['session_year'].choices = session_list # Use new field name 'session_year'


    # Renamed field to match model: subject instead of subject_id
    subject = forms.ChoiceField(label="Subject", widget=forms.Select(attrs={"class":"form-control"}))
    # Renamed field to match model: session_year instead of session_ids
    session_year = forms.ChoiceField(label="Session Year", widget=forms.Select(attrs={"class":"form-control"}))

    # Renamed field to match model: student instead of student_ids
    # Use ChoiceNoValidation if choices are populated dynamically via JS
    student = ChoiceNoValidation(label="Student", widget=forms.Select(attrs={"class":"form-control"}))

    # Changed mark fields to FloatField to match model
    assignment_marks = forms.FloatField(label="Assignment Marks", widget=forms.NumberInput(attrs={"class":"form-control"}), required=False) # Use NumberInput, allow blank
    fca_marks = forms.FloatField(label="1st CA", widget=forms.NumberInput(attrs={"class":"form-control"}), required=False) # Use NumberInput, allow blank
    sca_marks = forms.FloatField(label="2nd CA", widget=forms.NumberInput(attrs={"class":"form-control"}), required=False) # Use NumberInput, allow blank
    exam_marks = forms.FloatField(label="Exam CA", widget=forms.NumberInput(attrs={"class":"form-control"}), required=False) # Use NumberInput, allow blank

    # Changed overall_marks to FloatField to match model, allow blank
    overall_marks = forms.FloatField(label="Overall CA", widget=forms.NumberInput(attrs={"class":"form-control"}), required=False) # Use NumberInput, allow blank

    # Added grade_marks field to match model, allow blank
    grade_marks = forms.CharField(label="Grade", max_length=2, widget=forms.TextInput(attrs={"class":"form-control"}), required=False)


# Example Staff Form (if you need one, based on Admin views)
# class AddStaffForm(forms.Form):
#      # Move choice population to __init__ if needed
#      def __init__(self, *args, **kwargs):
#         super(AddStaffForm, self).__init__(*args, **kwargs)
#         # Populate choices dynamically here if needed

#     # Fields for CustomUser attributes
#     email = forms.EmailField(label="Email", max_length=254, widget=forms.EmailInput(attrs={"class":"form-control","autocomplete":"off"}))
#     password = forms.CharField(label="Password", max_length=128, widget=forms.PasswordInput(attrs={"class":"form-control"}))
#     first_name = forms.CharField(label="First Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))
#     last_name = forms.CharField(label="Last Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))
#     username = forms.CharField(label="Username", max_length=150, widget=forms.TextInput(attrs={"class":"form-control","autocomplete":"off"}))

#     # Fields for Staffs model attributes
#     address = forms.CharField(label="Address", max_length=255, widget=forms.TextInput(attrs={"class":"form-control"}))
#     gender_choice = (
#         ("Male", "Male"),
#         ("Female", "Female")
#     )
#     gender = forms.ChoiceField(label="Gender", choices=gender_choice, widget=forms.Select(attrs={"class":"form-control"}))
#     state = forms.CharField(label="State", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
#     city = forms.CharField(label="City", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))


# class EditStaffForm(forms.Form):
#      # Move choice population to __init__ if needed
#      def __init__(self, *args, **kwargs):
#         super(EditStaffForm, self).__init__(*args, **kwargs)
#         # Populate choices dynamically here if needed

#     # Fields for CustomUser attributes
#     email = forms.EmailField(label="Email", max_length=254, widget=forms.EmailInput(attrs={"class":"form-control"}))
#     first_name = forms.CharField(label="First Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))
#     last_name = forms.CharField(label="Last Name", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))
#     username = forms.CharField(label="Username", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))

#     # Fields for Staffs model attributes
#     address = forms.CharField(label="Address", max_length=255, widget=forms.TextInput(attrs={"class":"form-control"}))
#     gender_choice = (
#         ("Male", "Male"),
#         ("Female", "Female")
#     )
#     gender = forms.ChoiceField(label="Gender", choices=gender_choice, widget=forms.Select(attrs={"class":"form-control"}))
#     state = forms.CharField(label="State", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
#     city = forms.CharField(label="City", max_length=50, widget=forms.TextInput(attrs={"class":"form-control"}))
#     # No password field here usually, password changes are separate