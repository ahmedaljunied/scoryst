from django.utils import timezone
import pytz
from rest_framework import serializers
from scorystapp import models


class AssessmentSerializer(serializers.ModelSerializer):
  is_exam = serializers.SerializerMethodField('get_is_exam')
  solutions_pdf = serializers.SerializerMethodField('get_solutions_pdf')
  is_fully_editable = serializers.SerializerMethodField('get_is_fully_editable')

  # Only valid if the assessment is an exam (else None)
  page_count = serializers.SerializerMethodField('get_page_count')
  exam_pdf = serializers.SerializerMethodField('get_exam_pdf')

  # Only valid if the assessment is a homework (else None)
  soft_deadline = serializers.SerializerMethodField('get_soft_deadline')
  hard_deadline = serializers.SerializerMethodField('get_hard_deadline')
  groups_allowed = serializers.SerializerMethodField('get_groups_allowed')
  max_group_size = serializers.SerializerMethodField('get_max_group_size')

  def get_is_exam(self, assessment):
    return hasattr(assessment, 'exam')

  def get_page_count(self, assessment):
    if self.get_is_exam(assessment):
      return assessment.exam.page_count
    return None

  def get_solutions_pdf(self, assessment):
    """
    Returns URL for solutions PDF. Since there is a delay in uploading the file,
    it is possible that the url has not yet been set. Catch the error.
    """
    try:
      return assessment.solutions_pdf.url if assessment.solutions_pdf else None
    except ValueError:
      return None

  def get_exam_pdf(self, assessment):
    """
    Returns URL for exam PDF. Since there is a delay in uploading the file, it
    is possible that the url has not yet been set. Catch the error.
    """
    if self.get_is_exam(assessment):
      try:
        return assessment.exam.exam_pdf.url
      except ValueError:
        return None
    return None

  def get_soft_deadline(self, assessment):
    """ Submission deadline is a string returning the time in local time. """
    if hasattr(assessment, 'homework'):
      cur_timezone = pytz.timezone(assessment.course.get_timezone_string())
      local_time = timezone.localtime(assessment.homework.soft_deadline, timezone=cur_timezone)
      return local_time.strftime('%m/%d/%Y %I:%M %p')
    return None

  def get_hard_deadline(self, assessment):
    """ Submission deadline is a string returning the time in local time. """
    if hasattr(assessment, 'homework'):
      cur_timezone = pytz.timezone(assessment.course.get_timezone_string())
      local_time = timezone.localtime(assessment.homework.hard_deadline, timezone=cur_timezone)
      return local_time.strftime('%m/%d/%Y %I:%M %p')
    return None

  def get_groups_allowed(self, assessment):
    if hasattr(assessment, 'homework'):
      return assessment.homework.groups_allowed
    return None

  def get_max_group_size(self, assessment):
    if hasattr(assessment, 'homework'):
      return assessment.homework.max_group_size
    return None

  def get_is_fully_editable(self, assessment):
    """ Editing all fields of an assessment is only possible if there are no submissions. """
    return models.Submission.objects.filter(assessment=assessment).count() == 0

  class Meta:
    model = models.Assessment
    fields = ('id', 'name', 'course', 'is_exam', 'page_count', 'solutions_pdf',
              'soft_deadline', 'hard_deadline', 'exam_pdf', 'is_fully_editable',
              'grade_down', 'groups_allowed', 'max_group_size')
    read_only_fields = ('id', 'name', 'course', 'grade_down')


class QuestionPartSerializer(serializers.ModelSerializer):
  def validate_assessment(self, attrs, source):
    """ Validates that the QuestionPart matches the one currently being viewed. """
    assessment = attrs.get(source)

    if not assessment == self.context['assessment']:
      raise serializers.ValidationError('Rubric for invalid assessment: %d' % assessment.pk)
    return attrs

  class Meta:
    model = models.QuestionPart
    fields = ('id', 'assessment', 'question_number', 'part_number', 'max_points', 'pages')
    read_only_fields = ('id', 'assessment', 'question_number', 'part_number',
                        'max_points', 'pages')
