from swinf.selector import handler

@handler("GET")
def hello():
    return "<h1>Welcome to Swinf!</h1>"
