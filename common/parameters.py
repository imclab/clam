###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Parameter classes --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################


from lxml import etree as ElementTree
from StringIO import StringIO

#class Validation(object):
#    def __init__(self, bool: valid, error = None):
#        self.valid = valid
#        self.error = error
#    
#    def __nonzero__(self):
#        return self.valid
    

def parameterfromxml(node):
    if not isinstance(node,ElementTree._Element):
        node = ElementTree.parse(StringIO(node)).getroot() 
    if node.tag in globals():
        id = ''
        paramflag = ''
        name = ''
        description = ''
        kwargs = {}
        for attrib, value in node.attrib.items():
            if attrib == 'id':
                id = value
            elif attrib == 'paramflag':
                paramflag = value       
            elif attrib == 'name':
                name = value
            elif attrib == 'description':
                description = value
            else:
                kwargs[attrib] = value
        for subtag in node: #parse possible subtags
            if subtag.tag == 'choice': #extra parsing for choice parameter (TODO: put in a better spot)
                if not 'choices' in kwargs: kwargs['choices'] = {}
                kwargs['choices'][subtag.attrib['id']] = subtag.text
                if 'selected' in subtag.attrib and (subtag.attrib['selected'] == '1' or subtag.attrib['selected'] == 'yes'):
                    if 'multi' in kwargs and kwargs['multi'] == 1:
                        if not 'default' in kwargs: kwargs['default'] = []
                        kwargs['default'].append(subtag.attrib['id'])
                    else:
                        kwargs['default'] = subtag.attrib['id']

        return globals()[node.tag](id, paramflag, name, description, **kwargs) #return parameter instance
    else:
        raise Exception("No such parameter exists: " + node.tag)

    pass

class AbstractParameter(object):
    def __init__(self, id, paramflag, name, description = '', **kwargs):
        self.id = id #a unique ID
        self.paramflag = paramflag #the parameter flag passed to the command (include a trailing space!)        
        self.name = name #a representational name
        self.description = description
        self.error = None                    
        self.value = False
        self.kwargs = kwargs #make a copy for XML generation later
        self.required = False
        self.nospace = False
        self.require = []
        self.forbid = []
        self.allowusers = []
        self.denyusers = []
        for key, value in kwargs.items():
            if key == 'allowusers': 
                self.allowusers = value  #Users to allow access to this parameter (If not set, all users have access)
            elif key == 'denyusers': 
                self.denyusers = value   #Users to deny access to this parameter (If not set, nobody is denied)
            elif key == 'value' or key == 'default':
                #set an error message
                self.set(value)
            elif key == 'required': 
                self.required = value  #Mandatory parameter?  
            elif key == 'require':
                #if this argument is set, the ones with the following IDs should as well
                self.require = value
            elif key == 'forbid':
                #if this argument is set, the ones with the following IDs can not
                self.forbid = value
            elif key == 'nospace':
                #no space between option and it's value
                self.nospace = value
            elif key == 'error':
                #set an error message (if you also set a value, make sure this is set AFTER the value is set)
                self.error = value

    def validate(self,value):
        self.error = None #reset error
        return True

    def compilearg(self, value):
        """This method compiles the parameter into syntax that can be used on the shell, such as for example: --paramflag=value"""
        if self.paramflag and self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        elif self.paramflag:
            sep = ' '
        return self.paramflag + sep + value

    def xml(self):
        """This methods renders an XML representation of this parameter, along with 
        its selected value, and feedback on validation errors"""
        xml = "<" + self.__class__.__name__
        xml += ' id="'+self.id + '"'
        xml += ' flag="'+self.paramflag + '"'
        xml += ' name="'+self.name + '"'
        xml += ' description="'+self.description + '"'
        for key, v in self.kwargs.items():    
            if isinstance(v, bool):
                xml += ' ' + key + '="' + str(int(v))+ '"'                    
            elif isinstance(v, list):
                xml += ' ' + key + '="'+",".join(v)+ '"'        
            elif isinstance(v, unicode) or isinstance(v, str)  :
                xml += ' ' + key + '="'+v+ '"'        
            else:
                xml += ' ' + key + '="'+str(v)+ '"'        
        if self.value:
            xml += ' value="'+unicode(self.value) + '"'
        if self.error:
            xml += ' error="'+self.error + '"'
        xml += " />"
        return xml

    def set(self, value):
        """This parameter method attempts to set a specific value for this parameter. The value will be validated first, and if it can not be set. An error message will be set in the error property of this parameter"""
        if self.validate(value):
            print "Parameter " + self.id + " successfully set to " + repr(value)
            self.value = value
            return True
        else:
            print "Parameter " + self.id + " COULD NOT BE set to " + repr(value)
            return False

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.id in postdata and postdata[self.id]:
            return postdata[self.id]
        else: 
            return False


    def access(self, user):
        """This method checks if the given user has access to see/set this parameter, based on the denyusers and/or allowusers option."""
        if self.denyusers:
            if user in self.denyusers:
                return False
        if self.allowusers:
            if not user in self.allowusers:
                return False
        return True
            
        
class BooleanParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description = '', **kwargs):
        super(BooleanParameter,self).__init__(id,paramflag,name,description, **kwargs)
        
        #defaultinstance
        self.reverse = False
        for key, value in kwargs.items():
            if key == 'reverse': 
                self.reverse = value  #Option gets outputted when option is NOT checked


    def compilearg(self, value):
        if self.reverse: value = not value
        if value:
            return self.paramflag  
        else:
            return ""



class StringParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description = '', **kwargs):
        self.maxlength = 0 #unlimited
        super(StringParameter,self).__init__(id,paramflag,name,description, **kwargs)

        #defaults
        if not 'default' in kwargs and not 'value' in kwargs:
            self.value = ""
        for key, value in kwargs.items():
            if key == 'default': 
                self.value = value  
            elif key == 'maxlength': 
                self.maxlength = int(value)

    def validate(self,value):
        self.error = None
        if self.maxlength > 0 and len(value) > self.maxlength:
            self.error = "Text too long, exceeding maximum of " + str(self.maxlength) + " characters allowed"
            return False
        else:
            return True            

    def compilearg(self, value):
        if value.find(" ") >= 0 or value.find(";") >= 0:            
            value = value.replace('"',r'\"')
            value = '"' + value + '"' #wrap in quotes
        return super(StringParameter,self).compilearg(value)


class ChoiceParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description, **kwargs):    
        if not 'choices' in kwargs:
            raise Exception("No parameter choices specified for parameter " + ID + "!")
        self.choices = [] #list of key,value tuples
        for x in kwargs['choices']:
            if not isinstance(x,tuple) or len(x) != 2:
                self.choices.append( (x,x) ) #list of two tuples
            else:
                self.choices.append(x) #list of two tuples

        super(ChoiceParameter,self).__init__(id,paramflag,name,description, **kwargs)

        #defaults
        self.delimiter = ","
        self.showall = False
        self.multi = False
        if not 'value' in kwargs and not 'default' in kwargs:
            self.value = self.choices[0][0] #no default specified, first choice is default
                
        for key, value in kwargs.items():
            if key == 'multi': 
                self.multi = value #boolean 
            elif key == 'showall': 
                self.showall = value #show all options at once (radio instead of a pull down) 
            elif key == 'delimiter': 
                self.delimiter = value #char

    def validate(self,values):
        self.error = None
        if not isinstance(values,list):
            values = [values]
        for v in values:
            if not v in [x[0] for x in self.choices]:
                self.error = "Selected value was not an option!"
                return False
        return True



    def compilearg(self, values): 
        """This method compiles the parameter into syntax that can be used on the shell, such as -paramflag=value"""
        if isinstance(values,list):
            value = self.delimiter.join(values)
        else:
            value = values
        if value.find(" ") >= 0:
            value = '"' + value + '"' #wrap all in quotes
        return super(ChoiceParameter,self).compilearg(value)

    def xml(self):
        """This methods renders an XML representation of this parameter, along with 
        its selected value, and feedback on validation errors"""
        xml = "<" + self.__class__.__name__
        xml += ' id="'+self.id + '"'
        xml += ' name="'+self.name + '"'
        xml += ' description="'+self.description + '"'
        for key, value in self.kwargs.items():    
            if key != 'choices' and key != 'default':
                if isinstance(value, bool):
                    xml += ' ' + key + '="' + str(int(value))+ '"'                    
                elif isinstance(value, list):
                    xml += ' ' + key + '="'+",".join(value)+ '"'        
                else:
                    xml += ' ' + key + '="'+value+ '"'
        if self.error:
             xml += ' error="'+self.error + '"'               
        xml += ">"
        for key, value in self.choices:
            if self.value == key or (isinstance(self.value ,list) and key in self.value):
                xml += " <choice id=\""+key+"\" selected=\"1\">" + value + "</choice>"        
            else:
                xml += " <choice id=\""+key+"\">" + value + "</choice>"
        xml += "</" + self.__class__.__name__ + ">"
        return xml

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.multi:
            found = False
            values = []
            for choicekey in [x[0] for x in self.choices]:
                if self.id+'['+choicekey+']' in postdata:
                    found = True
                    if postdata[self.id+'['+choicekey+']']:
                        values.append(choicekey)
            if not found: 
                return False
            else:
                return values
        else:
            if self.id in postdata and postdata[self.id]:
                return postdata[self.id]     


class TextParameter(StringParameter): #TextArea based
    def __init__(self, id, paramflag, name, description = '', **kwargs):
        super(TextParameter,self).__init__(id,paramflag,name,description, **kwargs)

    #def compilearg(self, value):
    #    return super(TextParameter,self).compilearg(value)

    def compilearg(self, value):
        if value.find(" ") >= 0 or value.find(";") >= 0:            
            value = value.replace('"',r'\"')
            value = '"' + value + '"' #wrap in quotes
        return super(TextParameter,self).compilearg(value)

class IntegerParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description = '', **kwargs):
        self.minvalue = 0
        self.maxvalue = 0 #unlimited

        super(IntegerParameter,self).__init__(id,paramflag,name,description, **kwargs)
        
        
        #defaults
        if not 'default' in kwargs and not 'value' in kwargs:
            self.value = 0
        for key, value in kwargs.items():
            if key == 'minvalue': 
                self.minvalue = int(value)
            elif key == 'maxvalue': 
                self.maxvalue = int(value)

    def validate(self, value):
        self.error = None
        try:
            value = int(value)
        except:
            self.error = "Not a valid number, note that no decimals are allowed"
            return False
        if ((self.maxvalue < self.minvalue) or ((value >= self.minvalue) and  (value <= self.maxvalue))):
            return True
        else:
            self.error = "Number must be a whole number between " + str(self.minvalue) + " and " + str(self.maxvalue)
            return False


class FloatParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description = '', **kwargs):
        self.minvalue = 0.0
        self.maxvalue = -1.0 #unlimited if maxvalue < minvalue

        super(FloatParameter,self).__init__(id,paramflag,name,description, **kwargs)
                
        #defaults
        if not 'default' in kwargs and not 'value' in kwargs:
            self.value = 0.0
        for key, value in kwargs.items():
            if key == 'minvalue': 
                self.minvalue = float(value)
            elif key == 'maxvalue': 
                self.maxvalue = float(value)

    def validate(self, value):
        self.error = None
        try:
            value = float(value)
        except:
            self.error = "Not a valid number"
            return False
        if ((self.maxvalue < self.minvalue) or ((value >= self.minvalue) and  (value <= self.maxvalue))):
            return True
        else:
            self.error = "Number must be between " + str(self.minvalue) + " and " + str(self.maxvalue)
            return False
        

