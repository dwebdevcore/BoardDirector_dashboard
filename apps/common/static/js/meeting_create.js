jQuery(document).ready(function ($) {

    function startChange() {
        var startTime = start.value();

        if (startTime) {
            startTime = new Date(startTime);
            startTime.setMinutes(startTime.getMinutes() + this.options.interval);
            end.min(startTime);
            end.value(startTime);
        }
    }

    //init start timepicker
    var time_start = $("#id_time_start");
    if (!time_start.val())
        time_start.val('8:00 AM');
    var start = time_start.kendoTimePicker({
        change: startChange,
        format: "h:mm tt",
        parseFormats: ["HH:mm"]
    }).data("kendoTimePicker");

    //init end timepicker
    var time_end = $("#id_time_end");
    if (!time_end.val())
        time_end.val('10:00 AM');
    var end = time_end.kendoTimePicker({
        format: "h:mm tt",
        parseFormats: ["HH:mm"]
    }).data("kendoTimePicker");

    //define min/max range
    start.min("6:00 AM");
    start.max("10:00 PM");

    //define min/max range
    end.min("6:00 AM");
    end.max("10:00 PM");

    $("#id_date").kendoDatePicker({
        format: "MMM. dd, yyyy"
    });

    board_book_kendo_init();
    agenda_kendo_init();
    minutes_kendo_init();
    other_docs_kendo_init();

    $('#id_extra_members').selectize({
        plugins: ['remove_button'],
        dropdownParent: 'body'
    });

    var top_locations = [];
    $('#select-location-box').find("option").each(function () {
        top_locations.push($(this).attr("value"));
    });

    $('#edit-location-box').autocomplete({ source: top_locations });

    $('#select-location-box').change(function () {
        $("#edit-location-box").val($("#select-location-box option:selected").html());
    });

    setup_repeat_type();

    $('.publish-meeting').click(function () {
        $('#action-hidden-field').val('publish');
    });

    $('.draft-meeting').click(function () {
        $('#action-hidden-field').val('update-no-email');
    });

    $(".right-side button[type='submit']").click(function () { $('.common-form').submit(); });

    // $(".right-side button[type='submit']").click(function () {
    //     var $prompt = $('#prompt-send-email');
    //     if ($prompt.length) {
    //         var kendoWindow = $("<div />").kendoWindow({
    //             title: gettext('Confirm'),
    //             resizable: false,
    //             modal: true,
    //             height: "110px",
    //             width: "210px",
    //             visible: false
    //         });

    //         kendoWindow.data("kendoWindow")
    //             .content($prompt.html())
    //             .center().open();

    //         kendoWindow
    //             .find("button")
    //             .click(function (e) {
    //                 e.preventDefault();
    //                 if ($(this).hasClass("skip-emails")) {
    //                     $('#action-hidden-field').val('update-no-email');
    //                 }
    //                 kendoWindow.data("kendoWindow").close();
    //                 $('.common-form').submit();
    //             })
    //             .end();
    //     } else {
    //         $('.common-form').submit();
    //     }
    // });
});

function setup_repeat_type() {
    $('#id_repeat_type').selectize({
        // dropdownParent: '.repeat-modal .modal-body'
    });

    $("#id_repeat_end_date").kendoDatePicker({
        format: "MMM. dd, yyyy"
    });

    $("input[name='repeat_end_type'][value='max_count']").click(function () {
        setTimeout(function () {
            $('#id_repeat_max_count').focus();
        }, 50);
    });

    $("input[name='repeat_end_type'][value='end_date']").click(function () {
        setTimeout(function () {
            $('#id_repeat_end_date').focus();
        }, 50);
    });

    var previous_state = {};

    $('#apply-repeat').click(apply_repeat);
    $('#cancel-repeat').click(function () {
        restore_repeat_state(previous_state);
        apply_repeat();
    });

    $('#repeat-checkbox').click(check_box_clicked);
    $('#repeat-change').click(check_box_clicked);
    $('#myCheckbox0').click(check_box_clicked); // Legacy fancy checkbox support

    // Initial value
    update_repeat_state();

    function check_box_clicked() {
        var repeat_type = $('#id_repeat_type');

        if ($('#repeat-checkbox').is(':checked')) {
            previous_state = collect_repeat_state();
            $('.repeat-modal')
                .modal({ backdrop: 'static', keyboard: false })
                .modal('show');
        } else {
            repeat_type[0].selectize.setValue("0");
            update_repeat_state();
        }
    }

    function apply_repeat() {
        // TODO: Client-side validation
        var repeat_type = 1 * $('#id_repeat_type').val();

        var checked, checkbox_class;
        if (repeat_type) {
            checked = 'checked';
            checkbox_class = 'checkboxAreaChecked';
        } else {
            checked = undefined;
            checkbox_class = 'checkboxArea';
        }

        $('#repeat-checkbox').attr('checked', checked);
        $('#myCheckbox0').attr('class', checkbox_class); // Overwrite full class

        update_repeat_state();

        $('.repeat-modal').modal('hide');
    }
}

var REPEAT_FIELDS = ['repeat_type', 'repeat_interval', 'repeat_end_date', 'repeat_max_count'];

function collect_repeat_state() {
    var state = {};
    $.each(REPEAT_FIELDS, function (i, field) {
        state[field] = $('#id_' + field).val();
    });

    state.repeat_end_type = $("input[name='repeat_end_type']:checked").val();
    return state;
}

function restore_repeat_state(state) {
    console.log(state);
    $.each(REPEAT_FIELDS, function (i, field) {
        $('#id_' + field).val(state[field]);
    });

    $('#id_repeat_type').get(0).selectize.setValue(state.repeat_type);  // requires special handling

    $("input[name='repeat_end_type']").each(function () {
        this.checked = false;
    });
    $("input[name='repeat_end_type'][value='" + state.repeat_end_type + "']").each(function () {
        this.checked = true;
    });
}


function update_repeat_state() {
    $('#repeat-string').text(make_repeat_string());
    $('#repeat-change')[$('#id_repeat_type').val() != 0 ? 'show' : 'hide']();
}

function make_repeat_string() {
    var repeat_type = 1 * $('#id_repeat_type').val();
    var repeat_interval = $('#id_repeat_interval').val();
    var repeat_max_count = 1 * $('#id_repeat_max_count').val();
    var repeat_end_date = $('#id_repeat_end_date').val();

    if (!repeat_type) {
        return '';
    }

    var repeat_str = window.repeat_type_choices[repeat_type];
    if (repeat_interval != 1) {
        repeat_str += ' (every ' + repeat_interval + ')';
    }
    if (repeat_max_count) {
        repeat_str += ' ' + repeat_max_count + ' repetitions';
    }
    if (repeat_end_date) {
        repeat_str += ' up to ' + repeat_end_date;
    }

    return repeat_str;
}