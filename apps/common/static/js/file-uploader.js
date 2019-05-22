// Attempt to extract some reusable file upload. A lot of code is copied from other places.
// In best scenario other places should be rewritten to use this code as more customizable and less copy-pasted.
var FileUploader = (function () {
    function FileUploader($target, options) {
        options = $.extend({}, FileUploader.default_options, options);

        $target.kendoUpload({
            localization: {
                "select": options.select_text || "Select file from your computer...",
                "dropFilesHere": options.drop_files_here_text || "or drag & drop here to attach"
            },
            multiple: !!options.multiple,
            async: {
                saveUrl: "/documents/create/",
                autoUpload: true
            },
            complete: options.on_complete.bind(options),
            error: options.on_error.bind(options),
            progress: options.on_progress.bind(options),
            success: options.on_success.bind(options),
            upload: options.on_upload.bind(options),
            select: options.on_select.bind(options),
        });
    }

    FileUploader.default_options = {
        allowed_ext: [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".ppt", ".pptx", ".gif", ".zip", ".mp3", ".ods", ".odt", ".odp"],
        submit_button: null, // This button will be disabled/enabled while uploading
        uploaded_file: '#id_uploaded_file', // Selector for uploaded file
        multiple: false,
        on_upload: function (e) {
            e.data = this.upload_data || {};
            e.data.csrfmiddlewaretoken = csrftoken;
        },
        on_select: function (e) {
            var that = this;
            $.each(e.files, function (index, value) {
                if (jQuery.inArray(value.extension, that.allowed_ext) === -1) {
                    e.preventDefault();
                    this.get_warning('');
                }
            });
        },
        on_progress: function (e) {
            console.log("Upload progress :: " + e.percentComplete + "% :: " + getFileInfo(e));
            if (this.submit_button) {
                $(this.submit_button).attr("disabled", "disabled");
            }
        },
        on_complete: function (e) {
            if (this.submit_button) {
                $(this.submit_button).removeAttr("disabled");
            }
        },
        on_success: function (e) {
            console.log("Status: ", e.response.status, ", Object pk: ", e.response.pk);

            if (this.uploaded_file && $(this.uploaded_file).length) {
                var uploaded = $(this.uploaded_file);
                var value = uploaded.val();
                if (value) value += ',';
                uploaded.val(value + e.response.pk);
            } else {
                console.log("No uploaded_file option specified, or it's target isn't found.", this.uploaded_file);
            }

            if (e.response.html) {
                this.update_html(e, e.response.html, e.response.type);
            }
        },
        update_html: function (e, html, type) {
            if (type === 'other') type = 'temp_doc';
            var item_temp = $('#id_' + type).closest('.edit-uploader-block');
            item_temp.before(html);
        },
        on_error: function (e) {
            console.log("Error (" + e.operation + ") :: " + getFileInfo(e));
            var http_request = jQuery.parseJSON(e.XMLHttpRequest.response);
            if (e.XMLHttpRequest.status === 403 && http_request.status === 'error') {
                var kendoWindow = $("<div />").kendoWindow({
                    title: gettext('Warning!'),
                    resizable: false,
                    modal: true,
                    height: "100px",
                    width: "270px",
                    visible: false
                });
                var message =
                    '<p>' + http_request.message + '</p>'
                    + '<div class="warning-buttons">'
                    + '     <button class="warning-confirm k-button">' + gettext("Ok") + '</button>'
                    + '</div>';
                kendoWindow.data("kendoWindow").content(message).center().open();

                kendoWindow
                    .find(".warning-confirm")
                    .click(function (e) {
                        e.preventDefault();
                        kendoWindow.data("kendoWindow").close();
                    })
                    .end();
            }
        },

        get_warning: function (message) {
            var kendoWindow = $("<div />").kendoWindow({
                title: gettext('Warning!'),
                resizable: false,
                modal: true,
                height: "150px",
                width: "360px",
                visible: false
            });
            if (!message) {
                message =
                    '<p>' + gettext('You can only upload following files: ' + this.allowed_ext.join(',') + '.</p>' +
                        '<p>Try to upload the correct file type.') + '</p>' +
                    '<div class="warning-buttons">' +
                    '   <button class="warning-confirm k-button">' + gettext("Ok") + '</button>' +
                    '</div>';
            }
            kendoWindow.data("kendoWindow").content(message).center().open();
            kendoWindow
                .find(".warning-confirm")
                .click(function (e) {
                    e.preventDefault();
                    kendoWindow.data("kendoWindow").close();
                })
                .end();
        }
    }

    function getFileInfo(e) {
        return $.map(e.files, function (file) {
            var info = file.name;

            // File size is not available in all browsers
            if (file.size > 0) {
                info += " (" + Math.ceil(file.size / 1024) + " KB)";
            }
            return info;
        }).join(", ");
    }

    return FileUploader;
})();