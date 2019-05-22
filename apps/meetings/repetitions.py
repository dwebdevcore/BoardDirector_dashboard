from datetime import timedelta, date
from time import time

import logging
import pytz
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY, weekday
from django.conf import settings
from django.utils.timezone import is_aware, make_aware, get_current_timezone

MAX_YEARS = 5

logger = logging.getLogger(__name__)


def generate_repetition_dates(meeting, today=None, timezone=None):
    today = today or date.today()

    aware_start = meeting.start if is_aware(meeting.start) else make_aware(meeting.start)
    start = aware_start.astimezone(pytz.utc).date()
    local_start = aware_start.astimezone(timezone or pytz.timezone(settings.TIME_ZONE))

    if meeting.repeat_type == meeting.REPEAT_TYPES.once:
        it = iter([start])
    elif meeting.repeat_type == meeting.REPEAT_TYPES.every_day:
        it = every_day_generator(start, meeting.repeat_interval)
    elif meeting.repeat_type == meeting.REPEAT_TYPES.every_work_day:
        it = every_work_day_generator(start, meeting.repeat_interval)
    elif meeting.repeat_type == meeting.REPEAT_TYPES.every_week:
        it = every_week_generator(start, meeting.repeat_interval)
    elif meeting.repeat_type == meeting.REPEAT_TYPES.every_month:
        it = week_day_every_month_generator(start, meeting.repeat_interval, local_start)
    elif meeting.repeat_type == meeting.REPEAT_TYPES.every_year:
        it = every_year_generator(start, meeting.repeat_interval)
    else:
        raise ValueError("Unknown repeat_type %d" % (meeting.repeat_type,))

    end_date = meeting.repeat_end_date or (today + relativedelta(years=MAX_YEARS))
    n = 0
    max_count = meeting.repeat_max_count
    if max_count is not None and max_count < 1:
        max_count = 1  # at least 1 repetition always regardless of settings

    while True:
        dt = next(it)
        if dt > end_date:
            break
        if max_count is not None and n >= max_count:
            break

        yield dt
        n += 1

    # At least one date must be always emitted
    if n == 0:
        yield start


# Internal testable method (doesn't work with DB in any way)
def sync_meeting_repetitions_internal(meeting, existing_dates, today, timezone=None):
    # Local import to remove circular dependency with model module
    from meetings.models import MeetingRepetition

    existing_dates = set(existing_dates)
    create = []

    for dt in generate_repetition_dates(meeting, today, timezone):
        if dt in existing_dates:
            existing_dates.remove(dt)
        else:  # also all past meetings
            create.append(MeetingRepetition(meeting=meeting, date=dt))

    return create, existing_dates


def sync_meeting_repetitions(meeting, today=None):
    # Local import to remove circular dependency with model module
    from meetings.models import MeetingRepetition

    today = today or date.today()

    started = time()

    # safe bet - let's generate all the repetitions for now,
    # it can be tuned for only future but it'll require handling situations with at least one
    # repetition for past meeting.
    existing = meeting.repetitions.all()
    existing_dates = set(r.date for r in existing)

    create_repetitions, remove_dates = \
        sync_meeting_repetitions_internal(meeting, existing_dates, today, timezone=get_current_timezone())

    logger.debug('Dates generation/check done in %.4d seconds' % (time() - started,))

    if len(remove_dates):
        MeetingRepetition.objects.filter(meeting=meeting, date__in=remove_dates).delete()

    MeetingRepetition.objects.bulk_create(create_repetitions)

    meeting.reset_closest_repetition()

    logger.debug('Sync done in %.4d seconds total' % (time() - started,))


def every_day_generator(start, interval):
    i = 0
    while True:
        yield start + timedelta(days=i * interval)
        i += 1


def every_work_day_generator(start, interval):
    for d in every_day_generator(start, interval):
        if d.weekday() < 5:
            yield d


def every_week_generator(start, interval):
    i = 0
    while True:
        yield start + timedelta(weeks=i * interval)
        i += 1


def every_month_generator(start, interval):
    i = 0
    while True:
        yield start + relativedelta(months=i * interval)
        i += 1


def week_day_every_month_generator(start, interval, local_date):
    start_week = (local_date.day - 1) / 7 + 1
    start_wday = start.weekday()

    # Use "Last" for 5-th week
    wday = weekday(start_wday, -1 if start_week == 5 else start_week)

    rule = rrule(freq=MONTHLY, dtstart=start, count=MAX_YEARS * 12, interval=interval, byweekday=wday)

    it = iter(rule)
    while True:
        yield next(it).date()


def every_year_generator(start, interval):
    i = 0
    while True:
        yield start + relativedelta(years=i * interval)
        i += 1
