$(function () {
   function handleFileSelect(evt) {
    evt.stopPropagation();
    evt.preventDefault();

    var files = evt.dataTransfer.files; // FileList object.
    var reader = new FileReader();
    reader.onload = function(event) {
         document.getElementById('drop_zone').value = event.target.result;
    }
    reader.readAsText(files[0],"UTF-8");
  }

  function handleDragOver(evt) {
    evt.stopPropagation();
    evt.preventDefault();
    evt.dataTransfer.dropEffect = 'copy'; // Explicitly show this is a copy.
  }

  // Setup the dnd listeners.
  var dropZone = document.getElementById('drop_zone');
  dropZone.addEventListener('dragover', handleDragOver, false);
  dropZone.addEventListener('drop', handleFileSelect, false);

  $('#csv_form').ajaxForm({
      delegation: true,
      error: function (data, statusText, shr, $form) {
          toastr.error('Server encountered an error. Please try again.');
      },
      success: function (data, statusText, xhr, $form) {
          if(data.status === 'success') {
              toastr.success(data.message);
          } else {
              toastr.error(data.message);
          }
      }
  })
});