# # class definition written by Dr. Ben Geisler
# class Concerts():  
#     foo = 'bar' #member variable on Concerts class 

#     def __init__(self):  #this is construtor
#         self.concertsDict = {}
#         with open("data/concerts/concerts.txt") as f:        
#             while line := f.readline():
#                 self.concertsDict.update(self.process(line))

#     def process(self, line): #member function
#         concertsDict = {}
#         linedata = line.split("|")
#         # print(linedata)
#         # print(linedata[0])
#         # print(linedata[1])
#         # print(linedata[2])
#         concertsDict[linedata[0]] = linedata[1]        
#         return concertsDict
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

