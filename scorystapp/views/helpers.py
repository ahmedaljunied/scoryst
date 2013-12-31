from scorystapp import models
from django import shortcuts
from django.utils import timezone

def render(request, template, data={}):
  """
  Renders the template for the given request, passing in the provided data.
  Adds extra data attributes common to all templates.
  """
  # fetch all courses this user is in
  if request.user.is_authenticated():
    course_users_ta = (models.CourseUser.objects.filter(user=request.user.pk).
      exclude(privilege=models.CourseUser.STUDENT))
    courses_ta = map(lambda course_user_ta: course_user_ta.course, course_users_ta)

    course_users_student = models.CourseUser.objects.filter(user=request.user.pk, 
      privilege=models.CourseUser.STUDENT)
    courses_student = map(lambda course_user_student: course_user_student.course, course_users_student)

    user = shortcuts.get_object_or_404(models.User, id=request.user.pk)
    name = user.first_name
  else:
    courses_ta = []
    courses_student = []
    name = ''

  # is_instructor is true if the user is an instuctor for at least one course,
  # false otherwise. Uses the count method for efficiency.
  num_course_users = models.CourseUser.objects.filter(user=request.user.id,
    privilege=models.CourseUser.INSTRUCTOR).count()
  is_instructor = True if num_course_users > 0 else False

  extra_data = {
    'courses_ta': courses_ta,
    'courses_student': courses_student,
    'path': request.path,
    'user': request.user,
    'name': name,
    'is_authenticated': request.user.is_authenticated(),
    'year': timezone.now().year,
    'is_instructor': is_instructor
  }
  extra_data.update(data)

  return shortcuts.render(request, template, extra_data)
