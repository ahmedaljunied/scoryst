// TODO: browserify
var StudentNavView = IdempotentView.extend({
  /* How long to display the nav success icon. */
  NAV_SUCCESS_DISPLAY_DURATION: 1000,

  /* Key codes for keyboard shorcuts. */
  UP_ARROW_KEY_CODE: 38,
  DOWN_ARROW_KEY_CODE: 40,

  events: {
    'click .next-student': 'goToNextStudent',
    'click .previous-student': 'goToPreviousStudent',
    'change .hide-student-name': 'toggleStudentName',
  },

  // TODO: comments
  initialize: function(options) {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.isNavigating = false;

    // if the next student button exists, then we can navigate through
    // students; otherwise, navigation should be disabled
    if (this.$('.next-student').length > 0) {
      // attach events from elements outside this view
      this.listenToDOM($(window), 'keydown', this.handleShortcuts);
      this.listenToDOM($('.next-student'), 'click', this.goToNextStudent);
      this.listenToDOM($('.previous-student'), 'click', this.goToPreviousStudent);
      this.enableBackButton();
    } else {
      this.undelegateEvents();
    }

    this.$('.student-nav-header').show();
    // User does not want to see student name
    if (window.localStorage && window.localStorage.hideStudentName == 'true') {
      this.$('.hide-student-name').attr('checked', false);
      // In case for some reason, the name is already empty, don't push that as student name
      // into local storage
      self.$('h2').hide();
    } else {
      self.$('h2').show();
    }
  },

  showNavSuccess: function() {
    // show success icon and then hide it; note that there is also a success
    // icon outside of el (at the very bottom of the page)
    var $navSuccessIcon = $('.student-nav-success');
    $navSuccessIcon.show();

    clearTimeout(this.successTimeout);
    this.successTimeout = setTimeout(function() {
      $navSuccessIcon.hide();
    }, this.NAV_SUCCESS_DISPLAY_DURATION);
  },

  /* Makes the back button work by handling the popState event. */
  enableBackButton: function() {
    var self = this;

    this.listenToDOM($(window), 'popstate', function(event) {
      // URL has already been updated by popstate;
      // update student name and trigger AJAX requests for the new student
      this.$('h2').text(event.originalEvent.state.studentName);
      Mediator.trigger('changeStudent');
    });
  },

  toggleStudentName: function(event) {
    var showName = this.$('.hide-student-name').is(':checked');
    // User wants to show the name
    if (window.localStorage == undefined) {
      alert('You must be on a browser that supports local storage to show/hide student names');
      return;
    }
    if (showName) {
      this.$('h2').show();
    } else {
      this.$('h2').hide();
    }
    window.localStorage.hideStudentName = !showName;
  },

  /* Goes to the next student if goToNext is true. Otherwise, goes to the
   * previous student. */
  goToStudent: function(goToNext) {
    if (this.isNavigating) {
      // in progress navigating to previous/next student; don't do anything
      return;
    }

    var self = this;
    this.isNavigating = true;

    var skipGraded = self.$('.skip-graded').is(':checked');
    var url = '?skipGraded=' + skipGraded;
    var activeQuestionNumber = $.cookie('activeQuestionNumber') || 0;
    var activePartNumber = $.cookie('activePartNumber') || 0;
    url = url + '&questionNumber=' + activeQuestionNumber + '&partNumber=' + activePartNumber;

    if (goToNext) {
      url = 'get-next-student/' + url;
    } else {
      url = 'get-previous-student/' + url;
    }

    $.ajax({
      type: 'GET',
      url: url,

      dataType: 'json',
      success: function(data) {
        var studentPath = data.studentPath;
        var studentName = data.studentName;

        if (studentPath !== window.location.pathname) {
          // update URL with history API; fall back to standard redirect
          if (window.history) {
            window.history.pushState({ studentName: studentName }, null, studentPath);

            // update student name and trigger AJAX requests for the new student
            self.$('h2').text(studentName);
            if (window.localStorage && window.localStorage.hideStudentName == 'true') {
              self.$('h2').hide();
            } else {
              self.$('h2').show();
            }
            Mediator.trigger('changeStudent');
          } else {
            window.location.pathname = studentPath;
          }

          self.showNavSuccess();
        }

        self.isNavigating = false;
      },

      error: function() {
        // TODO: handle error
        self.isNavigating = false;
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
      case this.UP_ARROW_KEY_CODE:
        if (event.shiftKey) {
          event.preventDefault();
          this.goToPreviousStudent();
        }
        break;

      case this.DOWN_ARROW_KEY_CODE:
        if (event.shiftKey) {
          event.preventDefault();
          this.goToNextStudent();
        }
        break;
    }
  }
});
