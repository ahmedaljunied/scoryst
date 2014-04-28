// TODO: browserify
var StudentNavView = IdempotentView.extend({
  /* How long to display the nav success icon. */
  NAV_SUCCESS_DISPLAY_DURATION: 1000,

  /* Key codes for keyboard shorcuts. */
  UP_ARROW_KEY_CODE: 38,
  DOWN_ARROW_KEY_CODE: 40,

  events: {
    'click .next-student': 'goToNextStudent',
    'click .previous-student': 'goToPreviousStudent'
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

  /* Goes to the next student if goToNext is true. Otherwise, goes to the
   * previous student. */
  goToStudent: function(goToNext) {
    if (this.isNavigating) {
      // in progress navigating to previous/next student; don't do anything
      return;
    }

    var self = this;
    this.isNavigating = true;

    $.ajax({
      type: 'GET',
      url: goToNext ? 'get-next-student/' : 'get-previous-student/',

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
