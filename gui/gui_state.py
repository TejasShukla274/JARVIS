# gui/gui_state.py

# stores current assistant state
# idle / listening / speaking

assistant_state = "idle"


def set_state(state):

    global assistant_state

    assistant_state = state


def get_state():

    return assistant_state