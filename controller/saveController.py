#!/usr/bin/python3
# -*- coding-utf_8 -*-
import json
from log import logger
from app import signalManager

def load_json(fpath):
    with open(fpath,'r', encoding='utf-8') as f:
        dict_data = json.loads(f.read())
    return dict_data

class SaveController(object):

    def __init__(self):
        self.initData()
        self.initConnect()

    def initData(self):
        self.start_map = load_json('start.json')
        self.config_map = load_json('config.json')

    def initConnect(self):
        signalManager.startArgsChanged.connect(self.save_startArgs)
        signalManager.configArgsChanged.connect(self.save_configArgs)

    def save_startArgs(self, start_map):
        logger.info('saving startArgs!!')
        self.start_map = start_map

        with open('start.json', 'w') as f:
            f.write(json.dumps(self.start_map, indent=4))

    def save_configArgs(self, config_map):
        logger.info('save_configArgs!!')
        self.config_map = config_map

        with open('config.json', 'w') as f:
            f.write(json.dumps(self.config_map, indent=4))

