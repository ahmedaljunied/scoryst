from scorystapp import models
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, forms as django_forms
from django.contrib.admin import widgets
from django.utils import html, timezone
import PyPDF2
from PyPDF2 import utils as pdf_utils
import pytz


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
  """
  Overrides the renderer method so that radio buttons are rendered horizontal as
  opposed to as a vertical list, making it compatible with Bootstrap styling.
  """
  def render(self):
    # Add inline-radio class to input fields
    modified_radio_buttons = []
    for radio_button in self:
      radio_button_str = str(radio_button)
      modified_radio_button = '%s class="radio-inline" %s' % (radio_button_str[:6],
        radio_button_str[6:])
      modified_radio_buttons.append(modified_radio_button)
    full_html = u'\n'.join([u'%s\n' % radio_button for radio_button in modified_radio_buttons])
    return html.mark_safe(full_html)


class UserSignupForm(forms.Form):
  """ Allow a student to sign up. """
  first_name = forms.CharField(label='First Name', max_length=100)
  last_name = forms.CharField(label='Last Name', max_length=100)
  email = forms.EmailField(label='School Email', max_length=100)
  student_id = forms.CharField(label='Student ID', max_length=100)

  def clean_email(self):
    """ Converts email address to lowercase and makes sure it is unique. """
    email = self.cleaned_data['email'].lower()

    if models.User.objects.filter(email=email).count() > 0:
      raise forms.ValidationError('A user with that email already exists.')

    return email


class UserLoginForm(forms.Form):
  """ Allows the user to log in. """
  email = forms.EmailField(max_length=100)
  password = forms.CharField(max_length=100, widget=forms.PasswordInput)

  def clean_email(self):
    """ Converts email to lowercase. """
    return self.cleaned_data['email'].lower()

  def clean(self):
    """ Confirms the user provided valid credentials. """
    data = self.cleaned_data
    email = data.get('email')
    password = data.get('password')

    user = authenticate(username=email, password=password)
    if email and password:
      if user is None:
        raise forms.ValidationError('Invalid credentials.')
      elif not user.is_active:
        raise forms.ValidationError('User is not active.')
      elif not user.is_signed_up:
        user.is_signed_up = True
        user.save()
    return data


class TokenForm(forms.Form):
  """ Allows the user to enroll in a class using the token """
  token = forms.CharField(max_length=10)

  def clean_token(self):
    """ Ensures the token is valid """
    token = self.cleaned_data.get('token')
    valid = False

    try:
      course = models.Course.objects.get(student_enroll_token=token)
    except models.Course.DoesNotExist:
      pass
    else:
      valid = True

    try:
      course = models.Course.objects.get(ta_enroll_token=token)
    except models.Course.DoesNotExist:
      pass
    else:
      valid = True

    if not valid:
      raise forms.ValidationError('Please enter a valid token')

    return token


class AddPeopleForm(forms.Form):
  """ Allows the user to add students/TAs to a class. """
  people = forms.CharField(max_length=40000, widget=forms.Textarea)
  privilege = forms.ChoiceField(choices=models.CourseUser.USER_PRIVILEGE_CHOICES,
    widget=forms.RadioSelect)

  def clean_people(self):
    """
    Ensures people field is a valid listing of people. Each person should have
    a first name, last name, email, and student ID.
    """
    people = self.cleaned_data.get('people')
    cleaned_people = []

    if not people:
      return people

    for person in people.splitlines():
      parts = person.split(',')

      # ensure we have all parts
      if not len(parts) == 4:
        raise forms.ValidationError('You must provide a first name, last name, '
          'email, and ID for each student')

      parts = map(lambda part: part.strip(), parts)
      first_name, last_name, email, student_id = parts

      # ensure email is valid
      field = forms.EmailField(max_length=100, error_messages={
        'invalid': '%s is not a valid email address' % email})
      email = field.clean(email)

      # ensure first name, last name, and student ID are provided
      field = forms.CharField(max_length=100)
      first_name = field.clean(first_name)
      last_name = field.clean(last_name)
      student_id = field.clean(student_id)

      # reconstruct cleaned string
      cleaned_people.append(','.join((first_name, last_name, email, student_id)))

    return '\n'.join(cleaned_people)


