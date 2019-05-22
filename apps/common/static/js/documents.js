jQuery(document).ready(function($) {
    $(document).on('click', '.edit', function (event) {
        event.preventDefault();
        var doc_id = $(this).attr('data-doc-id');
        var doc_type = $(this).attr('data-doc-type');
        update_document(doc_id, doc_type);
    });

    $(document).on('click', '.delete', function (event) {
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
            .content($("#delete-confirmation").html())
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
                            delete_document(response);
                        }
                    });
                }
                kendoWindow.data("kendoWindow").close();
            })
            .end();
    });

    $(document).on('click', '.update', function (event) {
        event.preventDefault();
        var document_id = $(this).attr('data-doc-id');
        var document_type = $(this).attr('data-doc-type');
        var filename = $(this).parent('[id*="tabs"]').children('input[name*=filename]').val();

        var kendoWindow = $("<div />").kendoWindow({
            title: gettext('Confirm'),
            resizable: false,
            modal: true,
            height: "110px",
            width: "220px",
            visible: false
        });

        kendoWindow.data("kendoWindow")
            .content($("#update-confirmation").html())
            .center().open();

        kendoWindow
            .find(".update-confirm,.update-cancel")
            .click(function(e) {
                e.preventDefault();
                if ($(this).hasClass("update-confirm")) {
                    var request = $.ajax({
                        url: DOC_RENAME_URL,
                        type: "POST",
                        data: {
                            document_id: document_id,
                            filename: filename
                        },
                        success: function(response) {
                            update_document(document_id, document_type);
                        }
                    });
                }
                kendoWindow.data("kendoWindow").close();
            })
            .end();
    });
});

function edit_doc_tabs_kendo_init(id) {
    $("#" + id).kendoTabStrip({
        animation:  {
            open: {
                effects: "fadeIn"
            }
        }
    });
}

function agenda_kendo_init() {
    edit_doc_tabs_kendo_init('id_agenda_tabs');

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

function board_book_kendo_init() {
    edit_doc_tabs_kendo_init('id_board_book_tabs');

    $("#id_board_book").kendoUpload({
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
        upload: onBoardBookUpload,
        select: onSelect
    });
}
function key_file_kendo_init() {
    $("#id_file").kendoUpload({
        localization: {
            "select": "Select file from your computer...",
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
        success: onSuccessFile,
        upload: onKeyFileUpload,
        select: onSelect
    });
}
function minutes_kendo_init() {
    edit_doc_tabs_kendo_init('id_minutes_tabs');

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
    edit_doc_tabs_kendo_init('id_temp_doc_tabs');

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
    console.log("Upload progress :: " + e.percentComplete + "% :: " + getFileInfo(e));
    $('.create-committee').attr("disabled", "disabled");
}

function onError(e) {
    console.log("Error (" + e.operation + ") :: " + getFileInfo(e));
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
    var allowed_ext = [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".ppt", ".pptx", ".gif", ".zip", ".mp3", ".ods", ".odt", ".odp"];
    var warning = false;
    $.each(e.files, function(index, value) {
        if(jQuery.inArray(value.extension.toLowerCase(), allowed_ext) == '-1') {
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
            height: "160px",
            width: "360px",
            visible: false
        });
        if (!message){
            message = '<p>' + gettext('You can only upload following files: ' +
                'pdf, doc, docx, xls, xlsx, png, jpg, jpeg, tif, tiff, ppt, pptx, gif, zip, mp3, odt, ods, odp. </p><p>Try to upload the correct file type.') +
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
