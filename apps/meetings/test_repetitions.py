from datetime import date, time, datetime, timedelta
from unittest.case import TestCase

import pytz
from django.utils.timezone import make_aware

from meetings.models import Meeting
from meetings.repetitions import sync_meeting_repetitions_internal, week_day_every_month_generator

TODAY = date(2017, 4, 2)


class TestRepetitions(TestCase):
    def test_no_repeat(self):
        meeting = Meeting(
            start=datetime.combine(TODAY, time(12)),
            repeat_type=Meeting.REPEAT_TYPES.once)

        create, remove = sync_meeting_repetitions_internal(meeting, [], TODAY)
        self.assertEqual(1, len(create))
        self.assertEqual(0, len(remove))
        self.assertEqual(TODAY, create[0].date)

    def test_no_repeat_in_past(self):
        date_in_past = TODAY - timedelta(days=3)
        meeting = Meeting(
            start=datetime.combine(date_in_past, time(12)),
            repeat_type=Meeting.REPEAT_TYPES.once)

        create, remove = sync_meeting_repetitions_internal(meeting, [], TODAY)
        self.assertEqual(1, len(create))
        self.assertEqual(0, len(remove))
        self.assertEqual(date_in_past, create[0].date)

    def test_create_every_day_without_limit(self):
        start = date(2017, 4, 7)
        meeting = Meeting(
            start=datetime.combine(start, time(12)),
            repeat_type=Meeting.REPEAT_TYPES.every_day,
            repeat_interval=2)

        create, remove = sync_meeting_repetitions_internal(meeting, [], TODAY)
        self.assertEqual(0, len(remove))
        self.assertEqual(911, len(create))  # 911 ~= (5 * 365 + 1 - 5) / 2
        self.assertEqual(date(2017, 4, 7), create[0].date)
        self.assertEqual(date(2017, 4, 9), create[1].date)

    def test_create_every_workday_with_max_count(self):
        start = date(2017, 4, 9)  # Sunday
        meeting = Meeting(
            start=datetime.combine(start, time(12)),
            repeat_type=Meeting.REPEAT_TYPES.every_work_day,
            repeat_max_count=10,
            repeat_interval=2)

        create, remove = sync_meeting_repetitions_internal(meeting, [], TODAY)
        self.assertEqual(0, len(remove))
        self.assertEqual(10, len(create))
        self.assertEqual(date(2017, 4, 11), create[0].date)  # every 2-nd day if it's a workday
        self.assertEqual(date(2017, 4, 13), create[1].date)

    def test_create_every_week_with_end_date(self):
        start = date(2017, 4, 9)  # Sunday
        meeting = Meeting(
            start=datetime.combine(start, time(12)),
            repeat_type=Meeting.REPEAT_TYPES.every_week,
            repeat_end_date=date(2017, 5, 7),
            repeat_interval=1)  # note every week

        create, remove = sync_meeting_repetitions_internal(meeting, [], TODAY)
        self.assertEqual(0, len(remove))
        self.assertEqual(5, len(create))
        self.assertEqual(date(2017, 4, 9), create[0].date)
        self.assertEqual(date(2017, 4, 16), create[1].date)
        self.assertEqual(date(2017, 5, 7), create[4].date)

    def test_sync(self):
        start = date(2017, 4, 1)
        meeting = Meeting(
            start=datetime.combine(start, time(12)),
            repeat_type=Meeting.REPEAT_TYPES.every_day,
            repeat_end_date=date(2017, 4, 14),
            repeat_interval=1)

        existing = [date(2017, 3, 29), date(2017, 3, 31), date(2017, 4, 2), date(2017, 5, 1)]

        create, remove = sync_meeting_repetitions_internal(meeting, existing, TODAY)

        self.assertEqual(3, len(remove))
        self.assertEqual(13, len(create))
        self.assertIn(date(2017, 3, 29), remove)
        self.assertEqual(date(2017, 4, 1), create[0].date)
        self.assertEqual(date(2017, 4, 3), create[1].date)
        self.assertEqual(date(2017, 4, 4), create[2].date)

    def test_month_by_week_num(self):
        start = date(2017, 4, 1)
        g = week_day_every_month_generator(start, 1, start)
        self.assertEqual(date(2017, 4, 1), next(g))
        self.assertEqual(date(2017, 5, 6), next(g))
        self.assertEqual(date(2017, 6, 3), next(g))

        start = date(2017, 4, 21)  # 3-d Friday
        g = week_day_every_month_generator(start, 1, start)
        self.assertEqual(date(2017, 4, 21), next(g))
        self.assertEqual(date(2017, 5, 19), next(g))
        self.assertEqual(date(2017, 6, 16), next(g))

        start = date(2017, 4, 22)  # 4-th Saturday
        g = week_day_every_month_generator(start, 1, start)
        self.assertEqual(date(2017, 4, 22), next(g))
        self.assertEqual(date(2017, 5, 27), next(g))
        self.assertEqual(date(2017, 6, 24), next(g))

        start = date(2017, 4, 29)  # "Last" Saturday
        g = week_day_every_month_generator(start, 1, start)
        self.assertEqual(date(2017, 4, 29), next(g))
        self.assertEqual(date(2017, 5, 27), next(g))
        self.assertEqual(date(2017, 6, 24), next(g))
        self.assertEqual(date(2017, 7, 29), next(g))

    def test_every_month_in_bad_tz(self):
        start = date(2017, 5, 29)  # 29 May 2017 = Monday, 5-th Monday
        moscow = pytz.timezone('Europe/Moscow')
        meeting = Meeting(
            # For some reason 2 a.m. 29 Jul - this is 11 p.m. 28 May UTC = 4-th Sunday
            start=make_aware(datetime.combine(start, time(2)), timezone=moscow),
            repeat_type=Meeting.REPEAT_TYPES.every_month,
            repeat_max_count=5,
            repeat_interval=1)

        create, remove = sync_meeting_repetitions_internal(meeting, [], TODAY, timezone=moscow)
        self.assertEqual(0, len(remove))
        self.assertEqual(5, len(create))
        self.assertEqual(date(2017, 5, 28), create[0].date)  # dates are UTC, so shifted
        self.assertEqual(date(2017, 6, 25), create[1].date)
        self.assertEqual(date(2017, 7, 30), create[2].date)  # 30 July - UTC, it's 5-th Sunday
