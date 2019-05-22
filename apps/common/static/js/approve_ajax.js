$(document).ready(function () {

    $('a.approve-doc').click(function (e) {

        e.preventDefault();

        var $btn = $(this);

        var $href = $btn.attr('href');
        if ($href.length == 0){
            return False;
        }

        $.ajax({
            url: $btn.attr('href'),
            type: 'GET',
        }).then(
            function (success) {
                if (success.approval_id > 0){
                    $btn.attr('class', 'approved-doc');
                    $btn.attr('href', '');
                    $btn.html("<i class='fa fa-check'></i>&nbsp;Approved");
                    // $btn.unbind('click');
                }
            },
            function (error) {
                console.log(error);
            }
        );

        return false;
    });

});