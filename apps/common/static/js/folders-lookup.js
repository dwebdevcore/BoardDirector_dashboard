(function () {
    var folder_lookup;

    function show_move_folder_modal(init_params, current_ids) {
        var $modal = $('#move-folder-dialog');
        $modal.dialog('open');
        $('.popup-overlay').show();

        var $target_element = $modal.find('.lookup-folder-children-target');
        if ($target_element.jstree()) {
            $target_element.jstree('destroy');
        }

        var $send_button = $modal.parents('.ui-dialog').find('.form-send-button');
        $send_button.button('disable');

        $target_element.jstree({
            core: {
                data: function (node, callback) {
                    if (node.id === '#') {
                        folder_lookup.init(init_params).then(callback);
                        // QUESTION: Is there a global ajax error handler?
                    } else {
                        folder_lookup.lookup(node.id).then(callback);
                    }
                }
            }
        }).on('select_node.jstree', function (event, data) {
            $send_button.button('option', 'disabled', !data.node.id || current_ids.indexOf(data.node.id) != -1);
        });
    }

    function create_folder_lookup(url) {
        return {
            lookup: function (slug) {
                return $.ajax({
                    url: url,
                    data: {document_slug: slug}
                });
            },
            init: function (init_params) {
                return $.ajax({
                    url: url,
                    data: init_params
                });
            }
        }
    }

    // Initialize
    $(function ($) {
        var $select_document_dialog = $('#move-folder-dialog');
        var make_url_fn;
        $select_document_dialog.dialog({
            autoOpen: false,
            width: 696,
            resizable: false,
            buttons: [
                {
                    text: $select_document_dialog.attr('data-cancel-button-text'),
                    click: function () {
                        $(this).dialog('close');
                        $('.popup-overlay').hide();
                    },
                    class: 'cancel-button'
                },
                {
                    text: 'To be replaced on show',
                    click: function () {
                        var target_slug = $select_document_dialog.find('.lookup-folder-children-target').jstree().get_selected();
                        $.ajax({
                            url: make_url_fn(),
                            type: 'POST',
                            data: {
                                target_slug: target_slug[0]
                            }
                        }).then(function () {
                            $select_document_dialog.dialog('close');
                            $('.popup-overlay').hide();
                            location.reload();
                        });
                    },
                    disabled: true,
                    class: 'form-send-button'
                }
            ],
            beforeClose: function (event, ui) {
                $('.popup-overlay').hide();
            }
        });

        folder_lookup = create_folder_lookup($('#folder-lookup-url').val());

        $('.move-folder-link').click(function () {
            var folder_slug = $(this).attr('data-folder-slug');
            var parent_slug = $('#current-folder-slug').val();

            // Setup for folder
            $select_document_dialog.dialog('option', 'title', $select_document_dialog.attr('data-move-folder-title'));
            $select_document_dialog.parents('.ui-dialog').find('.form-send-button').text($select_document_dialog.attr('data-send-button-text-folder'));
            make_url_fn = function() {
                return $select_document_dialog.attr('data-move-folder-url').replace('SLUGTEMPLATE', folder_slug);
            };

            show_move_folder_modal({init_for_folder: folder_slug}, [folder_slug, parent_slug]);
        });

        $('.move-document-link').click(function () {
            var document_id = $(this).attr('data-doc-id');
            var parent_slug = $('#current-folder-slug').val();

            // Setup for document
            $select_document_dialog.dialog('option', 'title', $select_document_dialog.attr('data-move-document-title'));
            $select_document_dialog.parents('.ui-dialog').find('.form-send-button').text($select_document_dialog.attr('data-send-button-text-document'));
            make_url_fn = function() {
                return $select_document_dialog.attr('data-move-document-url').replace('000000000', document_id);
            };

            show_move_folder_modal({init_for_document: document_id}, ['doc-' + document_id, parent_slug]);
        });
    })
})();