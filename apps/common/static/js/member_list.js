var body = $('body');
$(document).ready(function(){
    $('.list-view').on('click', function(){
        $('.sort-list li a').removeClass('active');
        $(this).addClass('active');
        $('.container').removeClass('grid');
        return false;
    });

    $('.grid-view').on('click', function () {
        $('.sort-list li a').removeClass('active');
        $(this).addClass('active');
        $('.container').addClass('grid');
        return false;
    });

    $('#browse-by').on('change', function(){
        var val = $(this).val();
        var email = '';
        if (val == 'chairman') {
            $('.member-active').addClass('hidden');
            $('.member-active[data-chairman="true"]').removeClass('hidden').each(function(){
                email = email + '<' + $(this).find('a.email-l').data('email') + '>,';
            });
        } else if (val) {
            $('.member-active').addClass('hidden');
            $('.member-active[data-role="'+val+'"]').removeClass('hidden');
            $('.member-active[data-role="'+val+'"][data-invited="true"]').each(function(){
                email = email + '<' + $(this).find('a.email-l').data('email') + '>,';
            });
        } else {
            $('.member-active').removeClass('hidden').each(function(){
                email = email + '<' + $(this).find('a.email-l').data('email') + '>,';
            });
        }
        $('#mail-to').attr('href', 'mailto:' + email);
    })

    $('#id_social_media_link').each(function(){
       var input = $(this);
       var input_parent = input.parent();
       var values = input.attr('href').split(',');
       var element, parent;
       for (var i=0, max=values.length; i<max; i++){
           parent = $(this).parent().clone();
           element = parent.find('a');
           element.attr('id', input.attr('id') + '_' + i);
           element.attr('href', values[i]);
           if (values[i].indexOf("facebook.com") > 0){
               element.attr('class', 'facebook');
           } else if (values[i].indexOf("linkedin.com") > 0){
               element.attr('class', 'linkedin');
           } else if (values[i].indexOf("twitter.com") > 0){
               element.attr('class', 'twitter');
           } else {
               element.attr('class', 'hyperlink');
           }
           if (max>1){
               parent.find('li').attr('hidden', false);
           }
           input_parent.before(parent);
       }
       input_parent.remove();
    });
});
