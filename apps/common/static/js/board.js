$(document).ready(function() {
    $('.account-list li a:not(.start_subscription)').live("click", function (event) {
        event.preventDefault();
        var accId = $(this).attr('data-account');
        var url = BOARD_SET_URL;
        if ($(this).hasClass('reactivate')) url = BOARD_REACTIVATE_URL;
        if (accId) {
            $.ajax({
                url: url,
                type: "POST",
                data: {
                    account_id: accId
                },
                success: function(response) {
                    window.location.href = response.url;
                }
            });
        }
    });
});
