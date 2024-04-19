import math
import random
import sys

def dummy(frame_number: int, res: int) -> int:
    '''Returns the original resolution, unchanged.'''
    return res


def cyclic(frame_number: int, res: int) -> int:
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


func_dict = {
    'shrink':      (shrink,      'closure'),
    'random_slow': (random_slow, 'direct'),
    'random':      (random_res,  'direct'),
    'cyclic':      (cyclic,      'direct'),
    'dummy':       (dummy,       'direct'),
}


def init_func(name: str, length: int):
    try:
        func, kind = func_dict[name]
        if kind == 'closure':
            return func(length)
        return func
    except KeyError:
        sys.exit(f'Error: {name} is not defined in webm_functions.py')
