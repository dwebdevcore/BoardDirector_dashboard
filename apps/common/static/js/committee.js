$(document).ready(function() {
    var stylesheets = [];
    $('link[rel="stylesheet"]').each(function (style) {
        var href = $(this).attr('href');
        if (href) {
            stylesheets.push(href);
        }
    });

    var editor = $(".kendo_editor").kendoEditor({
        encoded: false,
        stylesheets: stylesheets
    }).data('kendoEditor');
    console.log(editor.body);
    $(editor.body).addClass('committee-description');

    $( ".multiple" ).each(function( index ) {
        $(this).selectize({
            plugins: ['remove_button'],
            dropdownParent: 'body'
        });
    });

    file_kendo_init();
});

function delete_document(data){
    $('#item_' + data.doc_id).fadeOut(500, function(){
        var charter = '<li><label for="id_file">' + gettext('Add Charter') + '</label><input id="id_file" name="file" type="file"></li>';
        var closest_li = $(this).closest('.archives').parent();

        closest_li.before(charter);
        file_kendo_init();

        $(this).parent().remove();
    });
}

function update_document(doc_id, doc_type){
    var item = $('#item_' + doc_id);

    if (!item.next().is('.edit-uploader-block')) {
        item.wrap('<div class="edit-block">');
        var charter = '<div class="edit-uploader-block"><label for="id_file">' + gettext('Edit Document') + '</label><input id="id_file" name="file" type="file"></div>';
        item.after(charter);
        file_kendo_init();
    }
}

function file_kendo_init() {
    $("input[type='file']").kendoUpload({
        localization: {
            "select": "Select file from your computer...",
            "dropFilesHere": "or drag & drop here to attach"
        },
        multiple: false,
        async: {
            saveUrl: "/documents/create/",
            autoUpload: true
        },
        complete: onComplete,
        error: onError,
        progress: onProgress,
        success: onSuccess,
        upload: onUpload,
        select: onSelect
    });
}

function onUpload(e) {
    var item_temp = $('#id_file');
    var committee = $('#committee_id').val();
    e.data = {'csrfmiddlewaretoken': csrftoken};

    if (item_temp.closest('.items').find('.edit-block').length) {
        var closest_edit_block_item = item_temp.closest('.items').find('.item');
        var document_id = closest_edit_block_item.find('.edit').attr('data-doc-id');
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
        e.data['action'] = 'update';
        e.data['committee'] = committee;
    }
}

function onSuccess(e) {
    console.log("Status: " + e.response.status);
    console.log("Object pk: " + e.response.pk);
    var uploaded = $("#id_uploaded_file");
    uploaded.val(e.response.pk);
    if (e.response.html) {
        var html = e.response.html;
        var item_temp = $('#id_file').closest('.edit-uploader-block');
        item_temp.before(html);
    }
}
