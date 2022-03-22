from datetime import datetime, timedelta, time, timezone

from codetiming import Timer
from timeslot import Timeslot

from services import meet_service
from utils import py as py_utils

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

EXP_WORKING_HOURS = py_utils.WorkingHours(time(8, 30), time(17, 30))

EXP_MEET_LEN = timedelta(minutes=30)

USERS_IDS = [1, 2, 8, 9]


@Timer(text=f"Time consumption for {'get_slot_from_slots'}: {{:.3f}}")
def get_joined_slot(slots):
    min_slot = min(slots)
    max_slot = max(slots)
    joined_slot = Timeslot(min_slot.start.replace(tzinfo=timezone.utc),
                           max_slot.end.replace(tzinfo=timezone.utc))
    return min_slot, max_slot, joined_slot


@Timer(text=f"Time consumption for {'cut_left_start_dt'}: {{:.3f}}")
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


@Timer(text=f"Time consumption for {'cut_right_end_dt'}: {{:.3f}}")
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


@Timer(text=f"Time consumption for {'split_middle_slots'}: {{:.3f}}")
def split_middle_slots(middle_slots, exp_slot_w_hours, exp_working_hours):
    # In func scope helpers.
    # -------------------------------------------------------
    #TODO: Extract on func w/ param start or end
    def split_left(slot):
        # Possibly split very first slot.
        if (not exp_slot_w_hours.contains(slot) and
                slot.intersects(exp_slot_w_hours)):
            slot.start = cut_left_start_dt(slot, exp_working_hours)
        return slot

    def split_right(slot):
        # Possibly split very first slot.
        if (not exp_slot_w_hours.contains(slot) and
                slot.intersects(exp_slot_w_hours)):
            slot.end = cut_right_end_dt(slot, exp_working_hours)
        return slot
    # -------------------------------------------------------

    if len(middle_slots) == 0:
        return middle_slots

    #TODO: To test and adjust
    if len(middle_slots) == 1:
        slot = split_right(split_left(middle_slots[0]))
        return [slot]

    # [<Timeslot(start=2012-05-21 08:30:00, end=2012-05-21 10:00:00)>, -> 8.30
    # ...
    # <Timeslot(start=2012-05-23 16:00:00, end=2012-05-23 17:30:00)>] -> 17.30
    if len(middle_slots) >= 2:
        middle_slots[0] = split_left(middle_slots[0])
        middle_slots[-1] = split_right(middle_slots[-1])
        return middle_slots


#TODO: Improve code and logic (but works as expected)
@Timer(text=f"Time consumption for {'get_exp_slot_w_working_hours'}: {{:.3f}}")
def get_middle_slots_w_union(busy_slots, exp_slot_w_hours, exp_working_hours):
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

    # [<Timeslot(start=2012-05-21 06:00:00, end=2012-05-21 10:00:00)>,
    # <Timeslot(start=2012-05-22 07:00:00, end=2012-05-22 09:00:00)>,
    # <Timeslot(start=2012-05-22 10:00:00, end=2012-05-22 10:30:00)>,
    # <Timeslot(start=2012-05-22 11:00:00, end=2012-05-22 15:00:00)>,
    # <Timeslot(start=2012-05-22 15:30:00, end=2012-05-22 17:30:00)>,
    # <Timeslot(start=2012-05-23 16:00:00, end=2012-05-23 19:00:00)>]
    return middle_slots


@Timer(text=f"Time consumption for {'extract_all_slots'}: {{:.3f}}")
def extract_all_slots(busy_slots, exp_slot, exp_working_hours):
    exp_slot_w_hours = get_exp_slot_w_working_hours(
        exp_slot, exp_working_hours)
    # LEFT and RIGHT
    left_slot = Timeslot(exp_slot_w_hours.start, exp_slot_w_hours.start)
    right_slot = Timeslot(exp_slot_w_hours.end, exp_slot_w_hours.end)

    # MIDDLE
    middle_w_union_slots = get_middle_slots_w_union(
        busy_slots, exp_slot_w_hours, exp_working_hours)
    adjusted_middle_slots = split_middle_slots(
        middle_w_union_slots, exp_slot_w_hours, exp_working_hours)

    # ALL
    all_slots = sorted([left_slot] + adjusted_middle_slots + [right_slot])

    return all_slots


#TODO: Replace to real DB users meets data
@Timer(text=f"Time consumption for {'get_busy_slots'}: {{:.3f}}")
def get_busy_slots(users_ids):
    # With duplications to make repr of steps, but sorted for future proc.
    users_busy_slots = meet_service.get_busy_timeslots_by_users_ids(users_ids)
    # users_busy_slots = list(py_utils.flatten(BUSY_SLOTS))
    return sorted(users_busy_slots)


# @Timer(text=f"Time consumption for {'get_free_slots'}: {{:.3f}}")
def get_free_slots(users_ids, exp_slot, exp_meet_len, exp_working_hours):
    busy_slots = get_busy_slots(users_ids)
    all_slots = extract_all_slots(busy_slots, exp_slot, exp_working_hours)

    w_start_t = exp_working_hours.start  # w1
    w_end_t = exp_working_hours.end  # w2
    free_slots = []

    for i in range(len(all_slots) - 1):
        current, next = (all_slots[i], all_slots[i + 1])
        start, end = current.end, next.start
        #TODO: Handle first and last and rest of the cases
        # if start <= end:
        #     raise Exception(
        #         f'Error on getting free time slots for users: {users_ids}')

        while start + exp_meet_len <= end:
            free_slot = Timeslot(start, start + exp_meet_len)
            # Limited to working hours.
            start_t = free_slot.start.time()
            end_t = free_slot.end.time()
            if (w_start_t <= start_t < w_end_t and
                w_start_t < end_t <= w_end_t):

                free_slots.append(free_slot)
            # For debugging purposes.
            # print(
            #     "{:%m/%d/%Y, %H:%M:%S} - {:%m/%d/%Y, %H:%M:%S}".format(
            #         start, start + exp_meet_len))

            start += exp_meet_len

    return busy_slots, free_slots


# # 100 first ids
# users_ids=list(range(1, 101, 1))
#
# # db_users = user_service.get_users_by_ids(users_ids)
# users_meets = meet_service.get_meets_by_users_ids([22])  # 64 count
# proposed_slots = get_free_slots(
#     USERS_IDS,
#     EXP_TIMESLOT,
#     EXP_MEET_LEN,
#     EXP_WORKING_HOURS)

