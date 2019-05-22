$(function () {
    new FileUploader($('input[type=file]'), {
        multiple: true,
        uploaded_file: '.create-document-form #id_uploaded_file',
        on_success: function (e) {
            $('.documents-upload-files').show();
            FileUploader.default_options.on_success.bind(this)(e);
        }
    });

    $('.documents-cancel-upload').click(function (e) {
        e.preventDefault();
        $('.create-document-form #id_uploaded_file').val('');
        $('.create-document-form .k-upload-files li').remove();
        $('.documents-upload-files').hide();
    });
})