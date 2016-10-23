# Message class

class mMessage:
    digest = ''
    entropy = ''
    counter = -1
    data = ''

    def __init__(self):
        pass

    def setDigest(self, digest):
        self.digest = digest

    def getDigest(self):
        return self.digest

    def setEntropy(self, entropy):
        self.entropy = entropy

    def getEntropy(self):
        return self.entropy

    def setCounter(self, counter):
        self.counter = counter

    def getCounter(self):
        return self.counter

    def setData(self, data):
        self.data = data

    def getData(self):
        return self.data

    def getMessageID(self):
        return str(self.getEntropy()) + str(self.getCounter())
