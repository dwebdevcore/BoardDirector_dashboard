$(document).ready(function () {

    /// delete confirmation dialog with jQuery UI
    var deleteConfirm = $('#delete-confirm');

    deleteConfirm.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        closeText: '',
        
        buttons: [
            {
                text: "Delete",
                click: function () {
                    $(this).dialog("close");
                    $('.popup-overlay').hide();
                    $('#content .message').remove();
                    var form = $('#delete-form');
                    $.post(form.attr('action'), form.serialize())
                        .done(function (data) {
                            window.location = data.url;
                        })
                        .fail(function () {
                            $('#content').prepend('<div class="message">Error</div>');
                        })
                }
            },
            {
                text: "Cancel",
                click: function () {
                    $(this).dialog("close");
                    $('.popup-overlay').hide();
                },
                class: 'cancel-button'
            }
        ],
        beforeClose: function (event, ui) { $('.popup-overlay').hide(); }
    });

    $('.delete-button').click(function (event) {
        event.preventDefault();
        var deleteConfirm = $('#delete-confirm');
        deleteConfirm.dialog('open');
        $('.popup-overlay').show();
        deleteConfirm.attr('data-url', $(this).attr('data-url'));
        $('#delete-form').attr('action', $(this).attr('data-form-action-url'));
        deleteConfirm.attr('active-btn', $(this).attr('id'));
    });


});