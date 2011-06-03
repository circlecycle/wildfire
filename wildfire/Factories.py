import Helpers
import xml.etree.ElementTree as et
from xml.etree.ElementTree import tostring

#these track tag types that receieve special treatment along the way
NAMELESS_NODES = ['attribute', 'handler', 'method', 'class']
TAG_NAME_REMAP = {'import':'_import', 'class':'BaseClass'}
NON_COPIED_ATTRS = ['name', 'id', 'extends']
UNNAMED_COUNTER = 0

class ClassBuilder:
    """I assist in the making of classes by giving different indents to different inputs
       (either lists of strings or strings) and returning the concatenated results 
       after their done with me.
    """
    
    def __init__(self):
        self.output = []
    
    def classLevel(self, lines):
        if type(lines) is type(""): lines = [lines]
        self.output.extend(lines)
        
    def memeberLevel(self, lines):
        if type(lines) is type(""): lines = [lines]
        self.output.extend(["    %s"%x for x in lines]) 
        
    def execLevel(self, lines):
        if type(lines) is type(""): lines = [lines]
        self.output.extend(["        %s"%x for x in lines]) 
        
    def blankLine(self):
        self.output.append("")
        
    def getClassLines(self):
        self.blankLine()
        self.blankLine()
        return self.output

class ClassFactory:
    """ I take a class definition and return a list that when 
        joined is the actual code to make the python class described
        by the class xml tag passed to me. 
    """
    
    def __init__(self, elem):
        self.elem = elem
        self.builder = ClassBuilder()
        
        #if the element has a reserved class name (like "class") we 
        #use a lookup to rewrite it to something usuable (e.g. "class"->"BaseClass")
        if elem.get('name') in TAG_NAME_REMAP: 
            elem.set('name', TAG_NAME_REMAP[elem.get('name')])

    def flatten(self):
        #MODULE LEVEL IMPORTS
        imports = [node for node in self.elem.getchildren() if node.tag == 'import']
        self.builder.blankLine()
        self.builder.classLevel("#module level imports")
        for entry in imports:
            if entry.get('as'):
                self.builder.classLevel("import %s as %s"%(entry.get('name'), entry.get('as')))
            else:
                self.builder.classLevel("import %s"%(entry.get('name')))
        if imports:    
            self.builder.blankLine()
            
        #MODULE LEVEL GLOBALS
        globalsToAdd = [node for node in self.elem.getchildren() if node.tag == 'global']   
        globalsLines = []
        [globalsLines.extend(AttributeValueFactory(node).flatten()) for node in globalsToAdd]
        if globalsLines:
            self.builder.classLevel("#global attributes")
            self.builder.classLevel(globalsLines)
            self.builder.blankLine()
        
        #CLASS DEFINITION
        extends = self.elem.get('extends') or 'node'
        if extends != 'none':
            self.builder.classLevel("class %s(%s):"%(self.elem.get('name'), extends))
        else:
            self.builder.classLevel("class %s:"%(self.elem.get('name')))
        
        #COMPILED ATTRIBUTES
        attributes = [node for node in self.elem.getchildren() if node.tag == 'attribute']    
        #   STORE ALL ATTRIUBUTE TYPES
        attributeTypeLine = AttributeTypesFactory(attributes).flatten()
        if attributeTypeLine:
            self.builder.memeberLevel("#attribute type lookup")
            self.builder.memeberLevel(attributeTypeLine)
        
        #   ASSIGN ALL DEFAULT VALUES
        attributeLines = []
        [attributeLines.extend(AttributeValueFactory(node).flatten()) for node in attributes]
        if attributeLines:
            self.builder.memeberLevel("#static attributes")
            self.builder.memeberLevel(attributeLines)
        
        #COMPILED METHODS
        methods = [node for node in self.elem.getchildren() if node.tag == 'method']  
        methodLines = []
        [methodLines.extend(MethodFactory(node).flatten()) for node in methods]
        self.builder.memeberLevel(methodLines)
        self.builder.blankLine()
        
        #OBJECT GRAPH
        self.builder.memeberLevel("#builtin method: __objectgraph__")
        self.builder.memeberLevel("def __objectgraph__(self, %s):" %(self.elem.get('args')  or ''))
        ogs = []
        [ogs.extend(ObjectGraph(child).flatten()) for child in self.elem.getchildren()]
        #indent the output, if no object graph print at least pass
        self.builder.execLevel(ogs or ['pass'])
        
        #return the list of lines that define this class.
        return self.builder.getClassLines()
                
