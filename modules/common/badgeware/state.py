import os
import json

class State:
    @staticmethod
    def delete(app):
        try:
            os.remove("/state/{}.json".format(app))
        except OSError:
            pass

    @staticmethod
    def save(app, data):
        try:
            with open("/state/{}.json".format(app), "w") as f:
                f.write(json.dumps(data))
                f.flush()
        except OSError:
            import os

            try:
                os.stat("/state")
            except OSError:
                os.mkdir("/state")
                State.save(app, data)

    @staticmethod
    def modify(app, data):
        state = {}
        State.load(app, state)
        state.update(data)
        State.save(app, state)

    @staticmethod
    def load(app, defaults):
        try:
            data = json.loads(open("/state/{}.json".format(app), "r").read())
            if type(data) is dict:
                defaults.update(data)
                return True
        except (OSError, ValueError):
            pass

        State.save(app, defaults)
        return False
