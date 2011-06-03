import xml.etree.ElementTree as et
import os, sys, re, traceback, wildfire
from Factories import ObjectGraph
from Factories import ClassFactory

#make the application in the current working directory
appPath = os.path.join(os.getcwd(), 'app.py')
#get the path to the base modules
basePath = os.path.join(os.path.split(wildfire.__file__)[0],'base.wfx')
basecwd = os.getcwd()

class Application:
    """ Perform functions necessary to start a wildfire application, including
        patching code into a running instance of the engine.
    """
    
    def __init__(self):
        self.output = []
        
    def compile(self, dom):
        #if a filepath is passed in, open that file and load the dom from it:
        if type(dom) is type(""):
            xml = file(dom).read()
            eofPos = re.finditer("^EOF$", xml)
            if eofPos: print "EOF detected", eofPos[0].start()
            dom = et.fromstring(xml_dom.strip())
        
        self.includes(dom)
        [buf.append("\n".join(ClassFactory(elem).flatten())) for elem in dom.getiterator('class')]
        
    def includes(self, dom, cwd=basecwd):
        for elem in dom.getiterator('include'):
            src = elem.get('src')
            path_parts = src.split('/')[:1]
            file_name = src.split('/')[-1]
            print 
            
            self.include(elem, cwd=cwd)
        
        
        #take the element
        #load the specified file
        #append to the parent nodes' children
        #send back to includes with updated cwd (cwd+path up to last '/' entry)
        
        

        
    
