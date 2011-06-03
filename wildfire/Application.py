import xml.etree.ElementTree as et

class Application:
    """ Perform functions necessary to start a wildfire application, including
        patching code into a running instance of the engine.
    """
    def __init__(self, dom):
        #if a filepath is passed in, open that file and load the dom from it:
        if type(dom) is type(""):
            fp = file(dom).read()
            
        
            
        
    