class MethodFactory:
    def __init__(self, elem):
        self.elem = elem
        self.name = elem.get('name')
        self.args = elem.get('args') or ''
        
    def flatten(self):
        #create the function definition line
        buf = ["", "#static method: %(name)s" % self.__dict__]
        buf.append("def %(name)s(self, %(args)s):"%(self.__dict__))
        #normalize and indent the function text
        [buf.append('    %s' % line) for line in Helpers.normalizeScript(self.elem.text or '').split('\n')]
        return buf
        
class AttributeTypesFactory:
    """ I turn a series of attribute tags into a single python statement
        that makes a dictionary keyed on name:type
    """
    types = {'expression':'eval', 'number':'float', 'string':'str'}

    def __init__(self, elems):
        self.elems = elems

    def flatten(self):
        output = {}
        for elem in self.elems:
            try:    output[elem.get('name')] = self.types[elem.get('type') or 'expression']
            except Exception, e: 
                raise "Type '%s' is not defined at element:\n%s\n"%(elem.get('type'), tostring(elem))
        return ["attrtypes_ = %s"%output]
        
class AttributeValueFactory:
    """ I turn a single attribute tag into a python statement
        that will initialize that attribute.
    """
    types = {'expression':'', 'number':'float', 'string':'str'}
    
    def __init__(self, elem):
        self.name = elem.get('name')
        self.type = elem.get('type') or 'expression'
        self.value = elem.get('value')

    def flatten(self):
        #if no value then there is nothing to do
        if not self.value:
            return []
    
        return [Helpers.castValueFromType(self.name, self.type, self.value)]
        
class ObjectGraph:
    """ I take a DOM tree and produce a list python code to instantiate 
        both named and unnamed nodes in a given namespace
    """
        
    def __init__(self, elem, path=['self']):
        self.elem = elem
        self.path = path
        
    def flatten(self):
        """ I return a list of code lines meant to be added to a classes init method """
        self.lines = []
        self.walk(self.elem, path=self.path, topmostnode=True)
        return self.lines
        
    def walk(self, elem, path, topmostnode=False):
        """ I traverse a dom tree in document order, creating python commands
            that would create the same tree - an xml->python object graph creator
        """
        
        global UNNAMED_COUNTER
                
        #if the encountered tags are either a class definition or an import
        #ignore them, because these are not part of the object graph
        if ['class', 'import', 'global'].count(elem.tag): 
            return
            
        #if we are at the top of the object graph - aka - directly under
        #the class defintion, don't process method tags. These are automatically
        #defined as "static methods" and handled in the class factory
        if topmostnode and ["method", "attribute"].count(elem.tag): 
            return
        
        #get the class name
        classname = elem.tag
        
        #get the text of the node, if any
        if elem.text and elem.text.strip():
          elem.attrib['text'] = elem.text            
        else:
          elem.attrib['text'] = ""

        #assign a name if one has not been provided.
        name = elem.get('name')
        if (not name) or elem.tag in NAMELESS_NODES:
          name = "anon_%s_"%(UNNAMED_COUNTER)
          UNNAMED_COUNTER += 1
          
        #Get the context of the call (o)
        realPath = '.'.join(path)
            
        #make the object creation statement, and continue our little walk in the park
        dot = ''
        if realPath: dot = '.'
        
        self.lines.append("""%s%s%s = %s(%s, %s, topmostnode=False)"""%(realPath, dot, name, classname, realPath or 'None', `elem.attrib`))
        
        for child in elem.getchildren():
            self.walk(child, path=path+[name])
