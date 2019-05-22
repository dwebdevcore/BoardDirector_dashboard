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
    // console.log("Status: " + e.response.status);
    // console.log("Object pk: " + e.response.pk);
    add_to_uploaded(e.response.pk);
    if (e.response.html) {
        var html = e.response.html;
        var type = e.response.type;
        if (type == 'other') type = 'temp_doc';
        var item_temp = $('#id_' + type).closest('.edit-uploader-block');
        item_temp.before(html);
    }
}

function add_to_uploaded(pk) {
    var uploaded = $("#id_uploaded_file");
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


function upload_from_popup(e, item_temp){
    var document_id = item_temp.attr('data-doc-id');
    e.data['meeting'] = item_temp.attr('data-doc-meeting');
    var request = $.ajax({
        url: DOC_DELETE_URL,
        type: "POST",
        data: {
            document_id: document_id,
            action: 'update'
        },
        success: function(response) {
            var item_id = '#item' + document_id;
            $(item_id).remove();
            location.reload();
        }
    });
}

function rename_from_popup(e, item_temp){
    var document_id = item_temp.attr('data-doc-id');
    var filename = item_temp.val();
    var request = $.ajax({
        url: DOC_RENAME_URL,
        type: "POST",
        data: {
            document_id: document_id,
            filename: filename
        },
        success: function(response) {
            var item_id = '#item' + document_id;
            $(item_id).remove();
            location.reload();
        }
    });
}

jQuery(document).ready(function($) {
    var $folder_items = $('.folder-items');
    // console.log($folder_items);
    $folder_items.on('click', '.edit', function (event) {
        event.preventDefault();
        var doc_id = $(this).attr('data-doc-id');
        var doc_type = $(this).attr('data-doc-type');
        update_document(doc_id, doc_type);
    });

    $folder_items.on('click', '.edit-in-popup', function (event) {
        event.preventDefault();
        var doc_id = $(this).attr('data-doc-id');
        var doc_type = $(this).attr('data-doc-type');
        var doc_meeting_id = $(this).attr('data-doc-meeting');
        var filename = $(this).attr('data-doc-filename');
        init_update_modal(doc_id, doc_type, doc_meeting_id, filename);
    });

    $folder_items.on('click', '.rename-in-popup', function (event) {
        event.preventDefault();
        var doc_id = $(this).attr('data-doc-id');
        init_rename_modal(doc_id);
    });

    $folder_items.on('click', '.delete-doc-link', function (event) {
        event.preventDefault();
        var document_id = $(this).attr('data-doc-id');

        var kendoWindow = $("<div />").kendoWindow({
            title: gettext('Confirm'),
            resizable: false,
            modal: true,
            height: "110px",
            width: "220px",
            visible: false
        });

        kendoWindow.data("kendoWindow")
            .content($("#delete-document-confirmation").html())
            .center().open();

        kendoWindow
            .find(".delete-confirm,.delete-cancel")
            .click(function(e) {
                e.preventDefault();
                if ($(this).hasClass("delete-confirm")) {
                    var request = $.ajax({
                        url: DOC_DELETE_URL,
                        type: "POST",
                        data: {
                            document_id: document_id
                        },
                        success: function(response) {
                            location.reload();
                        }
                    });
                }
                kendoWindow.data("kendoWindow").close();
            })
            .end();
    });
});

function agenda_kendo_init() {
    $("#id_agenda").kendoUpload({
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
        upload: onAgendaUpload,
        select: onSelect
    });
}
function key_file_kendo_init() {
    $("#id_file").kendoUpload({
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
        success: onSuccessFile,
        upload: onKeyFileUpload,
        select: onSelect
    });
}
function minutes_kendo_init() {
    $("#id_minutes").kendoUpload({
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
        upload: onMinutesUpload,
        select: onSelect
    });
}
function other_docs_kendo_init() {
    $("#id_other").kendoUpload({
        localization: {
            "select": "Select files from your computer...",
            "dropFilesHere": "or drag & drop here to attach"
        },
        multiple: true,
        async: {
            saveUrl: "/documents/create/",
            autoUpload: true
        },
        complete: onComplete,
        error: onError,
        progress: onProgress,
        success: onSuccess,
        upload: onDocsUpload,
        select: onSelect
    });
}
function temp_doc_kendo_init() {
    $("#id_temp_doc").kendoUpload({
        localization: {
            "select": "Select file from your computer...",
            "dropFilesHere": "or drag & drop here to edit"
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
        upload: onTempDocsUpload,
        select: onSelect
    });
}

function onProgress(e) {
    // console.log("Upload progress :: " + e.percentComplete + "% :: " + getFileInfo(e));
    $('.create-committee').attr("disabled", "disabled");
}

function onError(e) {
    // console.log("Error (" + e.operation + ") :: " + getFileInfo(e));
    var http_request = jQuery.parseJSON(e.XMLHttpRequest.response);
    if (e.XMLHttpRequest.status == '403' && http_request.status == 'error') {

        var kendoWindow = $("<div />").kendoWindow({
            title: gettext('Warning!'),
            resizable: false,
            modal: true,
            height: "100px",
            width: "270px",
            visible: false
        });
        var message = '<p>' + http_request.message +
            '</p>' + '<div class="warning-buttons">' +
            '<button class="warning-confirm k-button">' + gettext("Ok") + '</button>' +
            '</div>';
        kendoWindow.data("kendoWindow").content(message).center().open();

        kendoWindow
            .find(".warning-confirm")
            .click(function(e) {
                e.preventDefault();
                kendoWindow.data("kendoWindow").close();
            })
            .end();
    }
}

function onComplete(e) {
    $('.create-committee').removeAttr("disabled");
}

function getFileInfo(e) {
    return $.map(e.files, function(file) {
        var info = file.name;

        // File size is not available in all browsers
        if (file.size > 0) {
            info  += " (" + Math.ceil(file.size / 1024) + " KB)";
        }
        return info;
    }).join(", ");
}

function onSelect(e) {
    var allowed_ext = [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".ppt", ".pptx", ".gif", ".zip", ".mp3"];
    var warning = false;
    $.each(e.files, function(index, value) {
        if(jQuery.inArray(value.extension, allowed_ext) == '-1') {
            e.preventDefault();
            warning = true;
        }
    });
    getWarning(warning, '');
}

function getWarning(warning, message){
    if (warning) {
        var kendoWindow = $("<div />").kendoWindow({
            title: gettext('Warning!'),
            resizable: false,
            modal: true,
            height: "120px",
            width: "300px",
            visible: false
        });
        if (!message){
            message = '<p>' + gettext('You can only upload following files: ' +
                'pdf, doc, docx, xls, xlsx, png, jpg, jpeg, tif, tiff, ppt, pptx, gif, zip, mp3".</p><p>Try to upload the correct file type.') +
                '</p>' + '<div class="warning-buttons">' +
                '<button class="warning-confirm k-button">' + gettext("Ok") + '</button>' +
                '</div>';
        }
        kendoWindow.data("kendoWindow").content(message).center().open();
        kendoWindow
            .find(".warning-confirm")
            .click(function(e) {
                e.preventDefault();
                kendoWindow.data("kendoWindow").close();
            })
            .end();
    }
}


function onSuccess(e) {
    // console.log("Status: " + e.response.status);
    // console.log("Object pk: " + e.response.pk);
    add_to_uploaded(e.response.pk);
    if (e.response.html) {
        var html = e.response.html;
        var type = e.response.type;
        if (type == 'other') type = 'temp_doc';
        var item_temp = $('#' + $(this.element).attr('id')).closest('.edit-uploader-block');
        item_temp.before(html);
    }
}

function onTempDocsUpload(e) {
    var item_temp = $(this.element);
    var closest_edit_block_item = item_temp.closest('.edit-block').find('.item');
    var edit_item = closest_edit_block_item.find('.edit');
    var download_item = closest_edit_block_item.find('.download');
    var document_id = edit_item.attr('data-doc-id') || download_item.attr('data-doc-id');
    e.data = {'csrfmiddlewaretoken': csrftoken, 'action': 'update', 'type': item_temp.attr('name'), 'old_document': document_id};
    upload(e, item_temp)
}

function delete_document(data){
    $('#item_' + data.doc_id).parents('li').fadeOut(500, function(){
        var closest_li = $(this).closest('.archives').parent();
        if ($(this).parent().children('.edit-uploader-block').length) $(this).parents('li').remove();
        else $(this).remove();
    });
}

function update_document(doc_id, doc_type){
    var item = $('#item_' + doc_id);
    if (!item.next().is('.edit-uploader-block')) {
        item.wrap('<div class="edit-block">');
        var temp_doc = '<div class="edit-uploader-block"><label for="id_temp_doc_' + doc_id + '">' + gettext('Edit Document') + '</label><input id="id_temp_doc_' + doc_id + '" name="file" type="file"></div>';
        item.after(temp_doc);
        temp_doc_kendo_init("#id_temp_doc_" + doc_id);
    }
}

function temp_doc_kendo_init(id) {
    var el = id || "#id_temp_doc";
    $(el).kendoUpload({
        localization: {
            "select": "Select file from your computer...",
            "dropFilesHere": "or drag & drop here to edit"
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
        upload: onTempDocsUpload,
        select: onSelect
    });
}

function init_update_modal(doc_id, doc_type, doc_meeting_id, filename){
    var $modal = $("#update-archive-dialog");
    $modal.dialog('open');
    $('.popup-overlay').show();
    var doc_meeting = '';
    if (doc_meeting_id) {
        doc_meeting = 'data-doc-meeting="' + doc_meeting_id + '"';
    }
    var $wrapper = $("#update-archive-file-wrapper");
    var temp_doc = '<input id="id_temp_doc_' + doc_id + '" name="file" type="file" data-doc-id="' + doc_id + '" ' + doc_meeting + '>';
    $('#doc-filename').html(filename);
    $wrapper.append(temp_doc);
    temp_doc_update_kendo_init("#id_temp_doc_" + doc_id);
}

function init_rename_modal(doc_id){
    var $modal = $("#rename-archive-dialog");
    $modal.dialog('open');
    $('.popup-overlay').show();
    var $wrapper = $("#rename-archive-file-wrapper");
    var temp_doc = '<div class="filename-form"><div class="form-group"><label>File Name:</label><input name="filename" type="text" data-doc-id="' + doc_id + '" /></div></div>';
    $wrapper.append(temp_doc);
}

function onSuccessUpdated(e) {
    window.eOnSuccess = e;
    if (e.response.html) {
        var html = e.response.html;
        var type = e.response.type;
        if (type == 'other') type = 'temp_doc';
        var item_temp = $('#' + $(this.element).attr('id')).closest('.edit-uploader-block');
        item_temp.before(html);
    }
}

function onTempDocsUpdateUpload(e) {
    var item_temp = $(this.element);
    var document_id = item_temp.attr('data-doc-id');
    e.data = {
        'csrfmiddlewaretoken': csrftoken,
        'action': 'update',
        'type': item_temp.attr('name'),
        'old_document': document_id
    };
    if (item_temp.attr('data-doc-meeting')) {
        e.data.meeting = item_temp.attr('data-doc-meeting');
    }
    window.eOnDocsUpdate = e;
    $(".form-send-button").prop("disabled", false).removeClass("ui-state-disabled");
}

function temp_doc_update_kendo_init(id, doc_id) {
    var el = id || "#id_temp_doc";
    $(el).kendoUpload({
        localization: {
            "select": "Select file...",
            "dropFilesHere": "Drop file here or click"
        },
        multiple: false,
        async: {
            saveUrl: "/documents/create/",
            autoUpload: true
        },
        complete: onComplete,
        error: onError,
        progress: onProgress,
        success: onSuccessUpdated,
        upload: onTempDocsUpdateUpload,
        select: onSelect
    });
}

function initUploadPopup() {

    var updDialog = $('#update-archive-dialog');
    updDialog.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        buttons: [
        {
            text: updDialog.attr('data-cancel-button-text'),
            click: function() {
                $( this ).dialog( "close" );
                $('.popup-overlay').hide();
            },
            class: 'cancel-button'
        },
        {
            text: updDialog.attr('data-send-button-text'),
            click: function() {
                var el = $("#update-archive-file-wrapper input");
                $("#id_notify_group").val($("#browse-by option:selected").val());
                $("#id_notify_me").val($("#notify_me").prop('checked'));
                upload_from_popup(window.eOnDocsUpdate, el);
                add_to_uploaded(window.eOnSuccess.response.pk);
                $( this ).dialog( "close" );
                $('.popup-overlay').hide();
            },
            class: 'form-send-button'
        }
        ],
        beforeClose: function( event, ui ) {
            $('.popup-overlay').hide();
            $('#update-archive-file-wrapper').empty();
        }
    });

    $(".form-send-button").prop("disabled", true).addClass("ui-state-disabled");

    $( "#browse-by" ).change(function () {
            $("#email-recipient").text($("#browse-by option:selected").text());
        })
        .change();
}

function initRenamePopup() {

    var updDialog = $('#rename-archive-dialog');
    updDialog.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        buttons: [
        {
            text: updDialog.attr('data-cancel-button-text'),
            click: function() {
                $( this ).dialog( "close" );
                $('.popup-overlay').hide();
            },
            class: 'cancel-button'
        },
        {
            text: updDialog.attr('data-send-button-text'),
            click: function() {
                var el = $("#rename-archive-file-wrapper input");
                rename_from_popup(window.eOnDocsUpdate, el);
                $( this ).dialog( "close" );
                $('.popup-overlay').hide();
            },
            class: 'form-send-button'
        }
        ],
        beforeClose: function( event, ui ) {
            $('.popup-overlay').hide();
            $('#rename-archive-file-wrapper').empty();
        }
    });
}

$(document).ready(function() {

    initUploadPopup();

    initRenamePopup();

    $( "li .items" ).hover(function() {
        $('.functional-btn').css("visibility", "hidden");
        $(this).find('.functional-btn').css("visibility", "visible");
    });
});
