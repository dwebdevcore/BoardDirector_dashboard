jQuery(document).ready(function($) {
  $('.close-guide').click(function (event) {
    event.preventDefault();
    var href = $(this).attr('href');

    var kendoWindow = $("<div />").kendoWindow({
        title: gettext('Confirm'),
        resizable: false,
        modal: true,
        height: "95px",
        width: "205px",
        visible: false
    });

    kendoWindow.data("kendoWindow")
        .content($("#close-guide-confirmation").html())
        .center().open();

    kendoWindow
        .find(".delete-confirm,.delete-cancel")
        .click(function(e) {
            e.preventDefault();
            if ($(this).hasClass("delete-confirm")) {
                window.location.href = href;
            }
            kendoWindow.data("kendoWindow").close();
        })
        .end();
  });
});
