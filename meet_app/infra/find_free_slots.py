import dataclasses
from datetime import datetime, timedelta, time

from codetiming import Timer
from timeslot import Timeslot

from utils import py as py_utils


@dataclasses.dataclass
class WorkingHours:
    start: time
    end: time


USER1_BUSY_SLOTS = [
    # Less: 2011 year
    Timeslot(
        datetime(2011, 5, 22, 16),
        datetime(2011, 5, 22, 16, 30)),
]
USER2_BUSY_SLOTS = [
    # Duplication
    Timeslot(
        datetime(2012, 5, 22, 12),
        datetime(2012, 5, 22, 13)),

    Timeslot(datetime(2012, 5, 22, 12),
             datetime(2012, 5, 22, 13)),

    # Overlaps
    Timeslot(datetime(2012, 5, 22, 12),
             datetime(2012, 5, 22, 15)),

    Timeslot(datetime(2012, 5, 22, 11),
             datetime(2012, 5, 22, 14)),

    Timeslot(datetime(2012, 5, 22, 7),
             datetime(2012, 5, 22, 9)),
    Timeslot(datetime(2012, 5, 22, 8),
             datetime(2012, 5, 22, 9)),
]

USER3_BUSY_SLOTS = [
    # Normal
    Timeslot(datetime(2012, 5, 22, 15, 30),
             datetime(2012, 5, 22, 17, 30)),

    Timeslot(
        datetime(2012, 5, 22, 10),
        datetime(2012, 5, 22, 10, 30)),

    # More: 2022 year
    Timeslot(
        datetime(2022, 5, 22, 11),
        datetime(2022, 5, 22, 11, 30)),
]

BUSY_SLOTS = USER1_BUSY_SLOTS, USER2_BUSY_SLOTS, USER3_BUSY_SLOTS

EXP_TIMESLOT = Timeslot(
    datetime(2012, 5, 21, 6),
    datetime(2012, 5, 23, 20))

EXP_WORKING_HOURS = WorkingHours(time(8, 30), time(17, 30))

EXP_MEET_LEN = timedelta(minutes=30)


@Timer(text=f"Time consumption for {'get_exp_slot_w_working_hours'}: {{:.3f}}")
def get_exp_slot_w_working_hours(exp_slot, exp_working_hours):
    left_start = exp_slot.start
    left_end = exp_slot.end

    l_start = exp_working_hours.start
    l_end = exp_working_hours.end

#TODO: Improve code and logic (but works as expected)
@Timer(text=f"Time consumption for {'get_exp_slot_w_working_hours'}: {{:.3f}}")
def get_middle_slots(busy_slots, exp_slot_w_hours):
    #  [<Timeslot(start=2012-05-22 07:00:00, end=2012-05-22 09:00:00)>, <Timeslot(start=2012-05-22 10:00:00, end=2012-05-22 10:30:00)>, <Timeslot(start=2012-05-22 11:00:00, end=2012-05-22 15:00:00)>, <Timeslot(start=2012-05-22 15:30:00, end=2012-05-22 17:10:00)>]
    middle_slots = []
    sorted_appointments = sorted(busy_slots)
    count = len(sorted_appointments) - 1
    unioned_app = False
    for i in range(count):
        first, second = (sorted_appointments[i], sorted_appointments[i + 1])

        if not first.intersects(second):

            if unioned_app:
                unioned_app = unioned_app.union(first)
                middle_slots.append(unioned_app)
                unioned_app = None
            else:
                middle_slots.append(first)
        else:
            if not unioned_app:
                unioned_app = first
            else:
                unioned_app = unioned_app.union(first)

        if i == (count - 1):
            middle_slots.append(second)

@Timer(text=f"Time consumption for {'extract_all_slots'}: {{:.3f}}")
def extract_all_slots(busy_slots, exp_slot, exp_working_hours):
    exp_slot_w_hours = get_exp_slot_w_working_hours(
        exp_slot, exp_working_hours)
    # LEFT and RIGHT
    left_slot = Timeslot(exp_slot_w_hours.start, exp_slot_w_hours.start)
    right_slot = Timeslot(exp_slot_w_hours.end, exp_slot_w_hours.end)

    # MIDDLE
    middle_slots = get_middle_slots(busy_slots, exp_slot_w_hours)

    # ALL
    all_slots = sorted([left_slot] + middle_slots + [right_slot])
    return all_slots

#TODO: Replace to real DB users meets data
@Timer(text=f"Time consumption for {'get_busy_slots'}: {{:.3f}}")
def get_busy_slots(users_ids):
    del users_ids
    users_busy_slots = py_utils.flatten(BUSY_SLOTS)
    return sorted(set(BUSY_SLOTS))

# @Timer(text=f"Time consumption for {'get_free_slots'}: {{:.3f}}")
def get_free_slots(users_ids, exp_slot, exp_meet_len, exp_working_hours):
    free_slots = []
    busy_slots = get_busy_slots(users_ids)
    all_slots = extract_all_slots(busy_slots, exp_slot, exp_working_hours)

    for i in range(len(all_slots) - 1):
        start, end = (all_slots[i].end, all_slots[i + 1].start)
        if start <= end:
            raise (f'Error on getting free time slots for users: {users_ids}')

        while start + exp_meet_len <= end:
            free_slots.append((start, start + exp_meet_len))
            print("{:%m/%d/%Y, %H:%M:%S} - {:%m/%d/%Y, %H:%M:%S}".format(
                start, start + exp_meet_len))
            start += exp_meet_len

    return free_slots

proposed_slots = get_free_slots(
    [1, 2, 8, 9], EXP_TIMESLOT, EXP_MEET_LEN, EXP_WORKING_HOURS)

g1 = []