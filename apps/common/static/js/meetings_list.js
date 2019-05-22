$(document).ready(function () {

    $('.selectize-it').selectize({ dropdownParent: 'body' });
    $('#meeting-filter').change(function () { init_loaders(api_meetings_list, true); });
    $('div.waiting-modal').remove();

    var meetings_up = {
        'holder': $('#upcoming-meetings-holder'),
        'listing': $('#upcoming-meetings-holder .listing'),
        'loader': $('#upcoming-meetings-holder .loader'),
        'next_page': null
    };

    var meetings_past = {
        'holder': $('#past-meetings-holder'),
        'listing': $('#past-meetings-holder .listing'),
        'loader': $('#past-meetings-holder .loader'),
        'next_page': null
    };

    function load_meetings(meetingset) {

        if (meetingset['next_page']) {
            $.ajax({
                url: meetingset['next_page'],
                datatype: 'json',
                method: "GET",
                success: function (rsp) { put_meetings_on_page(rsp, meetingset); },
                error: function (rsp) { console.log(rsp); }
            });
        }

        meetingset['next_page'] = null;

    }


    function put_meetings_on_page(rsp, meetingset) {

        if (!rsp.next) {
            meetingset.loader.hide();
        }

        meetingset.next_page = rsp.next;
        var container = meetingset.listing;

        for (var i = 0; i < rsp.results.length; i++) {
            var meet = rsp.results[i];
            var card = make_card(meet, true);
            container.append(card);
        }

        if (!rsp.previous_page && rsp.results.length == 0) {
            container.append("<p class='empty'>nothing found</p>");
        }

    }

    function make_card(m, add_clicker) {

        var attendees = "";

        var icon_class = (is_events_list) ? 'event-icon' : '';
        var card = '<div class="dashboard-meeting-card" data-id="' + m.id + '">';

        card += '<div class="meeting-icon ' + icon_class + '">' +
            '<div class="month">' + m.date_formatted[2] + '.</div>' +
            '<div class="day">' + m.date_formatted[1] + '</div></div>';

        card += '<div class="meeting-description">';
        card += '<h3><a href="' + m.id + '">' + m.name + '</a></h3>';
        card += '<p><b>Attendees:</b>' + (m.committee_name ? m.committee_name : 'All Board Members') + '</p>';
        card += '<p><b>Date:</b>' + m.date_formatted[0] + '</p>';
        card += '<p><b>Time:</b>' + m.time_formatted + '</p>';

        if (m.location) {
            card += '<p><b>Address:</b>' + m.location + '</p>';
        }

        card += '</div></div>'; // meeting-description, dashboard-meeting-card

        qcard = $(card);

        if (add_clicker) {
            var m_url = url_meetings_list + m.id;
            qcard.click(function (e) { window.location = m_url; });
        }

        return qcard;

    }


    function init_loaders(base_url, use_filters) {

        var up_url = base_url;
        var past_url = base_url + "?past=1";

        var qs = {};

        if (is_events_list) {
            qs['event'] = '1';
        }

        if (use_filters) {

            var order_by = $('select#id_order_by').val();
            if (order_by) {
                qs['order_by'] = order_by;
            }
            var committee = $('select#id_committee').val();
            if (committee) {
                qs['committee'] = committee;
            }
            var qss = jQuery.param(qs);

            var up_url = base_url + "?" + jQuery.param(qs);
            var past_url = base_url + "?past=1&" + jQuery.param(qs);

        }

        var query_string = jQuery.param(qs);

        if (query_string.length > 0) {
            up_url = up_url + "?" + query_string;
            past_url = past_url + "&" + query_string;
        }

        meetings_up['next_page'] = up_url;
        meetings_past['next_page'] = past_url;

        meetings_up['listing'].empty();
        meetings_past['listing'].empty();

        meetings_up['loader'].show();
        meetings_past['loader'].show();

        $(window).scroll(check_loaders).resize(check_loaders);
        $('.meetings-meetings .loader').click(check_loaders);
        check_loaders();
    }

    function check_loaders() {

        // check if loader div is visible and call the handler

        var win_top = $(window).scrollTop();
        var win_bot = win_top + $(window).height();
        var up_top = $(meetings_up['loader']).offset().top;
        var past_top = $(meetings_past['loader']).offset().top;

        // 'up' loader is visible 
        if (up_top > win_top && up_top < win_bot && meetings_up['next_page'] !== null) {
            load_meetings(meetings_up);
            // possible optimization: skip loading past meetings if upcoming was updated
            // return;
        }

        // 'past' loader is visible
        if (past_top > win_top && past_top < win_bot && meetings_past['next_page'] !== null) {
            load_meetings(meetings_past);
        }
    }

    // 
    init_loaders(api_meetings_list);

});
