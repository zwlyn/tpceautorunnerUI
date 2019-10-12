
class AgentController(object):

    def __init__(self):
        self.initData()
        self.initConnect()

    def initData(self):
        self.start_map = load_json('start.json')

    def initConnect(self):
        pass