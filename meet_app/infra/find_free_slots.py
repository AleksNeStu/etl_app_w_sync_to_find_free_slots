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

USER4_BUSY_SLOTS = [
    # Overlaps w/ exp_slot_w_hours on left side => 8.30 - 10.00
    Timeslot(datetime(2012, 5, 21, 6),
             datetime(2012, 5, 21, 10, 00)),

    # Overlaps w/ exp_slot_w_hours on right side => 16.00 - 17.30
    Timeslot(
        datetime(2012, 5, 23, 16),
        datetime(2012, 5, 23, 19)),
]

BUSY_SLOTS = (
    USER1_BUSY_SLOTS, USER2_BUSY_SLOTS, USER3_BUSY_SLOTS, USER4_BUSY_SLOTS)

EXP_TIMESLOT = Timeslot(
    datetime(2012, 5, 21, 6),
    datetime(2012, 5, 23, 20))

EXP_WORKING_HOURS = WorkingHours(time(8, 30), time(17, 30))

EXP_MEET_LEN = timedelta(minutes=30)

USERS_IDS = [1, 2, 8, 9]


def cut_left_start_dt(exp_slot, exp_working_hours):
    w_start_t = exp_working_hours.start  # w1
    w_end_t = exp_working_hours.end  # w2
    # LEFT
    l_start_dt = exp_slot.start
    l_start_t = l_start_dt.time()  # x1
    if w_start_t < l_start_t and l_start_t > w_end_t:
        # next day
        l_start_dt = datetime.combine(
            (l_start_dt + timedelta(days=1)).date(), w_start_t)
    elif w_start_t >= l_start_t:
        # w1: replace
        l_start_dt = datetime.combine(l_start_dt.date(), w_start_t)
    # elif w1 <= l_start_t:
    #     # l_start_t: no changes
    return l_start_dt


def cut_right_end_dt(exp_slot, exp_working_hours):
    w_start_t = exp_working_hours.start  # w1
    w_end_t = exp_working_hours.end  # w2
    # RIGHT
    r_end_dt = exp_slot.end
    r_end_t = r_end_dt.time()  # x2

    if w_end_t > r_end_t and r_end_t < w_start_t:
        # next day
        r_end_dt = datetime.combine(
            (r_end_dt - timedelta(days=1)).date(), w_end_t)
    elif w_end_t <= r_end_t:
        # w2: replace
        r_end_dt = datetime.combine(r_end_dt.date(), w_end_t)
    # elif w2 >= w_end_t:
    #     # w_end_t: no changes
    return r_end_dt


@Timer(text=f"Time consumption for {'get_exp_slot_w_working_hours'}: {{:.3f}}")
def get_exp_slot_w_working_hours(exp_slot, exp_working_hours):
    l_start_dt = cut_left_start_dt(exp_slot, exp_working_hours)
    r_end_dt = cut_right_end_dt(exp_slot, exp_working_hours)

    exp_slot_w_hours = Timeslot(l_start_dt, r_end_dt)

    return exp_slot_w_hours


#TODO: Improve code and logic (but works as expected)
@Timer(text=f"Time consumption for {'get_exp_slot_w_working_hours'}: {{:.3f}}")
def get_middle_slots(busy_slots, exp_slot_w_hours):
    middle_slots = []

    unioned_slot = False
    for i in range(len(busy_slots) - 1):
        current, next = (busy_slots[i], busy_slots[i + 1])

        # Busy slot not in range initial search.
        if not current.intersects(exp_slot_w_hours):
            continue

        if not current.intersects(next):

            if unioned_slot:
                unioned_slot = unioned_slot.union(current)
                middle_slots.append(unioned_slot)
                unioned_slot = None
            else:
                middle_slots.append(current)
        else:
            if not unioned_slot:
                unioned_slot = current
            else:
                unioned_slot = unioned_slot.union(current)

        if i == (len(busy_slots) - 2) and next.intersects(exp_slot_w_hours):
            middle_slots.append(next)

    # [<Timeslot(start=2012-05-22 07:00:00, end=2012-05-22 09:00:00)>,
    # <Timeslot(start=2012-05-22 10:00:00, end=2012-05-22 10:30:00)>,
    # <Timeslot(start=2012-05-22 11:00:00, end=2012-05-22 15:00:00)>,
    # <Timeslot(start=2012-05-22 15:30:00, end=2012-05-22 17:30:00)>]
    return middle_slots


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
    # With duplications to make repr of steps, but sorted for future proc.
    del users_ids
    users_busy_slots = list(py_utils.flatten(BUSY_SLOTS))
    return sorted(users_busy_slots)

# @Timer(text=f"Time consumption for {'get_free_slots'}: {{:.3f}}")
def get_free_slots(users_ids, exp_slot, exp_meet_len, exp_working_hours):
    free_slots = []
    busy_slots = get_busy_slots(users_ids)
    all_slots = extract_all_slots(busy_slots, exp_slot, exp_working_hours)

    for i in range(len(all_slots) - 1):
        start, end = (all_slots[i].end, all_slots[i + 1].start)
        if start <= end:
            raise Exception(
                f'Error on getting free time slots for users: {users_ids}')

        while start + exp_meet_len <= end:
            free_slots.append((start, start + exp_meet_len))
            print("{:%m/%d/%Y, %H:%M:%S} - {:%m/%d/%Y, %H:%M:%S}".format(
                start, start + exp_meet_len))
            start += exp_meet_len

    return free_slots


proposed_slots = get_free_slots(
    USERS_IDS, EXP_TIMESLOT, EXP_MEET_LEN, EXP_WORKING_HOURS)