// TODO: browserify
var RubricView = IdempotentView.extend({
  tagName: 'li',
  template: _.template($('.rubric-template').html()),

  events: {
    'click': 'toggle',
    'click .edit': 'edit',
    'click .save': 'save',
    'blur .rubric-description': 'setBlurred',
    'blur .rubric-points': 'setBlurred'
  },

  /* Initializes this rubric. Requires a Rubric model and the following options:
   * response -- the Response model of the current student
   *  being graded
   */
  initialize: function(options) {
    this.constructor.__super__.initialize.apply(this, arguments);
    this.response = options.response;

    this.editing = false;
    if (options.editingEnabled) {
      this.enableEditing();
    } else {
      this.disableEditing();
    }

    this.listenTo(this.response, 'change:rubrics', this.render);
    this.listenTo(Mediator, 'enableEditing', this.enableEditing);
    this.listenTo(Mediator, 'disableEditing', this.disableEditing);

    this.listenToDOM($(window), 'click', this.checkIfShouldSave);
  },

  /* Renders this rubric in a new li element. */
  render: function() {
    var rubric = this.model.toJSON();
    var gradeDown = this.response.get('questionPart').gradeDown;

    // associate a color (red or green) with each rubric
    if (gradeDown) {
      rubric.color = rubric.points > 0 ? 'red' : 'green';
      // If we are grading down, we want the points to be displayed as negative
      // so if a rubric has 10 points associated, it shows up as -10
      rubric.displayPoints = -rubric.points;
    } else {
      rubric.color = rubric.points < 0 ? 'red' : 'green';
      rubric.displayPoints = rubric.points;
    }

    // track whether this rubric is selected
    var selectedRubrics = this.response.get('rubrics');
    if (_.contains(selectedRubrics, rubric.id)) {
      this.$el.addClass('selected');
    } else {
      this.$el.removeClass('selected');
    }

    rubric.editing = this.editing;
    this.$el.html(this.template(rubric));

    this.$('.destroy').popoverConfirm({
      confirm: _.bind(this.destroy, this)
    });
    return this;
  },

  /* Don't allow user to toggle rubrics when in editing mode. */
  enableEditing: function(event) {
    this.enableToggle = false;
  },

  disableEditing: function(event) {
    this.enableToggle = true;

    if (this.editing) {
      // when the user disables editing, save what that the user was editing
      this.save();
      this.editing = false;
      this.render();
    }
  },

  /* Toggles this rubric on/off. */
  toggle: function() {
    if (!this.enableToggle) {
      return;
    }

    if (Utils.IS_STUDENT_VIEW) {
      return;
    }

    // clone rubrics, since we're going to modify them
    var rubrics = _.clone(this.response.get('rubrics'));
    var rubricId = this.model.get('id');

    if (this.$el.hasClass('selected')) {
      // user wants to deselect rubric
      rubrics = rubrics.filter(function(rubric) {
        return rubric !== rubricId;
      });
    } else {
      // user wants to select rubric
      if (!_.contains(rubrics, rubricId)) {
        rubrics.push(rubricId);
      }
    }

    // TODO: make graded a computed property
    // update model with new rubrics
    this.response.save({ rubrics: rubrics }, { wait: true });
  },

  /* Make this rubric editable. */
  edit: function(event) {
    // this function may be called by other views, so event may not exist
    if (event) {
      event.preventDefault();
    }

    this.editing = true;
    this.render();

    // automatically focus the rubric description input, moving the mouse to the
    // end of the input box
    var $descriptionInput = this.$('.rubric-description');
    $descriptionInput.focus();
    var descriptionLength = $descriptionInput.val().length;
    $descriptionInput[0].setSelectionRange(descriptionLength, descriptionLength);
  },

  /* Save the edits made to this rubric. */
  save: function(event) {
    // this function may be called by other views, so event may not exist
    if (event) {
      event.preventDefault();
    }

    var description = this.$('.rubric-description').val();
    var points = parseFloat(this.$('.rubric-points').val(), 10);

    // use the correct sign if the assessment is graded down
    var gradeDown = this.response.get('questionPart').gradeDown;
    if (gradeDown) {
      points = -points;
    }

    var self = this;
    this.model.save({
      description: description,
      points: points
    }, {
      wait: true,

      // Re-render manually after completion. We don't listen for the change
      // event to re-render the model, since we want to get out of edit mode
      // even if the description/points weren't actually changed.
      success: function() {
        self.editing = false;
        self.render();
      }
    });
  },

  /* Destroys this rubric, removing it from the DOM. */
  destroy: function(event) {
    event.preventDefault();
    this.model.destroy({ wait: true });
    this.removeSideEffects();
    this.remove();
  },

  checkIfShouldSave: function(event) {
    var $clicked = $(event.target);
    if (this.blurred && this.editing && !$clicked.hasClass('rubric-description') &&
        !$clicked.hasClass('rubric-points')) {
      this.blurred = false;
      this.save();
    }
  },

  setBlurred: function() {
    // when true, this is the time between when the input box was just blurred
    // but the click/focus event on another DOM element has not yet triggered
    this.blurred = true;
  }
});
