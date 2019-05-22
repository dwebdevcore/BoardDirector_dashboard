$(document).ready(function () {
    var is_guest;

    if (typeof (IS_GUEST) === "undefined") {
        is_guest = false;
    } else {
        is_guest = IS_GUEST;
    }

    $('#avatar').hover(
        function () {
            var img_field = $("input[name='avatar']");
            if ((img_field.val().length || img_field.data('img'))) {
                var x1 = 10;
                var y1 = 10;
                var x2 = 230;
                var y2 = 150;
                var orig_w = $(this).attr('data-crop-orig-w');

                if (typeof orig_w !== 'undefined' && orig_w !== '') {
                    var x = $(this).attr('data-crop-x');
                    var y = $(this).attr('data-crop-y');
                    var w = $(this).attr('data-crop-w');
                    var h = $(this).attr('data-crop-h');
                    var scale = orig_w / 240;
                    x1 = x / scale;
                    y1 = y / scale;
                    x2 = x1 + w / scale;
                    y2 = y1 + h / scale;
                }

                $(this).imgAreaSelect({
                    x1: x1,
                    y1: y1,
                    x2: x2,
                    y2: y2,
                    aspectRatio: '1:1',
                    handles: true,
                    onSelectEnd: function (img, selection) {
                        $('input[name="x1"]').val(selection.x1);
                        $('input[name="y1"]').val(selection.y1);
                        $('input[name="x2"]').val(selection.x2);
                        $('input[name="y2"]').val(selection.y2);
                    }
                });
                $('.add-thumb').show();
            }
        }
    );

    $('.add-thumb, .add-thumb a').on("click", function (event) {
        event.preventDefault();
        $('.addmember-form').submit();
    });

    $(".kendo_editor").kendoEditor({ encoded: false });

    $('.avatar-input').on('change', function () {
        var name = $(this).val().split('\\').pop();
        $(this).closest('div').find('a').text(name);
    });

    $(".multiple").each(function (index) {
        $(this).selectize({
            plugins: ['remove_button'],
            dropdownParent: 'body'
        });
    });

    $("#id_date_joined_board, #id_term_start, #id_term_expires").kendoDatePicker({
        format: "MMM. dd, yyyy"
    });

    $('.upload-link, .add-pic').click(function (event) {
        event.preventDefault();
        $('.avatar-input').trigger('click');
    });

    $("input[name='avatar']").change(function () {
        if (this.files && this.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
                $('#avatar').attr('src', e.target.result);
            };

            reader.readAsDataURL(this.files[0]);
        }
    });

    $(".btn.add-another").click(function () {
        $('#id_add_another').val('True');
    });

    var $is_current_profile = $('#current_user_profile_header');

    // show some extra warnings when user try to disable his own profile
    if (CURRENT_PROFILE) {

        // active -> inactive
        $('#id_is_active').change(function (event) {
            if ($(this).val() != 'True') {
                event.preventDefault();
                $('.popup-overlay').show();
                inactive_admin_dialog.dialog('open');
            }
        });

        // admin -> not-admin
        $('#id_is_admin').change(function (event) {
            if (!$(this).is(":checked")) {
                event.preventDefault();
                $('.popup-overlay').show();
                stop_admin_dialog.dialog('open');
            }
        });

    }

    // autocomplete combobox for "role"
    var default_roles = [];
    $('#select-role-box').find("option").each(function () {
        default_roles.push($(this).attr("value"));
    });

    $('#create_crole').click(jqui_input_crole);

    function jqui_input_crole(event) {
        event.preventDefault();
        $('#create_crole').blur();
        $('.popup-overlay').show();
        crole_dialog.dialog("open");
    }

    var crole_dialog = $("#create_crole_popup").dialog({
        autoOpen: false,
        width: 600,
        modal: false,
        resizable: false,
        buttons: [
            {
                text: "Create",
                click: function () {
                    $('.popup-overlay').hide();
                    crole_dialog.dialog("close");
                    var txt = $('#crole_input').val();
                    if (txt && txt.length > 0) {
                        $('#edit-role-box').val(txt);
                    }
                    $('#crole_input').val("");
                }
            },
            {
                text: "Cancel", class: 'cancel-button',
                click: function () { $('.popup-overlay').hide(); crole_dialog.dialog("close"); }
            }
        ],

        beforeClose: function (event, ui) {
            $('.popup-overlay').hide();
        }
    });

    var inactive_admin_dialog = $("#confirm-inactive-admin").dialog({
        autoOpen: false,
        width: 720,
        modal: true,
        resizable: false,
        buttons: [
            {
                text: "Yes, change", 
                click: function () { 
                    $(this).dialog("close");
                }
            },
            {
                text: "No, revert",
                click: function () {
                    selectMe('id_is_active', 0, 2);
                    $(this).dialog("close");
                }
            }
        ],

        beforeClose: function (event, ui) {
            $('.popup-overlay').hide();
        },
    });


    var stop_admin_dialog = $("#confirm-stop-admin").dialog({
        autoOpen: false,
        width: 720,
        modal: true,
        resizable: false,
        buttons: [
            {
                text: "Yes, change", 
                click: function () { 
                    $(this).dialog("close");
                }
            },
            {
                text: "No, revert",
                click: function () {
                    $('#id_is_admin').prop('checked', true).change();
                    $(this).dialog("close");
                }
            }
        ],

        beforeClose: function (event, ui) {
            $('.popup-overlay').hide();
        },
    });

    if (is_guest) {
        if ($('#edit-role-box').val() == 'Staff') {
            $('.choose-admin').css('display', 'inline-block');
        } else {
            $('.choose-admin').css('display', 'none');
            if ($('#id_is_admin').is(":checked")) {
                $('#id_is_admin').prop('checked', false).trigger("change");
            }
        }
    }

    $('#select-role-box').change(function () {

        $("#edit-role-box").val($("#select-role-box option:selected").html());

        if (is_guest) {
            if ($(this).val() == 'Staff') {
                $('.choose-admin').css('display', 'inline-block');
            } else {
                $('.choose-admin').css('display', 'none');
                if ($('#id_is_admin').is(":checked")) {
                    $('#id_is_admin').prop('checked', false).trigger("change");
                }
            }
        }
    });

    $('#edit-role-box').autocomplete({
        source: default_roles
    });

});
