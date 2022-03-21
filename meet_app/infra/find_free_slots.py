# TODO: Finish and refactor
from datetime import datetime, timedelta
from timeslot import Timeslot

appointments = [Timeslot(datetime(2012, 5, 22,
                                  10),
                         datetime(2012, 5, 22,
                                  10, 30)),

                Timeslot(datetime(2012, 5, 22,
                                  12),
                         datetime(2012, 5, 22,
                                  13)),

                Timeslot(datetime(2012, 5, 22,
                                  12),
                         datetime(2012, 5, 22,
                                  13)),

                # Overwrite
                Timeslot(datetime(2012, 5, 22,
                                  12),
                         datetime(2012, 5, 22,
                                  15)),

                Timeslot(datetime(2012, 5, 22,
                                  11),
                         datetime(2012, 5, 22,
                                  14)),


                Timeslot(datetime(2012, 5, 22,
                                  7),
                         datetime(2012, 5, 22,
                                  9)),
                Timeslot(datetime(2012, 5, 22,
                                  8),
                         datetime(2012, 5, 22,
                                  9)),




                # Normal
                Timeslot(datetime(2012, 5, 22,
                                  15, 30),
                         datetime(2012, 5, 22,
                                  17, 10))]

hours = Timeslot(datetime(2012, 5, 22, 9), datetime(2012, 5, 22, 18))


def get_slots(hours, appointments, duration=timedelta(minutes=30)):

    # DONE  unique_appointments
    unique_appointments = []

    sorted_appointments = sorted(appointments)

    count = len(sorted_appointments) - 1
    unioned_app = False
    for i in range(count):
        app1, app2 = (sorted_appointments[i], sorted_appointments[i + 1])

        if not app1.intersects(app2):

            if unioned_app:
                unioned_app = unioned_app.union(app1)
                unique_appointments.append(unioned_app)
                unioned_app = None
            else:
                unique_appointments.append(app1)
        else:
            if not unioned_app:
                unioned_app = app1
            else:
                unioned_app = unioned_app.union(app1)

        if i == (count - 1):
            unique_appointments.append(app2)

    #  [<Timeslot(start=2012-05-22 07:00:00, end=2012-05-22 09:00:00)>, <Timeslot(start=2012-05-22 10:00:00, end=2012-05-22 10:30:00)>, <Timeslot(start=2012-05-22 11:00:00, end=2012-05-22 15:00:00)>, <Timeslot(start=2012-05-22 15:30:00, end=2012-05-22 17:10:00)>]

    # DONE  unique_appointments


    # TODO

    slots = sorted(
        [(hours[0], hours[0])] + unique_appointments + [(hours[1], hours[1])])

    for i in range(len(slots) - 1):
        start, end = (slots[i][1], slots[i + 1][0])
        # assert start <= end, "Cannot attend all appointments"
        if start <= end:
            g = 1

        while start + duration <= end:
            print("{:%m/%d/%Y, %H:%M:%S} - {:%m/%d/%Y, %H:%M:%S}".format(start,
                                                                         start + duration))
            start += duration
