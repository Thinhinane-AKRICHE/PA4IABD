from contextvars import ContextVar

current_user_id: ContextVar[int] = ContextVar('current_user_id', default=None)

def set_current_user(user_id: int):
    current_user_id.set(user_id)

def get_current_user() -> int:
    user_id = current_user_id.get()
    if user_id is None:
        raise ValueError("Aucun utilisateur dans le contexte")
    return user_id