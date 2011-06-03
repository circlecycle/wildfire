
from xml.etree.ElementTree import fromstring, tostring

def normalizeScript(value):
    """
        This analyzes a piece of python script to derive the proper first
        indent (by looking at the first line) and adjusts the rest accordingly.
    """
    value = value.split('\n')
    
    #find indent
    for line in value:
      if line.strip(): 
          indent = len(line) - len(line.lstrip())
          break
    
    #normalize script tab depth to zero, reindenting if wrapped in a defintion
    script = []
    for line in value:
      strippedline = line.strip()
      if not strippedline or strippedline[0] == '#': continue
      script.append(line[indent:])
      
    return '\n'.join(script)
    
def castValueFromType(name, typeof="expression", value=None):
    #make an expression from text
    if typeof in ['expression', 'eval']:
        if value == None: value = "None"
        return "%s = %s" % (name, value)
    
    #make an float from text
    elif typeof in ['number', 'float']:
        if value == None: value = 0
        return "%s = float(%r)" % (name, value)
    
    #make an string from text
    elif typeof in ['string', 'str']:
        if value == None: value = ""
        return "%s = %r" % (name, value)
    
    