import json
import urllib.request
from datetime import datetime
from dateutil.relativedelta import relativedelta
# There will be blocked dates at the end of the listing, so we can't just use that one and modify it.
# Easiest solution is to just create a fake.
fake_final_rollover_event = ["BEGIN:VEVENT", "DTEND;VALUE=DATE:" + ((datetime.now() + relativedelta(years=3)).strftime("%Y%m%d")),"DTSTART;VALUE=DUMMY", "UID:6fec1092d3fb-eeacf4609833f61743ba9ad02776d771@airbnb.com", "SUMMARY:The Final Event", "END:VEVENT"]
def lambda_handler(event, context):
    # TODO implement
    contents = urllib.request.urlopen("http://www.airbnb.com/calendar/ical/622748976782753312.ics?s=2f51c4709de6e3d96664e043146b19dd").read().decode("utf-8")
    lines = contents.split("\n")
    lines.extend(fake_final_rollover_event)
    curr_set = []
    curr_end_is_weekend = False
    curr_summary_is_reserved = True
    new_lines = []
    in_vevent = False
    rollover = False
    curr_end_date = None
    last_cleaning_end_date = None
    for line in lines:
        if not in_vevent and not line == "BEGIN:VEVENT":
            # always include lines outside of a vevent
            new_lines.append(line)
        else:
            if not in_vevent:
                in_vevent = True
                
            if line.startswith("DTSTART"):
                if rollover:#hackery to make sure same day booking status remains
                    curr_set.append("DTSTART;VALUE=DATE:" + last_cleaning_end_date)
                else:
                    start_date_str = line[19:]
                    if start_date_str == last_cleaning_end_date:
                        rollover=True
                    curr_set.append(line)
            else:
                curr_set.append(line)
            if line.startswith("DTEND"):
                curr_end_date = line[17:]
                day_of_week = datetime.strptime(curr_end_date, '%Y%m%d').strftime('%A')
                curr_end_is_weekend = day_of_week == "Saturday" or day_of_week == "Sunday"
            elif line.startswith("SUMMARY"):
                print(line)
                curr_summary_is_reserved = line[8:] != "The Final Event"
            elif line == "END:VEVENT":
                in_vevent = False
                if not curr_summary_is_reserved or curr_end_is_weekend:
                    new_lines.extend(curr_set)
                    rollover = False
                    last_cleaning_end_date = curr_end_date
                curr_set = []
                in_vevent = False
                curr_end_is_weekend = False
                curr_summary_is_reserved = True
    return {"statusCode": "200", "body": "\n".join(new_lines).encode("utf-8")}