class AssessmentUploadForm(forms.Form):
  """ Allows an exam to be uploaded along with the empty and solutions pdf file """
  MAX_ALLOWABLE_PDF_SIZE = 1024 * 1024 * 20

  HOMEWORK_TYPE = 'homework'
  EXAM_TYPE = 'exam'
  ASSESSMENT_TYPES = (
      (HOMEWORK_TYPE, 'Homework'),
      (EXAM_TYPE, 'Exam'),
  )

  GRADE_DOWN_TYPE = 'down'
  GRADE_UP_TYPE = 'up'
  GRADE_TYPES = (
      (GRADE_DOWN_TYPE, 'Grade down'),
      (GRADE_UP_TYPE, 'Grade up'),
  )

  NO_GROUPS_ALLOWED = 'no_groups_allowed'
  GROUPS_ALLOWED = 'groups_allowed'
  GROUP_TYPES = (
      (NO_GROUPS_ALLOWED, 'Individual submissions only'),
      (GROUPS_ALLOWED, 'Group submissions OK')
  )

  assessment_type = forms.ChoiceField(choices=ASSESSMENT_TYPES,
    widget=forms.RadioSelect(renderer=HorizontalRadioRenderer), initial=HOMEWORK_TYPE)
  name = forms.CharField(max_length=40)

  # For the following fields that have `required=False` but are required in
  # certain cases (explained more below), validation is done either in the
  # `clean` functions below or in the view
  # `grade_type` is not required if the assessment is not fully editable
  grade_type = forms.ChoiceField(choices=GRADE_TYPES, required=False,
    widget=forms.RadioSelect(renderer=HorizontalRadioRenderer), initial=GRADE_DOWN_TYPE)

  # The `exam_file` is not required if the assessment is being edited
  exam_file = forms.FileField(required=False)
  # The  `solutions_file` is never required
  solutions_file = forms.FileField(required=False)
  # `soft_deadline`, `hard_deadline` and `groups_allowed` are required only if
  # the assessment is a homework
  soft_deadline = forms.DateTimeField(required=False, input_formats=['%m/%d/%Y %I:%M %p', '%m/%d/%y %I:%M %p'])
  hard_deadline = forms.DateTimeField(required=False, input_formats=['%m/%d/%Y %I:%M %p', '%m/%d/%y %I:%M %p'])
  groups_allowed = forms.ChoiceField(choices=GROUP_TYPES, widget=forms.RadioSelect(
    renderer=HorizontalRadioRenderer), initial=NO_GROUPS_ALLOWED)
  max_group_size = forms.IntegerField(required=False, min_value=2)

  # The question part information is passed as stringified JSON
  question_part_points = forms.CharField()


  def __init__(self, *args, **kwargs):
    """ Get the string that corresponds to the course's timezone. """
    self.timezone_string = kwargs.pop('timezone_string', None)
    super(AssessmentUploadForm, self).__init__(*args, **kwargs)


  def clean(self):
    def change_timezone(datetime):
      """
      Given a datetime that believes it's in the `settings.TIME_ZONE` time zone
      (which is the default timezone for `forms.DateTimeField`s), change it to
      the course's timezone.
      """
      if datetime:
        cur_timezone = pytz.timezone(self.timezone_string)
        # Remove the timezone associated with the time (without changing the time)
        datetime = timezone.make_naive(datetime, timezone=pytz.timezone(settings.TIME_ZONE))
        # Add the correct timezone to the time (without changing the time)
        datetime = timezone.make_aware(datetime, timezone=cur_timezone)
        return datetime
      else:
        return None

    assessment_type = self.cleaned_data.get('assessment_type')
    soft_deadline = change_timezone(self.cleaned_data.get('soft_deadline'))
    hard_deadline = change_timezone(self.cleaned_data.get('hard_deadline'))
    groups_allowed = self.cleaned_data.get('groups_allowed')
    max_group_size = self.cleaned_data.get('max_group_size')

    if assessment_type == self.HOMEWORK_TYPE and not soft_deadline:
      # homework submission time required; add error to respective field
      self._errors['soft_deadline'] = self.error_class(['Must provide valid submission soft deadline.'])
      # This field is not valid, so remove from the cleaned_data
      if 'soft_deadline' in self.cleaned_data:
        del self.cleaned_data['soft_deadline']

    if assessment_type == self.HOMEWORK_TYPE and not hard_deadline:
      # homework submission time required; add error to respective field
      self._errors['hard_deadline'] = self.error_class(['Must provide valid submission hard deadline.'])
      # This field is not valid, so remove from the cleaned_data
      if 'hard_deadline' in self.cleaned_data:
        del self.cleaned_data['hard_deadline']

    if soft_deadline and hard_deadline:
      if soft_deadline > hard_deadline:
        self._errors['hard_deadline'] = self.error_class(['Hard deadline can\'t be before soft deadline'])
        del self.cleaned_data['hard_deadline']
      else:
        self.cleaned_data['soft_deadline'] = soft_deadline
        self.cleaned_data['hard_deadline'] = hard_deadline

    if assessment_type == self.HOMEWORK_TYPE and groups_allowed is None:
      # `groups_allowed` is required; add error to respective field
      self._errors['groups_allowed'] = self.error_class(['The groups allowed field is required for homework.'])
      # This field is not valid, so remove from the cleaned_data
      if 'groups_allowed' in self.cleaned_data:
        del self.cleaned_data['groups_allowed']

    if assessment_type == self.HOMEWORK_TYPE and groups_allowed and max_group_size is None:
      # `max_group_size` is required if groups are allowed; add error to respective field
      self._errors['max_group_size'] = self.error_class(['Need max number for group if groups allowed'])
      # This field is not valid, so remove from the cleaned_data
      if 'max_group_size' in self.cleaned_data:
        del self.cleaned_data['max_group_size']

    return self.cleaned_data


  def clean_exam_file(self):
    """
    Ensure that the exam_file is less than MAX_ALLOWABLE_PDF_SIZE and is a valid pdf.
    """
    exam_file = self.cleaned_data.get('exam_file')
    if exam_file:
      _validate_pdf_file(exam_file, AssessmentUploadForm.MAX_ALLOWABLE_PDF_SIZE)
    return exam_file


  def clean_solutions_file(self):
    """
    Ensure that the solutions_file is less than MAX_ALLOWABLE_PDF_SIZE and
    is a valid pdf
    """
    solutions_file = self.cleaned_data['solutions_file']
    if solutions_file:
      _validate_pdf_file(solutions_file, AssessmentUploadForm.MAX_ALLOWABLE_PDF_SIZE)
    return solutions_file

  def clean_groups_allowed(self):
    """
    Change the `groups_allowed` field to be True if groups are allowed and
    False otherwise.
    """
    return self.cleaned_data['groups_allowed'] == 'groups_allowed'


