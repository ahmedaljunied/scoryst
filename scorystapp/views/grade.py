from django import shortcuts, http
from scorystapp import models, forms, decorators, serializers
from scorystapp.views import helpers
from rest_framework import decorators as rest_decorators, response


@decorators.access_controlled
@decorators.instructor_or_ta_required
def grade(request, cur_course_user, submission_id):
  """ Allows an instructor/TA to grade an assessment. """
  submission = shortcuts.get_object_or_404(models.Submission, pk=submission_id)

  return helpers.render(request, 'grade.epy', {
    'title': 'Grade',
    'course_user': cur_course_user,
    'course': cur_course_user.course.name,
    'student_name': submission.course_user.user.get_full_name(),
    # TODO: The solutions PDF needs to be added to the assessment model
    # till then, I'm just returning False
    'solutions_exist': False, # bool(submission.assessment.solutions_pdf.name),
    'is_grade_page': True
  })


@rest_decorators.api_view(['GET'])
@decorators.access_controlled
@decorators.instructor_or_ta_required
def get_previous_student(request, cur_course_user, submission_id):
  """
  Given a particular student's assessment, returns the grade page for the previous
  student, ordered alphabetically by last name, then first name, then email.
  If there is no previous student, the same student is returned.
  """
  cur_submission = shortcuts.get_object_or_404(models.Submission, pk=submission_id)
  previous_submission = get_offset_student_assessment(submission_id, -1)

  return response.Response({
    'student_path': '/course/%d/grade/%d/' % (cur_course_user.course.pk,
      previous_submission.pk),
    'student_name': previous_submission.course_user.user.get_full_name(),
  })


@rest_decorators.api_view(['GET'])
@decorators.access_controlled
@decorators.instructor_or_ta_required
def get_next_student(request, cur_course_user, submission_id):
  """
  Given a particular student's assessment, returns the grade page for the next
  student, ordered alphabetically by last name, then first name, then email.
  If there is no next student, the same student is returned.
  """
  cur_submission = shortcuts.get_object_or_404(models.Submission, pk=submission_id)
  next_submission = get_offset_student_assessment(submission_id, 1)

  return response.Response({
    'student_path': '/course/%d/grade/%d/' % (cur_course_user.course.pk,
      next_submission.pk),
    'student_name': next_submission.course_user.user.get_full_name(),
  })


def get_offset_student_assessment(submission_id, offset):
  """
  Gets the assessment for the student present at 'offset' from the current student.
  If there is no student at that offset, the student at one of the bounds (0 or last index)
  is returned.
  """
  offset = int(offset)
  submission_id = int(submission_id)

  # Get the assessment of the current student
  cur_submission = shortcuts.get_object_or_404(models.Submission, pk=submission_id)

  # Fetch all submissions
  submissions = models.Submission.objects.filter(assessment=cur_submission.assessment,
    preview=False, course_user__isnull=False).order_by('course_user__user__first_name',
    'course_user__user__last_name', 'course_user__user__email')

  # Calculate the index of the current submission
  for cur_index, submission in enumerate(submissions.all()):
    if submission_id == submission.id:
      break

  total = submissions.count()

  # Fetch the index at offset from current, if possible, else return a bound
  if cur_index + offset >= 0 and cur_index + offset < total:
    next_index = cur_index + offset
  elif cur_index + offset < 0:
    next_index = 0
  else:
    next_index = total - 1

  # Get the submission correspodning to the index
  next_submission = submissions[next_index]
  return next_submission
