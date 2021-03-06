from django import shortcuts, http
from scorystapp import models, decorators
from scorystapp.views import helpers, grade, grade_or_view
import json


@decorators.access_controlled
@decorators.instructor_or_ta_required
def map(request, cur_course_user, exam_id, exam_answer_id=None):
  """ Renders the map exams page """

  # If no exam_answer_id is given, show the first exam_answer
  if exam_answer_id is None:
    exam_answers = models.Submission.objects.filter(exam_id=exam_id, preview=False)
    # TODO: How should I handle it best if length is 0?
    if not exam_answers.count() == 0:
      exam_answer_id = exam_answers[0].id
      return shortcuts.redirect('/course/%s/exams/%s/map-question-parts/%s/' %
        (cur_course_user.course.id, exam_id, exam_answer_id))

  return helpers.render(request, 'map-question-parts.epy', {'title': 'Map Exams'})


@decorators.access_controlled
@decorators.instructor_or_ta_required
def get_all_exam_answers(request, cur_course_user, exam_id):
  """
  Returns a json representation of a list where each element has the
  exam_id, name, email, student_id of the student (if any student is mapped)
  along with 'tokens' which is needed by typeahead.js
  """
  exam = shortcuts.get_object_or_404(models.Exam, pk=exam_id)

  exam_answers = models.Submission.objects.filter(exam=exam, preview=False)

  students = []
  for exam_answer in exam_answers:
    course_user = exam_answer.course_user
    student = {
      'exam_answer_id': exam_answer.pk,
      'name': course_user.user.get_full_name() if course_user else 'unmapped',
      'email': course_user.user.email if course_user else 'unmapped',
      'student_id': course_user.user.student_id if course_user else None,
      'tokens': [course_user.user.first_name, course_user.user.last_name] if course_user else ['unmapped']
    }
    students.append(student)

  return http.HttpResponse(json.dumps(students), mimetype='application/json')


@decorators.access_controlled
@decorators.instructor_or_ta_required
def get_all_question_parts(request, cur_course_user, exam_id, exam_answer_id):
  """
  Returns a list where index i corresponds to the number of parts question (i + 1) has
  eg. [1, 3, 2] means question 1 has 1 part, question 2 has 3 parts and question 3 has 2 parts.
  """
  exam = shortcuts.get_object_or_404(models.Exam, pk=exam_id)
  question_parts = models.QuestionPart.objects.filter(exam=exam).order_by(
    'question_number', 'part_number')
  num_questions = question_parts.reverse()[0].question_number if question_parts else 0
  questions = []

  for i in range(num_questions):
    num_parts = models.QuestionPart.objects.filter(exam=exam, question_number=i+1).count()
    questions.append(num_parts)

  return http.HttpResponse(json.dumps({'questions': questions}), mimetype='application/json')


@decorators.access_controlled
@decorators.instructor_or_ta_required
def get_all_pages_on_question_part(request, cur_course_user, exam_id, exam_answer_id,
    question_number, part_number):
  """
  Returns the pages that are associated to the given response for the current
  student.
  """
  exam_answer = shortcuts.get_object_or_404(models.Submission, pk=exam_answer_id)
  response = shortcuts.get_object_or_404(models.Response,
    exam_answer=exam_answer, question_part__question_number=question_number,
    question_part__part_number=part_number)
  return http.HttpResponse(response.pages, mimetype='text/html')


@decorators.access_controlled
@decorators.instructor_or_ta_required
def update_pages_on_question_part(request, cur_course_user, exam_id, exam_answer_id,
    question_number, part_number, pages):
  """
  Validates that the pages are correctly formatted and within the correct range
  and then updates the response
  """
  exam_answer = shortcuts.get_object_or_404(models.Submission, pk=exam_answer_id)
  response = shortcuts.get_object_or_404(models.Response,
    exam_answer=exam_answer, question_part__question_number=question_number,
    question_part__part_number=part_number)
  if _validate_pages(exam_answer, pages):
    response.pages = pages
    response.save()
    return http.HttpResponse(status=200)
  # We validate on the front-end so we just return an error code here.
  return http.HttpResponse(status=400)


def _validate_pages(exam_answer, pages):
  """
  Checks to see:
  1. We have a comma-separated list of digits
  2. All digits are between 1 and exam_answer.page_count inclusive
  """
  pages = pages.split(',')
  for page in pages:
    if not page.isdigit():
      return False

    page = int(page)
    if page > exam_answer.page_count or page < 1:
      return False
  return True
