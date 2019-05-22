$(document).ready(function () {
    $('.rsvp-response .btn[data-response]').click(function () {
        var $btn = $(this);
        var $response = $btn.closest('.rsvp-response');
        var repetition = 1 * $response.attr('data-repeat-type');
        var accept_hit = $btn.is('.rsvp-accept-type');

        var $dialog = $response.find('.rsvp-dialog');
        if (accept_hit || repetition) {
            var button_type = $btn.text().trim() || $response.find('.btn[data-response="Accept"]').text(); // Later is for arrow button to skip translation in JS
            if ($dialog.is(':visible') && $dialog.find('.btn-primary').attr('value') === button_type) {
                $dialog.hide();
            } else {
                $dialog.find('.rsvp-dialog-repetition-type')[repetition ? 'show' : 'hide']();
                $dialog.find('.rsvp-dialog-attendance-type')[accept_hit || $btn.attr('data-response') === 'Accept' ? 'show' : 'hide']();
                $dialog.find('.btn-primary').attr('value', button_type);
                $dialog.data('btn', $btn);
                $dialog.show();
            }
        } else {
            rsvp_response_for_btn($btn, $response.attr('data-for-repetition'), '0', null);
        }
    });


    $('.rsvp-dialog .btn-cancel').click(function () {
        $(this).closest('.rsvp-dialog').hide();
    });


    $('.rsvp-dialog .btn-primary').click(function (e) {
        e.preventDefault();

        var $dialog = $(this).closest('.rsvp-dialog');
        var $btn = $dialog.data('btn');

        var for_repetition = $dialog.find('.rsvp-apply-type:checked').val() || 'true';
        var attendance_visible = $dialog.find('.rsvp-dialog-attendance-type').is(':visible');
        var accept_type = attendance_visible ? $dialog.find('.rsvp-accept-type:checked').val() || '0' : '0';
        var note = attendance_visible ? $dialog.find('.rsvp-accept-note').val() : null;

        rsvp_response_for_btn($btn, for_repetition, accept_type, note)
    });


    function rsvp_response_for_btn($btn, for_repetition, accept_type, note) {
        var $response = $btn.closest('.rsvp-response');

        var repetition_id = $response.attr('data-repetition-id');
        var response = $btn.attr('data-response');

        $.ajax({
            url: window.urls.rsvp_response,
            type: 'POST',
            data: {
                repetition: repetition_id,
                for_repetition: for_repetition,
                response_text: response,
                accept_type: accept_type,
                note: note
            }
        }).then(
            function (success) {
                $response.attr('data-response', success.response);
                $btn.closest('.rsvp-response').find('.rsvp-dialog').hide();
            },
            function (error) {
                alert("Unable to set/change RSVP response");
                console.log(error);
            }
        );
    }
});