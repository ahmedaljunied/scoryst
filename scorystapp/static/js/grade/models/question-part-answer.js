$.cookie.raw = true;
var CSRF_TOKEN = $.cookie('csrftoken');
$.cookie.raw = false;

// TODO: browserify
var QuestionPartAnswerModel = Backbone.Model.extend({
  url: function() {
    return this.collection.url() + this.get('id') + '/';
  },

  sync: function(method, model, options) {
    options = options || {};
    if (method !== 'read' && method !== 'update') {
      // we only allow reading/updating a single instance
      throw 'Can only read or update question part answers.';
    }

    // add CSRF token to requests
    options.beforeSend = function(xhr) {
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
    };

    return Backbone.sync.apply(this, arguments);
  }
});

var QuestionPartAnswerCollection = Backbone.Collection.extend({
  model: QuestionPartAnswerModel,
  url: function() {
    return window.location.href + 'question-part-answer/';
  },

  sync: function(method, model, options) {
    options = options || {};
    if (method !== 'read') {
      // we only allow reading the list of question parts
      throw 'Can only read the list of question parts.';
    }

    return Backbone.sync.apply(this, arguments);
  }
});
