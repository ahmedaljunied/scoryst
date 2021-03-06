// TODO: browserify
var SubmissionPageModel = Backbone.Model.extend({});

var SubmissionPageCollection = Backbone.Collection.extend({
  model: SubmissionPageModel,
  url: function() {
    return window.location.pathname + 'submission-page/';
  },

  sync: function(method, model, options) {
    options = options || {};
    if (method !== 'read') {
      throw 'Can only read the list of submission pages.';
    }

    return Backbone.sync.apply(this, arguments);
  }
});
