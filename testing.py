import objects as obj
import game_engine as ge
from abstract_types import *
from returns.maybe import Some

a = "q"
b = True


match a, b:
    case ["q", True]:
        print("Here")
    case _:
        print("not")
