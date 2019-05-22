jQuery(document).ready(function($) {
    board_book_kendo_init();
    agenda_kendo_init();
    minutes_kendo_init();
    other_docs_kendo_init();
    key_file_kendo_init();
});

function onKeyFileUpload(e) {
    var item_temp = $('#id_file');
    e.data = {'csrfmiddlewaretoken': csrftoken, 'type': item_temp.attr('name')};
}

function onSuccessFile(e) {
    console.log("Status: " + e.response.status);
    console.log("Object pk: " + e.response.pk);
    add_to_uploaded_file(e.response.pk);
    if (e.response.html) {
        var html = e.response.html;
        var type = e.response.type;
        if (type == 'other') type = 'temp_doc';
        var item_temp = $('#id_' + type).closest('.edit-uploader-block');
        item_temp.before(html);
    }
}

function add_to_uploaded_file(pk) {
    var uploaded = $("#id_uploaded_file");
    var value = uploaded.val();
    if (value) value += ',';
    uploaded.val(value + pk);
}
