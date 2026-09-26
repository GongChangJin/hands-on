from security_lab.sql import find_order, find_user


class Cursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, parameters=None):
        self.calls.append((query, parameters))
        return self

    def fetchall(self):
        return []


def test_user_input_is_parameterized():
    cursor = Cursor()
    payload = "' OR 1=1 --"
    find_user(cursor, payload)
    query, parameters = cursor.calls[-1]
    assert payload not in query
    assert parameters == (payload,)


def test_order_input_is_parameterized():
    cursor = Cursor()
    payload = "0 OR 1=1"
    find_order(cursor, payload)
    query, parameters = cursor.calls[-1]
    assert payload not in query
    assert parameters == (payload,)
