from datetime import datetime

class SecurityMemory:
    def __init__(self):
        self.execution_trace = []
        self.state = {}

    def log(self, agent_name, message, status="INFO"):
        """
        Logs an event with a status tag for better UI rendering later.
        Valid statuses: INFO, SUCCESS, WARNING, ERROR
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.execution_trace.append({
            "agent": agent_name,
            "time": timestamp,
            "status": status.upper(),
            "message": message
        })

    def update_state(self, key, value):
        self.state[key] = value

    def get_state(self):
        return self.state

    def get_trace(self):
        return self.execution_trace