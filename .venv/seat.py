from user import *

class Seat: 
    def __init__(self, row, number, user, price, icon, key):
        self.row = row
        self.number = number
        self.user = user
        self.price = price
        self.icon = icon
        self.key = key

    def getRow(self):
        return self.row

    def getNumber(self):
        return self.number

    def getUser(self):
        return self.user

    def getPrice(self):
        return self.price

    def getIcon(self):
        return self.icon

    def getKey(self):
        return self.key