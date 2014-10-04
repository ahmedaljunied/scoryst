$(function() {
  // TODO: Why does this file exist? Move this code into history.js (and should
  // rename history.js --> submit.js)
  // Depending on whether group submissions are allowed, the field to enter in
  // partner email(s) hides/shows. Also, the max group size is shown.
  var $groupMembersFormGroup = $('.group-members');
  var groupValues = $('.group-values').html().toLowerCase();
  groupValues = JSON.parse(groupValues);
  var maxGroupSizes = $('.max-group-sizes').html();
  maxGroupSizes = JSON.parse(maxGroupSizes);

  if (!groupValues[0]) {
    $groupMembersFormGroup.hide();
  } else {
      $('.max-group-size').html(maxGroupSizes[0]);
  }

  $('#id_homework_id').on('change', function() {
    if (groupValues[this.selectedIndex]) {
      $groupMembersFormGroup.show();
      $('.max-group-size').html(maxGroupSizes[this.selectedIndex]);
    } else {
      $groupMembersFormGroup.hide();
    }
  });


  // Creates popovers
  $('.finalized-info-popover').popover();
  var fileSizeExceededTemplate = _.template($('.file-size-exceeded-template').html());

  var pdfInfoPopoverText = 'Not sure how to create a PDF? ' +
    'Just follow the instructions below.';

  var $pdfInfoPopover = $('.pdf-info-popover');
  $pdfInfoPopover.popover({ content: pdfInfoPopoverText });

  var $createPdfInfo = $('.create-pdf-info');
  // When the popover is being displayed, highlight the part that gives
  // instructions on how to create PDFs
  $pdfInfoPopover.on('shown.bs.popover', function () {
    $createPdfInfo.addClass('highlighted');
  });

  $pdfInfoPopover.on('hidden.bs.popover', function () {
    $createPdfInfo.removeClass('highlighted');
  });


  // Check for File API support
  if (window.FileReader && window.File && window.FileList && window.Blob) {
    var $uploadForm = $('.upload-exam');
    // In MB. Note that this value is also used in the backend, so in case of
    // any change it must also be changed in the backend.
    var MAX_FILE_SIZE = 40;
    var BYTES_IN_MB = 1024 * 1024;

    // When the form is submitted, check the file size. If the file size is
    // bigger than MAX_FILE_SIZE, prevent the submission and display an error
    $uploadForm.submit(function(event) {
      var $homeworkFile = $('#id_homework_file');
      var fileSize = $homeworkFile[0].files[0].size / BYTES_IN_MB;
      // Round up to nearest hundredth for display purposes
      fileSize = Math.ceil(fileSize * 100) / 100;

      if (fileSize > MAX_FILE_SIZE) {
        $homeworkFile.next('.error').html(fileSizeExceededTemplate({
          MAX_FILE_SIZE: MAX_FILE_SIZE,
          fileSize: fileSize
        }));
        event.preventDefault();
      } else {
        $uploadForm.find('button[type=submit]').attr('disabled', 'disabled');
      }
    });
  }
});
