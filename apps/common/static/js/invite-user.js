jQuery(document).ready(function($) {

    var inviteDialog = $('#invite-dialog');
    inviteDialog.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        closeText: '',
        buttons: [
        {
            text: inviteDialog.attr('data-send-button-text'),
            click: function() {
                $(this).dialog("close");
                $('.popup-overlay').hide();
                var form = $('#invite-form');
                $('#content .message').remove();
                $.post(form.attr('action'), form.serialize())
                    .done(function(data) {
                        $('#content').prepend('<div class="message success">' + data.msg + '</div>');
                        $('#'+inviteDialog.attr('active-btn')).text(inviteDialog.attr('data-resend-text'));
                    })
                    .fail(function() {
                        $('#content').prepend('<div class="message">Error</div>');
                    })
            }
        },
        {
            text: inviteDialog.attr('data-cancel-button-text'),
            click: function() {
                $(this).dialog("close");
                $('.popup-overlay').hide();
            },
            class: 'cancel-button'
        }
        ],
        beforeClose: function( event, ui ) {
            $('.popup-overlay').hide();
        }
    });

    $('#invite-popup-button').click(function(event){
        event.preventDefault();
        $('#invite-dialog').dialog('open');
        $('.popup-overlay').show();
    });

    $('.invite-popup-button').click(function(event){
        event.preventDefault();
        var inviteDialog = $('#invite-dialog');
        inviteDialog.dialog('open');
        $('.popup-overlay').show();
        inviteDialog.attr('data-url', $(this).attr('data-url'));
        $('#invite-dialog form').attr('action', $(this).attr('data-form-action-url'));
        $('#invite-dialog form input#invite-user').attr('value', $(this).attr('data-user-name'));
        inviteDialog.attr('active-btn', $(this).attr('id'));
    });
});
