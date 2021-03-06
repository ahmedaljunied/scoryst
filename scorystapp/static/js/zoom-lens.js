// TODO: browserify
// The `ZoomLensView` is responsible for the enabling/disabling zoom button and
// for showing/hiding the zoom lens.
var ZoomLensView = IdempotentView.extend({
  ZOOM_LENS_OFFSET_FROM_MOUSE: 20,

  events: {
    'click .enable-zoom': 'toggleZoom',
    'mouseleave .zoom-lens': 'hideZoomLens',
    'mousemove .zoom-lens': 'moveZoomLens',

    // This event is for an assessment canvas with freeform annotations
    'mouseenter .freeform-annotations-canvas': 'showZoomLens',

    // This event is for an assessment canvas without freeform annotations
    'mouseenter .assessment-image': 'showZoomLens'
  },

  initialize: function(options) {
    this.constructor.__super__.initialize.apply(this, arguments);

    this.$zoomLens = this.$el.find('.zoom-lens');
    this.curPageNum = options.curPageNum;
    this.createdImage = false;
    this.image = new Image();
    this.loadImage();

    if (localStorage && localStorage.zoomLensEnabled === 'true') {
      // This is needed if the user refreshes the page. this.zoomLensEnabled might be true
      // but by default the button shows 'Enable Zoom'. This accounts for this edge case.
      this.enableZoom();
      this.$('.enable-zoom').addClass('active');
    } else {
      this.zoomLensEnabled = false;
    }
  },

  loadImage: function() {
    if (this.zoomLensEnabled) {
      var imageSource = 'get-assessment-jpeg-large/' + this.curPageNum + '/';

      // dynamically create the image tag
      if (!this.createdImage) {
        this.createdImage = true;
        $('img.enlarged-exam').remove();
        this.$zoomImage = $('<img class="enlarged-exam" alt="Enlarged Exam" />').appendTo(
                            this.$el.find('.zoom-lens'));
      }

      this.$zoomImage.attr('src', imageSource);
      this.image.src = imageSource;
    }
  },

  toggleZoom: function() {
    if (this.zoomLensEnabled) {
      this.disableZoom();
    } else {
      this.enableZoom();
    }
  },

  enableZoom: function() {
    if (localStorage) {
      localStorage.zoomLensEnabled = true;
    }

    this.zoomLensEnabled = true;
    this.loadImage();

    this.$el.addClass('zoom-enabled');
  },

  disableZoom: function() {
    if (localStorage) {
      localStorage.zoomLensEnabled = false;
    }

    this.zoomLensEnabled = false;
    this.$el.removeClass('zoom-enabled');
  },

  showZoomLens: function() {
    if (this.zoomLensEnabled) {
      this.$zoomLens.show();
    }
  },

  hideZoomLens: function() {
    this.$zoomLens.hide();
  },

  moveZoomLens: function(event) {
    if (!this.zoomLensEnabled) {
      return;
    }

    var offset = this.$zoomLens.offset();
    x = event.pageX - offset.left;
    y = event.pageY - offset.top;

    // Get the offset top and left of the large image
    var $assessmentCanvas = $('.assessment-canvas');
    this.$zoomLens.height($assessmentCanvas.height());
    this.$zoomLens.width($assessmentCanvas.width());

    var offsetLeft = -x / this.$zoomLens.width() * this.image.naturalWidth;
    var offsetTop = -y / this.$zoomLens.height() * this.image.naturalHeight;

    this.$zoomImage.css('top', offsetTop);
    this.$zoomImage.css('left', offsetLeft);
  },

  changeAssessmentPage: function(curPageNum) {
    this.curPageNum = curPageNum;
    this.loadImage();
  }
});
