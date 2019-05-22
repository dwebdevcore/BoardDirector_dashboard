var body = $('body');
$(document).ready(function(){
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
           element.text(values[i]);
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
