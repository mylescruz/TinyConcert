from concert import *
import re

# Concerts dictionary constructor
class Concerts: 
    def __init__(self):
        self.concertsDict = {}

        with open("data/concerts/concerts.txt") as f:        
            while line := f.readline():
                concertData = line.split("|")
                self.concert = Concert(concertData[0],concertData[1],concertData[2],concertData[3])
                self.concertsDict.update(self.process(self.concert))

    def process(self, concert):
        concertsDict = {}
        concertsDict[concert.getDate()] = concert
        return concertsDict

