# APC UPS message
from mMessage import mMessage
import re
from pprint import pprint


class SimpleValue:
    def __init__(self, value):
        self.value = value

    def getValue(self):
        return self.value

    def __repr__(self):
        return 'SimpleValue(' + repr(self.value) + ')'


class LabeledValue:
    def __init__(self, value, label):
        self.value = value
        self.label = label

    def __repr__(self):
        return 'LabeledValue(' + repr(self.value) + ', ' + repr(self.label) + ')'

    def getValue(self):
        return self.value

    def getLabel(self):
        return self.label


class mApcMessage(mMessage):
    fields = {}
    labeledFields = ['LINEV', 'LOADPCT', 'BCHARGE', 'TIMELEFT', 'MBATTCHG', \
        'MINTIMEL', 'MAXTIME', 'LOTRANS', 'HITRANS', 'BATTV', 'TONBATT', \
        'CUMONBATT', 'NOMINV', 'NOMBATTV', 'NOMPOWER']


    def __init__(self, m):
        self.setDigest(m.getDigest())
        self.setEntropy(m.getEntropy())
        self.setCounter(m.getCounter())
        self.setData(m.getData())

        self.extractApcFields()


    def __repr__(self):
        value  = "mApcMessage('Digest': " + repr(self.getDigest()) + "\n"
        value += "  'Entropy': " + repr(self.getEntropy()) + "\n"
        value += "  'Counter': " + repr(self.getCounter()) + "\n"
        value += "  'Fields': {\n"

        for key, val in self.fields.iteritems():
            value += "    '" + key + "': " + repr(val) + "\n"

        value += "  }\n"
        value += ')'

        return value


    def extractApcFields(self):
        data = str(self.getData())

        # Split each line into a key and value
        for line in iter( data.splitlines() ):
            match = re.search('^([a-zA-Z0-9\s]*)\s*:\s(.*)$', line)

            # Make sure the match returned components
            if match.lastindex is not None:

                fieldName = match.group(1).strip()
                rawValue = match.group(2).strip()

                # If the field has a label, make it a labeledValue
                if fieldName in self.labeledFields:

                    # Check for empty value
                    if rawValue == '':
                        labeledValue = LabeledValue('','')

                    else:
                        valueMatch = re.search('^([^\s]*)\s(.*)$', rawValue)
                        labeledValue = LabeledValue(valueMatch.group(1), valueMatch.group(2))

                    self.fields[fieldName] = labeledValue

                # Field does not have a label, make it a SimpleValue
                else:
                    self.fields[fieldName] = SimpleValue(rawValue)

            else:
                #print "Error processing '{0}'".format(line)
                pass


    def getFieldValue(self, fieldName):
        if fieldName in self.fields:
            return self.fields[fieldName].getValue()

        else:
            raise KeyError("{0} is not in the available field list".format(fieldName))


    def getFieldLabel(self, fieldName):
        if fieldName not in self.fields:
            raise KeyError("{0} is not in the available field list".format(fieldName))

        if fieldName in self.labeledFields:
            return self.fields[fieldName].getLabel()

        else:
            return None
