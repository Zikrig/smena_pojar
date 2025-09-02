from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    shift_start = State()
    base1_patrol = State()
    atp_patrol = State()
    base2_patrol = State()
    problem_report = State()
    welding_work = State()
    emergency = State()
    fire_call = State()
    patrol_selection = State()
    patrol_problem = State()