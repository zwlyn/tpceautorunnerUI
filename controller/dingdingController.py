


class  DingdingController(object):
    def __init__(self):
        self.initData()
        self.initConnect()

    def  initData(self):
        pass

    def initConnect(self):
        pass

    def sendmsg(self,dingdingUrl,mesgpath):
        try:
            for url in dingdingUrl:
                HEADERS  =  {
                    "Content-Type": "application/json;charset=utf-8"
                }
                message  =  mesgpath
                String_textMsg  = {
                     "msgtype": "markdown",
                     "markdown": {
                         "title":"tpce test",
                         "text": "\n" +
                                 "> \n\n" +
                                 "> ![screenshot](%s)\n" % mesgpath  +
                                 "> \n"
                     },
                    "at": {
                        "atMobiles": [
                            "156xxxx8827", 
                            "189xxxx8325"
                        ], 
                        "isAtAll": 1
                    }
                    }
                String_textMsg  =  json.dumps(String_textMsg)
                res  =  requests.post(url, data = String_textMsg, headers = HEADERS)
                logger.info(u"钉钉发送【%s】成功！" % url)
                logger.info(res.json())

        except Exception as e:
            logger.error(traceback.format_exc(e))
            logger.error(u'钉钉发送失败！')
            logger.error(repr(e))