// TODO: browserify
var ExamPDFView = Backbone.View.extend({
  /* Key codes for keyboard shorcuts. */
  LEFT_ARROW_KEY_CODE: 37,
  RIGHT_ARROW_KEY_CODE: 39,
  UP_ARROW_KEY_CODE: 38,
  DOWN_ARROW_KEY_CODE: 40,

  LEFT_BRACKET_KEY_CODE: 219,
  RIGHT_BRACKET_KEY_CODE: 221,

  events: {
    'click .previous-page': 'goToPreviousPage',
    'click .next-page': 'goToNextPage'
  },

  // TODO: comments
  initialize: function(options) {
    // if there's a next student button on this page, we should preload
    // the next/previous student
    var shouldPreloadStudent = false;
    if (this.$('.next-student').length > 0) {
      shouldPreloadStudent = true;
    }

    this.questionParts = options.questionParts;
    this.imageLoader = new ImageLoader(1, true, shouldPreloadStudent);
    this.history = window.history; // for the history API

    this.setActiveQuestionPart(this.questionParts.at(0), 0);
    this.addRemoteEventListeners();
  },

  addRemoteEventListeners: function() {
    // mediator events
    var self = this;
    Mediator.on('changeQuestionPart', function(questionPart, pageIndex) {
      pageIndex = pageIndex || 0;
      self.setActiveQuestionPart(questionPart, pageIndex);
    });

    // events from other elements
    $(window).keydown(_.bind(this.handleShortcuts, this));
    $('.next-student').click(_.bind(this.goToNextStudent, this));
    $('.previous-student').click(_.bind(this.goToPreviousStudent, this));
  },

  goToPreviousPage: function(skipCurrentPart) {
    // display the previous page in the current part if it exists
    if (this.activePageIndex > 0 && !skipCurrentPart) {
      this.setActiveQuestionPart(this.activeQuestionPart, this.activePageIndex - 1);
      return;
    }

    // otherwise, look for the previous part:
    var curQuestionPart = this.activeQuestionPart;
    var previousQuestionPart;

    if (curQuestionPart.get('part_number') > 1) {
      // find the previous part in the current question
      previousQuestionPart = this.questionParts.filter(function(questionPart) {
        return questionPart.get('question_number') === curQuestionPart.get('question_number') &&
          questionPart.get('part_number') === curQuestionPart.get('part_number') - 1;
      });
      previousQuestionPart = previousQuestionPart[0];
    } else {
      // if there is no previous part, find the last part in the previous question
      previousQuestionPart = this.questionParts.filter(function(questionPart) {
        return questionPart.get('question_number') === curQuestionPart.get('question_number') - 1;
      });

      if (previousQuestionPart.length > 0) {
        // narrow down to last part
        previousQuestionPart = _.max(previousQuestionPart, function(questionPart) {
          return questionPart.get('part_number');
        });
      } else {
        // no previous question
        previousQuestionPart = null;
      }
    }

    if (previousQuestionPart) {
      Mediator.trigger('changeQuestionPart', previousQuestionPart, -1);
    } else {
      // if that didn't work, there is no previous part, so do nothing
    }
  },

  goToNextPage: function(skipCurrentPart) {
    // display the next page in the current part if it exists
    if (this.activePageIndex < this.activeQuestionPartPages.length - 1 && !skipCurrentPart) {
      this.setActiveQuestionPart(this.activeQuestionPart, this.activePageIndex + 1);
      return;
    }

    // otherwise, look for the next part:
    var curQuestionPart = this.activeQuestionPart;

    // find the next part in the current question
    var nextQuestionPart = this.questionParts.filter(function(questionPart) {
      return questionPart.get('question_number') === curQuestionPart.get('question_number') &&
        questionPart.get('part_number') === curQuestionPart.get('part_number') + 1;
    });
    nextQuestionPart = nextQuestionPart[0];

    // if that didn't work, find the next question
    if (!nextQuestionPart) {
      nextQuestionPart = this.questionParts.filter(function(questionPart) {
        return questionPart.get('question_number') === curQuestionPart.get('question_number') + 1 &&
          questionPart.get('part_number') === 1;
      });
      nextQuestionPart = nextQuestionPart[0];
    }

    if (nextQuestionPart) {
      Mediator.trigger('changeQuestionPart', nextQuestionPart, 0);
    } else {
      // if that didn't work, there is no next part, so do nothing
    }
  },

  setActiveQuestionPart: function(questionPart, pageIndex) {
    // set instance variables associated with the active question part
    this.activeQuestionPart = questionPart;
    this.activeQuestionPartPages = questionPart.get('pages').split(',');
    this.activeQuestionPartPages = this.activeQuestionPartPages.map(function(page) {
      return parseInt(page, 10);
    });

    // allow pythonic negative indexes for ease of use
    if (pageIndex < 0) {
      this.activePageIndex = this.activeQuestionPartPages.length + pageIndex;
    } else {
      this.activePageIndex = pageIndex;
    }

    // update displayed page
    var page = this.activeQuestionPartPages[this.activePageIndex];
    this.imageLoader.showPage(page, questionPart.question_number,
      questionPart.part_number);
  },

  /* Goes to the next student if goToNext is true. Otherwise, goes to the
   * previous student. */
  goToStudent: function(goToNext) {
    var self = this;

    $.ajax({
      type: 'GET',
      url: goToNext ? 'get-next-student/' : 'get-previous-student/',

      dataType: 'json',
      success: function(data) {
        var studentPath = data.student_path;
        if (studentPath === window.pathname) {
          // no next/previous student
          return;
        }

        // update URL with history API; fall back to standard redirect
        if (self.history) {
          self.history.pushState(null, null, studentPath);

          // update the part to trigger AJAX requests for the new student
          Mediator.trigger('changeQuestionPart', self.activeQuestionPart, self.activePageIndex);
        } else {
          window.pathname = studentPath;
        }
      },

      error: function() {
        // TODO: handle error
      }
    });
  },

  /* Navigates to the next student. */
  goToNextStudent: function() {
    this.goToStudent(true);
  },

  /* Navigates to the previous student. */
  goToPreviousStudent: function() {
    this.goToStudent(false);
  },

  handleShortcuts: function(event) {
    // ignore keys entered in an input/textarea
    var $target = $(event.target);
    if ($target.is('input') || $target.is('textarea')) {
      return;
    }

    switch (event.keyCode) {
      case this.LEFT_ARROW_KEY_CODE:
        this.goToPreviousPage();
        break;

      case this.RIGHT_ARROW_KEY_CODE:
        this.goToNextPage();
        break;

      case this.UP_ARROW_KEY_CODE:
        this.goToNextStudent();
        break;

      case this.DOWN_ARROW_KEY_CODE:
        this.goToPreviousStudent();
        break;

      case this.LEFT_BRACKET_KEY_CODE:
        this.goToPreviousPage(true);
        break;

      case this.RIGHT_BRACKET_KEY_CODE:
        this.goToNextPage(true);
        break;
    }
  }
});