
def load_json(fpath):
    with open(fpath,'r', encoding='utf-8') as f:
        dict_data = json.loads(f.read())
    return dict_data
    
class Model(object):

	def __init__(self):
		super(Model, self).__init__()

	