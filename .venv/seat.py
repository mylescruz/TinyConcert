from user import *

class Seat: 
    def __init__(self, row, seatNum, user, price, icon):
        self.row = row
        self.seatNum = seatNum
        self.user = user
        self.price = price
        self.icon = icon

    def getRow(self):
        return self.row

    def getSeatNumber(self):
        return self.seatNum

    def getUser(self):
        return self.user

    def getPrice(self):
        return self.price

    def getIcon(self):
        return self.icon