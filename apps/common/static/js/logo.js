function onSuccess(e) {
    console.log("Status: " + e.response.status);
    console.log("Object pk: " + e.response.pk);
    if (e.response.html) {
        var html = e.response.html;
        var type = e.response.type;
        var item_temp = $('#id_' + type).closest('.edit-uploader-block');
        item_temp.before(html);
    }
    var logo = $('#logo-img');
    if (logo.length){
        logo.attr('src', e.response.path);
    } else {
        $('#header h1').removeClass('logo').prepend('<img src="' + e.response.path + '" id="logo-img">');
    }

    $('.logo-preview img').attr('src', e.response.path);
    $('.logo-preview').show();
}

function update_document(doc_id, doc_type){
    var item = $('#item_' + doc_id);
    // remove previous uploader-blocks for documents
    var archives = item.closest('.archives');
    archives.find('.edit-block > .item').unwrap();
    archives.find('.edit-uploader-block').remove();
    if (!item.next().is('.edit-uploader-block')) {
        item.wrap('<div class="edit-block">');
        var logo_doc = '<div class="edit-uploader-block"><label for="id_logo">' + gettext('Edit Document') +
            '</label><input id="id_logo" name="logo" type="file"></div>';
        item.after(logo_doc);
        logo_kendo_init();
    }
}

function onLogoUpload(e) {
    var item_temp = $('#id_logo');
    e.data = {'csrfmiddlewaretoken': csrftoken, 'type': item_temp.attr('name')};
    upload(e, item_temp)
}

function upload(e, item_temp){
    var closest_edit_block_item = item_temp.closest('.edit-block').find('.item');
    var edit_item = closest_edit_block_item.find('.edit');
    var download_item = closest_edit_block_item.find('.download');
    var document_id = edit_item.attr('data-doc-id') || download_item.attr('data-doc-id');
    e.data['meeting'] = edit_item.attr('data-doc-meeting') || download_item.attr('data-doc-meeting');
    closest_edit_block_item.remove();
}

function delete_document(data){
    $('#item_' + data.doc_id).fadeOut(500, function(){
        var charter = '<li><input id="id_logo" name="logo" type="file"></li>';
        var closest_li = $(this).parent();

        closest_li.before(charter);
        logo_kendo_init();
        $(this).parent().remove();
        var logo = $('#logo-img');
        logo.remove();
        $('#header h1').addClass('logo');
    });
}

function onSelectImg(e) {
    var allowed_ext = [".png", ".jpg", ".jpeg", ".gif"];
    var warning = false;
    $.each(e.files, function(index, value) {
        if(jQuery.inArray(value.extension.toLowerCase(), allowed_ext) == '-1') {
            e.preventDefault();
            warning = true;
        }
    });
    var message = '<p>' + gettext('You can only upload following files: ' +
        'png, jpg, jpeg, gif".</p><p>Try to upload the correct file type.') +
        '</p>' + '<div class="warning-buttons">' +
        '<button class="warning-confirm k-button">' + gettext("Ok") + '</button>' +
        '</div>';
    getWarning(warning, message);
}

function logo_kendo_init() {
    $("#id_logo").kendoUpload({
        localization: {
            "select": "Select files from your computer...",
            "dropFilesHere": "or drag & drop here to attach"
        },
        multiple: true,
        async: {
            saveUrl: $('#logo-form').attr('action'),
            autoUpload: true
        },
        complete: onComplete,
        error: onError,
        progress: onProgress,
        success: onSuccess,
        upload: onLogoUpload,
        select: onSelectImg
    });
}

jQuery(document).ready(function($) {
    logo_kendo_init();
});