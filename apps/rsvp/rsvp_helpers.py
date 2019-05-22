from rsvp.models import RsvpResponse


def fill_rsvp_responses(repetitions, user):
    meeting_ids = {r.meeting_id for r in repetitions}
    responses = RsvpResponse.objects.filter(meeting_id__in=meeting_ids, user=user).order_by('timestamp')
    default_responses = {r.meeting_id: r for r in responses if r.meeting_repetition_id is None}
    repetition_responses = {r.meeting_repetition_id: r for r in responses if r.meeting_repetition_id is not None}

    for rep in repetitions:
        resp = repetition_responses.get(rep.id)
        default_response = default_responses.get(rep.meeting_id)
        if not resp or (default_response and default_response.timestamp > resp.timestamp):
            resp = default_response
        rep.rsvp_response = resp.get_response_display() if resp else 'None'
        rep.rsvp_response_num = resp.response if resp else None
        rep.rsvp_accept_type = resp.accept_type if resp else 0
        rep.rsvp_note = resp.note if resp else ''
