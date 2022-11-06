# class definition written by Myles Cruz
class Concert: 
    musician = 'None'
    date = 'January 01, 2022'
    time = '8:00pm'
    image = 'concert.jpg'

    def __init__(self, date, musician, time, image):
        self.date = date
        self.musician = musician
        self.time = time
        self.image = image

    def getDate(self):
        return self.date

    def getMusician(self):
        return self.musician
    
    def getTime(self):
        return self.time

    def getImage(self):
        return self.image