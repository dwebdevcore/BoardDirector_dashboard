jQuery(document).ready(function($) {

    $('#cancel_account').live("click", function (event) {
        event.preventDefault();

        var kendoWindow = $("<div />").kendoWindow({
            title: gettext('Confirm'),
            resizable: false,
            modal: true,
            height: "95px",
            width: "205px",
            visible: false
        });

        kendoWindow.data("kendoWindow")
            .content($("#delete-account-confirmation").html())
            .center().open();

        kendoWindow
            .find(".delete-confirm,.delete-cancel")
            .click(function(e) {
                e.preventDefault();
                if ($(this).hasClass("delete-confirm")) {
                    var request = $.ajax({
                        url: ACC_CANCEL_URL,
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

    $('#yearly_payment').live("click", function (event) {
        event.preventDefault();

        $.ajax({
            url: ACC_BILLING_CYCLE_URL,
            type: "POST",
            success: function(response) {
                window.location.href = response.url;
            }
        });
    });

    $('#myCheckbox0, #myCheckbox1, #saveform').click(function(event){
        event.preventDefault();
        var form = $('#send-notification-form');
        $.post(form.attr('action'), form.serialize());
    })

    $('#send-notification-form').submit(function(event){
        event.preventDefault();
        var form = $('#send-notification-form');
        $.post(form.attr('action'), form.serialize());
    })

});