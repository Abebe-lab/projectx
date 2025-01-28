$(document).ready(function() {
  $("#detailButton").click(function() {
    var memoId = $(this).data("memo-id");
    window.location.href = "/memo-details/" + memoId + "/";
  });
});
