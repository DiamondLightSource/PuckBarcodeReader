try:
    import winsound
except ImportError:
    import os
    def playsound(frequency, duration):
        #apt-get install beep
        os.system('beep -f %s -l %s' % (frequency, duration))
else:
    def playsound(frequency, duration):
        winsound.Beep(frequency, duration)

class Beeper:
    @staticmethod
    def good_beep(frequency=4000, duration=500):
        playsound(frequency, duration)
        
    def bad_beep(frequency=500, duration=500):
        playsound(frequency, duration)