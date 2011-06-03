def load(file, debug=True):
    """Parse the XML file, create the environment, and ....leaving the running up to the libraries!"""
    
    print "Loading base tags..."

    try:
        baseDom, comments = loadFile(basePath)
    except Exception, e:
        print "Error loading base classes!"
        displayError(e)

    print "Compiling base classes..."

    try:
        baseClasses = [ClassFactory(elem) for elem in baseDom.getiterator('class')]
    except Exception, e:
        print "Error compiling base classes!"
        displayError(e)

    print "Loading application..." 

    try:
        appDom, comments = loadFile(file)
    except Exception, e:
        print "Error loading application!"
        displayError(e)

    print "Compiling application..."
    
    try:
        appClasses = [ClassFactory(elem) for elem in appDom.getiterator('class')]
    except Exception, e:
        print "Error generating application!"
        displayError(e)

    print "Writing program..."
    
    #try:
    t = open(appPath,'w')
    
    # write a global to hold the application pointer
    t.write("#global application pointer\napplication = False")
    
    # write the base classes
    [t.write("\n".join(c.flatten())) for c in baseClasses]
    
    # write the app classes
    [t.write("\n".join(c.flatten())) for c in appClasses]
    
    # Make the applications' object graph, and since we don't have self 
    # (it runs in the main of the module) set the path to nothin' ([], it would normally be ['self'])
    
    # set the name of the app to be application
    appDom.set('name','application_')
    
    # create the application class
    applicationClass = ClassFactory(appDom)

    # write it to the file
    t.write("\n".join(applicationClass.flatten()))
    
    #turn on debug if asked for
    if debug:   t.write("\n    import pdb\n    pdb.set_trace()")
    
    # write the "bootloader"
    t.write("""\
#Kick off the application
if __name__ == '__main__':
    application = application_(None, attrs=%r)"""%(appDom.attrib)
    )
    
    t.close()
    
    print "Finished loading.\n"
