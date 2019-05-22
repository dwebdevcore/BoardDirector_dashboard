function delete_document(data){
    $('#item_' + data.doc_id).fadeOut(500, function(){
        var board_book = '<li><label for="id_board_book">' + gettext('Add Board Book') + '</label><input id="id_board_book" name="board_book" type="file"></li>';
        var agenda = '<li><label for="id_agenda">' + gettext('Add Agenda') + '</label><input id="id_agenda" name="agenda" type="file"></li>';
        var minutes = '<li><label for="id_minutes">' + gettext('Add Minutes') + '</label><input id="id_minutes" name="minutes" type="file"></li>';
        var closest_li = $(this).closest('.archives').parent();

        if (data.doc_type == '4') { closest_li.before(board_book); board_book_kendo_init(); }
        if (data.doc_type == '1') { closest_li.before(agenda); agenda_kendo_init(); }
        if (data.doc_type == '2') { closest_li.before(minutes); minutes_kendo_init(); }

        if ($(this).parent().children('.edit-uploader-block').length) $(this).parent().remove();
        else $(this).remove();
    });
}

function get_update_document_tabs(id, tabs) {
    var tabs_head = '';
    var tabs_body = '';
    for (var i = 0; i < tabs.length; i++) {
        tabs_head += '<li' +  (i === 0 ? ' class="k-state-active"' : '') + '>' + tabs[i]['head'] + '</li>';
        tabs_body += '<div>' + tabs[i]['body'] + '</div>';
    }
    return '<div id="' + id + '" class="document-edit-item"><ul>' + tabs_head + '</ul>' + tabs_body + '</div>';
}

function get_update_document_block(doc_id, doc_type, id, name) {
    var id_tabs = id + "_tabs";
    var id_filename = id + "_filename";
    var name_filename = name + "_filename"
    var tabs = [
        {
            head: gettext('Upload new version'),
            body: '<div class="edit-uploader-block"><input id="' + id + '" name="' + name + '" type="file"></div>'
        },
        {
            head: gettext('Rename'),
            body: '<input id="' + id_filename + '" name="' + name_filename + '" type="text" /><a class="label update" data-doc-id="' + doc_id + '" data-doc-type="' + doc_type + '" href="">' + gettext('Rename') + '</a>'
        }
    ]
    return get_update_document_tabs(id_tabs, tabs);
}

function update_document(doc_id, doc_type){
    var item = $('#item_' + doc_id);

    // remove previous uploader-blocks for documents
    if (doc_type == '3') {
        var archives = item.closest('.archives');
        archives.find('.edit-block > .item').unwrap();
        archives.find('.document-edit-item').remove();
    }

    if (!item.next().is('.document-edit-item')) {
        item.wrap('<div class="edit-block">');

        if (doc_type == '1') {
            item.after(get_update_document_block(doc_id, doc_type, 'id_agenda', 'agenda'));
            agenda_kendo_init();
        }
        if (doc_type == '2') {
            item.after(get_update_document_block(doc_id, doc_type, 'id_minutes', 'minutes'));
            minutes_kendo_init();
        }
        if (doc_type == '3') {
            item.after(get_update_document_block(doc_id, doc_type, 'id_temp_doc', 'other'));
            temp_doc_kendo_init();
        }
        if (doc_type == '4') {
            item.after(get_update_document_block(doc_id, doc_type, 'id_board_book', 'board_book'));
            board_book_kendo_init();
        }
    }
}

function onBoardBookUpload(e) {
    var item_temp = $('#id_board_book');
    e.data = {'csrfmiddlewaretoken': csrftoken, 'type': item_temp.attr('name')};
    upload(e, item_temp)
}

function onAgendaUpload(e) {
    var item_temp = $('#id_agenda');
    e.data = {'csrfmiddlewaretoken': csrftoken, 'type': item_temp.attr('name')};
    upload(e, item_temp)
}

function onMinutesUpload(e) {
    var item_temp = $('#id_minutes');
    e.data = {'csrfmiddlewaretoken': csrftoken, 'type': item_temp.attr('name')};
    upload(e, item_temp)
}

function onDocsUpload(e) {
    e.data = {'csrfmiddlewaretoken': csrftoken, 'type': $('#id_other').attr('name')};
}

function onTempDocsUpload(e) {
    var item_temp = $('#id_temp_doc');
    e.data = {'csrfmiddlewaretoken': csrftoken, 'action': 'update', 'type': item_temp.attr('name')};
    upload(e, item_temp)
}

function onSuccess(e) {
    console.log("Status: " + e.response.status);
    console.log("Object pk: " + e.response.pk);
    var group = $(this.element).data('group');
    add_to_uploaded(e.response.pk, group);
    if (e.response.html) {
        var html = e.response.html;
        var type = e.response.type;
        if (type == 'other') type = 'temp_doc';
        var item_temp = $('#id_' + type).closest('.edit-uploader-block');
        item_temp.before(html);
    }
}

function add_to_uploaded(pk, group) {
    var uploaded = $("#id_uploaded");
    var value = uploaded.val();
    if (value) value += ',';
    uploaded.val(value + pk);
}

function upload(e, item_temp){
    var closest_edit_block_item = item_temp.closest('.edit-block').find('.item');
    var edit_item = closest_edit_block_item.find('.edit');
    var download_item = closest_edit_block_item.find('.download');
    var document_id = edit_item.attr('data-doc-id') || download_item.attr('data-doc-id');
    e.data['meeting'] = edit_item.attr('data-doc-meeting') || download_item.attr('data-doc-meeting');
    var request = $.ajax({
        url: DOC_DELETE_URL,
        type: "POST",
        data: {
            document_id: document_id,
            action: 'update'
        },
        success: function(response) {
            closest_edit_block_item.remove();
        }
    });
}
