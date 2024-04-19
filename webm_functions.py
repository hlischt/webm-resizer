import math
import random

def dummy(frame_number: int, res: int) -> int:
    '''Returns the original resolution, unchanged.'''
    return res


def cyclic_resolution(frame_number: int, res: int) -> int:
    return math.ceil((res/4) * math.cos(frame_number / math.pi) + (res/4)*3)


def random_res(frame_number: int, res: int) -> int:
    return random.randint(2, 320)


def random_slow(frame_number: int, res: int) -> int:
    random.seed((frame_number//4) * res)
    return random.randint(2, 320)


def random_closure(minimum: int, maximum: int, hold: int):
    '''Create a random function that changes every `hold` number of frames.'''
    def rndm(frame_number: int, res: int) -> int:
        random.seed((frame_number//hold) * res)
        return random.randint(minimum, maximum)
    return rndm


def shrink(until: int):
    return lambda frame_num, res: \
        math.ceil((until + 1 - frame_num) * res)/(until + 1)