class ExamsUploadForm(forms.Form):
  """ Allows exams to be uploaded. """
  # 100MB max PDF size, as multiple exams can be uploaded
  MAX_ALLOWABLE_PDF_SIZE = 1024 * 1024 * 100

  SINGLE_SIDED_TYPE = 'single'
  DOUBLE_SIDED_TYPE = 'double'
  EXAM_UPLOAD_TYPES = (
      (SINGLE_SIDED_TYPE, 'Questions are on every page'),
      (DOUBLE_SIDED_TYPE, 'Questions are on every other page'),
  )

  exam_id = forms.ChoiceField()
  exam_file = forms.FileField()
  single_or_double = forms.ChoiceField(choices=EXAM_UPLOAD_TYPES,
    widget=forms.RadioSelect(renderer=HorizontalRadioRenderer), initial=DOUBLE_SIDED_TYPE)


  def __init__(self, exam_choices, *args, **kwargs):
    """ Sets up the `exam_id` choice field to hold the given choices. """
    super(ExamsUploadForm, self).__init__(*args, **kwargs)
    self.fields['exam_id'].choices = exam_choices


  def clean_exam_file(self):
    """ Ensure exam_file is a pdf of appropriate size. """
    exam_file = self.cleaned_data.get('exam_file')
    if exam_file:
      _validate_pdf_file(exam_file, ExamsUploadForm.MAX_ALLOWABLE_PDF_SIZE)
    return exam_file


