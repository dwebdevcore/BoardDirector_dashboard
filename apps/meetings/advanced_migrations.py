def meeting_next_repetitions_migration(connection, execute):
    if connection.vendor.startswith('postgres'):
        execute("""
            create or replace view meetings_meetingnextrepetition as
            select distinct on (meetings_meetingrepetition.meeting_id) meetings_meetingrepetition.id,
                meetings_meetingrepetition.date,
                meetings_meetingrepetition.meeting_id,
                meetings_meetingrepetition.id as repetition_id
            from meetings_meetingrepetition
            where meetings_meetingrepetition.date >= now()
            order by meetings_meetingrepetition.meeting_id, meetings_meetingrepetition.date
            """)
    else:
        # Basically SQLLite version for testing. Canonical SQL version for the problem, without distict on available.
        execute("""
                create view if not exists meetings_meetingnextrepetition as
                select 
                    r1.id,
                    r1.date,
                    r1.meeting_id,
                    r1.id as repetition_id
                from meetings_meetingrepetition r1
                where 
                    r1.date >= date('now')
                    and not exists (select 1 from meetings_meetingrepetition r2 where r2.meeting_id = r1.meeting_id and r2.date < r1.date and r2.date >= date('now'))
                order by r1.meeting_id, r1.date
                """)
