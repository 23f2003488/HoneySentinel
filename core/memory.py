from datetime import datetime

class SecurityMemory:
    def __init__(self):
        self.execution_trace = []
        self.state = {}

    def log(self, agent_name, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.execution_trace.append({
            "agent": agent_name,
            "time": timestamp,
            "message": message
        })

    def update_state(self, key, value):
        self.state[key] = value

    def get_state(self):
        return self.state

    def get_trace(self):
        return self.execution_trace