$(document).ready(function() {
    $(document).on('click', '.delete', function (event) {
        event.preventDefault();
        var url = $(this).attr('href');

        var kendoWindow = $("<div />").kendoWindow({
            title: gettext('Confirm'),
            resizable: false,
            modal: true,
            height: "110px",
            width: "210px",
            visible: false
        });

        kendoWindow.data("kendoWindow")
            .content($("#delete-confirmation").html())
            .center().open();

        kendoWindow
            .find(".delete-confirm,.delete-cancel")
            .click(function(e) {
                e.preventDefault();
                if ($(this).hasClass("delete-confirm")) {
                    var request = $.ajax({
                        url: url,
                        type: "POST",
                        success: function(response) {
                            window.location.href = response.url;
                        }
                    });
                }
                kendoWindow.data("kendoWindow").close();
            })
            .end();
    });
});