class HomeworkUploadForm(forms.Form):
  """ Allows homework to be uploaded. """
  # 40MB max PDF size, as only a single homework can be uploaded
  # Note that this value is also used for client-side validation
  # so any changes here should also be reflected in the front-end.
  MAX_ALLOWABLE_PDF_SIZE = 1024 * 1024 * 40

  homework_id = forms.ChoiceField()
  homework_file = forms.FileField()

  # student to upload as; this is an instructors-only field
  student_id = forms.ChoiceField(required=False)

  group_members = forms.CharField(required=False)

  def __init__(self, is_staff, homework_choices, student_choices, timezone_string,
      cur_course_user, course, *args, **kwargs):
    """ Sets up the `homework_id` choice field to hold the given choices. """
    super(HomeworkUploadForm, self).__init__(*args, **kwargs)
    self.fields['homework_id'].choices = homework_choices

    if is_staff:
      self.fields['student_id'].choices = student_choices
      self.fields['student_id'].required = True

    self.is_staff = is_staff
    self.timezone_string = timezone_string
    self.course = course

    self.cur_course_user = cur_course_user

  def clean_group_members(self):
    emails = self.cleaned_data['group_members']
    emails = emails.replace(' ', '')  # Remove spaces
    emails = emails.split(',')

    group_members = []

    for email in emails:
      if len(email) == 0:
        continue

      course_user = models.CourseUser.objects.filter(user__email=email, course=self.course)

      if course_user.count() != 1:
        raise forms.ValidationError('There is no user with email %s in this course' % email)

      group_members.append(course_user[0])

    return group_members


  def clean(self):
    """
    The clean method does two things. 1) If group submissions are allowed, ensure
    that the group size is at most `max_group_size`. 2) Ensure that it's not past
    the submission deadline.
    """
    data = self.cleaned_data
    homework = models.Homework.objects.get(pk=data['homework_id'])

    # First validation: check group size
    if homework.groups_allowed:
      group_members = data.get('group_members')

      if group_members:  # Does not pass if `group_members` is None or []
        # Find the `CourseUser` ID of the student who submits for the group. Even
        # if a staff member technically submits, `cu_id` corresponds to a student.
        cu_id = data['student_id'] if self.is_staff else self.cur_course_user

        cur_cu_included = len(filter(lambda cu: int(cu.id) == int(cu_id), group_members)) == 1
        max_len = homework.max_group_size - (0 if cur_cu_included else 1)

        if len(group_members) > max_len:
          raise forms.ValidationError('Number of emails exceeds the max group size')

    # Second validation: check submission deadline
    if self.is_staff:
      # staff have no submission deadlines
      return self.cleaned_data

    if timezone.now() > homework.hard_deadline:
      cur_timezone = pytz.timezone(self.timezone_string)
      formatted_deadline = (timezone.localtime(homework.hard_deadline, timezone=cur_timezone)
        .strftime('%a, %b %d, %I:%M %p'))

      raise forms.ValidationError('Cannot submit past the hard deadline of ' +
        formatted_deadline)

    return data


  def clean_homework_file(self):
    """ Ensure homework_file is a pdf of appropriate size. """
    homework_file = self.cleaned_data.get('homework_file')
    if homework_file:
      _validate_pdf_file(homework_file, HomeworkUploadForm.MAX_ALLOWABLE_PDF_SIZE)
    return homework_file


def _validate_pdf_file(pdf_file, max_size):
  """ Validates the pdf_file and ensures it is less than max_size (which is in bytes). """
  BYTES_IN_MB = 1024 * 1024
  if pdf_file.size > max_size:
    max_size_in_mb = max_size / float(BYTES_IN_MB)
    user_size_in_mb = pdf_file.size / float(BYTES_IN_MB)

    error_message = ('Max size allowed is %d MB but file size is %d MB. ' %
      (max_size_in_mb, user_size_in_mb))
    error_message += 'You may try http://smallpdf.com/compress-pdf to compress the pdf size.'
    raise forms.ValidationError(error_message)

  try:
    py_pdf_file = PyPDF2.PdfFileReader(pdf_file)
  except:  # TODO: need explicit error here
    raise forms.ValidationError('The PDF file is invalid and may be corrupted')

  try:
    num_pages = py_pdf_file.getNumPages()
  except pdf_utils.PdfReadError:
    raise forms.ValidationError('Cannot read the PDF file')

  # if for whatever reason the number of pages is non-positive, raise error
  if num_pages <= 0:
    raise forms.ValidationError('The PDF file has an invalid number of pages')

  pdf_file.seek(0)  # undo work of PyPDF2


class CourseForm(forms.ModelForm):
  """ Model Form for creating a new course """
  class Meta:
    model = models.Course
    exclude = ('student_enroll_token', 'ta_enroll_token')


class QuestionPartForm(forms.ModelForm):
  """ Model Form for creating a new question part used by create-exam """
  class Meta:
    model = models.QuestionPart
    exclude = ('assessment',)


class RubricForm(forms.ModelForm):
  """ Model Form for creating a new rubric used by create-exam """
  class Meta:
    model = models.Rubric
    exclude = ('question_part',)


class SetPasswordWithMinLengthForm(django_forms.SetPasswordForm):
  """ Form for resetting password. Ensure that the password length is at least 8. """
  def clean_new_password1(self):
    password1 = self.cleaned_data.get('new_password1')
    return _validate_password_length(password1)


class PasswordWithMinLengthChangeForm(django_forms.PasswordChangeForm):
  """ Form for changing password. Ensure that the password length is at least 8. """
  def clean_new_password1(self):
    password1 = self.cleaned_data.get('new_password1')
    return _validate_password_length(password1)


def _validate_password_length(password):
    if len(password) < 8:
      raise forms.ValidationError('Password must be at least 8 characters.')
    return password

