function init_add_folder_modal() {
    var $modal = $('#add-folder-dialog');
    $modal.dialog('open');
    $('.popup-overlay').show();
}

function add_folder() {
    if (!$('#id_add-name').val().length) {
        return;
    }
    var $form = $('#add-folder-form');
    send_form($form);
}

function init_edit_folder_modal(form_action, folder_name) {
    var $modal = $('#edit-folder-dialog');
    // Init form
    var $form = $('#edit-folder-form');
    $form.attr('action', form_action);
    $form.find('#id_edit-name').val(folder_name);
    $modal.dialog('open');
    $('.popup-overlay').show();
}

function edit_folder() {
    if (!$('#id_edit-name').val().length) {
        return;
    }
    var $form = $('#edit-folder-form');
    send_form($form);
}

function send_form($form) {
    $.post($form.attr('action'), $form.serialize())
        .done(function(data) {
            location.reload();
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            var errors = $.parseJSON(jqXHR.responseText);
            var error_text = errors.join('<br>');
            var message = $('.message.error');
            $('.folder-messages').removeClass('hidden');
            if(message.length) {
                message.text(error_text);
            }
    });
}

function update_folder_ordering(ev, ui, post_url) {
    // jquery-sortable -- handler for `sorting stopped` event
    var items = $('ul.folder-items.sortable > li');
    var orders = [];
    for(var i=0; i<items.length; i++){
        var item = items[i];
        var itype= item.getAttribute('data-itype');
        var iid= item.getAttribute('data-iid');
        if (itype && iid){
            orders.push([i,itype,iid]);
        }
    }
    // console.log("@update_folder_ordering >orders=", ui, post_url, orders);
    $.post(post_url, {'ordering': orders})
    .done(function() {})
    .fail(function() { console.log("fail");});
}

function file_dropped(ev, ui){
    // jquery-droppable -- handler for `file dropped on folder icon` event

    var doc_id = ui.draggable.data('iid');
    var doc_type = ui.draggable.data('itype');
    var doc_name = $.trim($('.folder-items-name', ui.draggable).text());
    
    var folder = $(ev.target).closest('li.folder');
    var folder_id = folder.data('iid');
    var folder_slug = folder.data('islug');
    var folder_name = $.trim($('.folder-items-name', folder).text());

    // show confirmation dialog    
    var moveConfirm = $('#confirm-move-file');
    var post_url = moveConfirm.attr('data-move-document-url').replace('000000000', doc_id);
    $('form', moveConfirm).attr('action', post_url);
    $('input[name="target_slug"]', moveConfirm).attr('value', folder_slug);
    $('input[name="document_id"]', moveConfirm).attr('value', doc_id);
    $('div.subtitle', moveConfirm)
    .html("Confirm moving file '<b>"+ doc_name + "</b>' to folder '<b>" + folder_name + "</b>'.");
    moveConfirm.dialog('open');
    $('.popup-overlay').show();

}

$(document).ready(function() {
    // Add folder modal
    $(document).on('click', '#add-folder', function (event) {
        event.preventDefault();
        init_add_folder_modal();
    });

    var addDialog = $('#add-folder-dialog');
    addDialog.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        buttons: [
        {
            text: addDialog.attr('data-cancel-button-text'),
            click: function() {
                $(this).dialog('close');
                $('.popup-overlay').hide();
            },
            class: 'cancel-button'
        },
        {
            text: addDialog.attr('data-send-button-text'),
            click: function() {
                add_folder();
                $(this).dialog('close');
                $('.popup-overlay').hide();
            },
            class: 'form-send-button'
        }
        ],
        beforeClose: function( event, ui ) {
            $('.popup-overlay').hide();
        }
    });
    // Edit folder modal
    $(document).on('click', 'a.edit-folder-link', function (event) {
        event.preventDefault();
        var form_action = $(this).data('form-action');
        var folder_name = $(this).data('folder-name');
        init_edit_folder_modal(form_action, folder_name);
    });
    var updDialog = $('#edit-folder-dialog');
    updDialog.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        buttons: [
        {
            text: updDialog.attr('data-cancel-button-text'),
            click: function() {
                $(this).dialog('close');
                $('.popup-overlay').hide();
            },
            class: 'cancel-button'
        },
        {
            text: updDialog.attr('data-send-button-text'),
            click: function() {
                edit_folder();
                $(this).dialog('close');
                $('.popup-overlay').hide();
            },
            class: 'form-send-button'
        }
        ],
        beforeClose: function( event, ui ) {
            $('.popup-overlay').hide();
        }
    });
    // Disable form submit on enter
    $('#add-folder-form, #edit-folder-form').on('keyup keypress', function(e) {
      var keyCode = e.keyCode || e.which;
      if (keyCode === 13) {
        e.preventDefault();
        $(this).parents('.ui-dialog').find('.form-send-button').click();
      }
    });
    // Delete Folder
    $(document).on('click', '.delete-folder-link', function (event) {
        event.preventDefault();
        var url = $(this).attr('href');

        var kendoWindow = $('<div />').kendoWindow({
            title: gettext('Confirm'),
            resizable: false,
            modal: true,
            height: '100px',
            width: '255px',
            visible: false
        });

        kendoWindow.data('kendoWindow')
            .content($('#delete-folder-confirmation').html())
            .center().open();

        kendoWindow
            .find('.delete-confirm,.delete-cancel')
            .click(function(e) {
                e.preventDefault();
                if ($(this).hasClass('delete-confirm')) {
                    $.ajax({
                        url: url,
                        type: 'POST',
                        success: function(response) {
                            location.reload();
                        }
                    });
                }
                kendoWindow.data('kendoWindow').close();
            })
            .end();
    });

    var moveConfirm = $('#confirm-move-file');

    moveConfirm.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        buttons: [
            {
                text: "Cancel",
                click: function() {
                    $(this).dialog("close");
                    $('.popup-overlay').hide();
                },
                class: 'cancel-button'
            },
            {
                text: "Move",
                click: function() {
                    $(this).dialog("close");
                    $('.popup-overlay').hide();
                    var form = $('#confirm-move-file form');
                    $.post(form.attr('action'), form.serialize())
                        .done(function(data) {location.reload();})
                        .fail(function(e) {console.log(e);});
                }
            }
        ],
        beforeClose: function( event, ui ) {$('.popup-overlay').hide();}
    });

    // Sort button margin
    var $sort = $('#sort');
    if (!$sort.length) {
        console.log('NOTE: #sort not found on page');
    } else {
        if ($('.folder-action').length == 0) {
            $sort.attr('style', 'margin-right: 20px;');
        }

        p = $sort.position();
        $('.sortingLinks').css('left', p.left - 50);
        $sort.click(function () {
            $('.sortingLinks').toggle();
            return false;
        });
    }

    // Folder items sublinks
    $(document).click(function () {
        $('.sublinkslist').hide();
    });
    $('.sublinks').click(function () {
        var target = $(this).next('.sublinkslist');
        $('.sublinkslist').not(target).hide();
        target.toggle();
        return false;
    });

    var sortable_folder = $(".folder-items.sortable");
    var post_url = sortable_folder.data('ordering-url');
    if (sortable_folder && post_url){

        sortable_folder.sortable({
            'stop': function(ev,ui){update_folder_ordering(ev, ui, post_url);},
            'cursor': 'grabbing',
            'distance': 10,
        });
        
        $('li.folder a.list-folder-new', sortable_folder).droppable({
            'accept': 'li.file',
            'drop': file_dropped,
            'tolerance': 'pointer'
        });

        sortable_folder.disableSelection();
    }

});
