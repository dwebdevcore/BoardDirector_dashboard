$(document).ready(function(){
    $("#id_phone_number, #id_work_number, #id_secondary_phone").mask("999-999-9999?9");
    $('#id_affiliation, #id_social_media_link').each(function(){
       var input = $(this);
       var input_parent = input.parent();
       var values = input.val().split(',');
       var element, parent;
       for (var i=0, max=values.length; i<max; i++){
           parent = $(this).parent().clone();
           element = parent.find('input');
           element.attr('id', input.attr('id') + '_' + i);
           element.attr('name', input.attr('name') + '_' + i);
           element.attr('data-parent', input.attr('id'));
           element.addClass('array-field');
           element.val(values[i]);
           if (max>1){
               parent.find('div').attr('hidden', false);
           }
           input_parent.before(parent);
       }
       input_parent.before('<div class="reset add-other"></div>');
       input_parent.hide();
    });

    $('input[type="reset"]').on('click', function(event){
        event.preventDefault();
        $('form').get(0).reset();
        $('input[data-parent]').each(function(){
           var input = $(this);
           var values = input.val().split(',');
           var i = input.attr('id').split('_');
           i = parseInt(i[i.length - 1]);
           input.val(values[i]);
        });
    });

    $('.array-field').live('keyup', function(e){
        e.preventDefault();
        changeValues(0, this);
    });

    $('.add-other').on('click', function(e){
        e.preventDefault();
        var parent = $(this).prev().clone();
        parent.find('div').attr('hidden', false);
        var element = parent.find('input');
        var i = element.attr('id').split('_');
        i = parseInt(i[i.length - 1]);
        element.attr('id', element.attr('id').replace(i, i+1));
        element.attr('name', element.attr('name').replace(i, i+1));
        element.val('');
        $(this).before(parent);
        var el = $('[id^="' + element.data('parent') + '_"]');
        if (el.length > 1){
            el.parent().find('div').attr('hidden', false);
        }
    });

    $('.remove').live('click', function(e){
        e.preventDefault();
        var element = $(e.target).parent();
        var input = element.find('input').val('');
        changeValues(0, input);
        element.remove();
        var el = $('[id^="' + input.data('parent') + '_"]');
        if (el.length == 1){
            el.parent().find('div').attr('hidden', true);
        }
    })

});

function changeValues(i, el){
    var input = $(el);
    var data = '';
    $('[id^="' + input.data('parent') + '_"]').each(function(){
        if($(this).val()){
            data += $(this).val() + ',';
        }
    });
    $('#' + input.data('parent')).val(data.substring(0, data.length - 1));
}
