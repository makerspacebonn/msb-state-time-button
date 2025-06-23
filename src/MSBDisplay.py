import time

from enhanced_display import Enhanced_Display


class MSBDisplay(Enhanced_Display):

    def __init__(self, address=0x3C,bus=None, freq=None, sda=None, scl=None, asw=None, i2c=None, display=None):
        Enhanced_Display.__init__(self, address,bus, freq, sda, scl, asw, i2c, display)
        self.load_fonts(['tiny', 'largeNum', 'tiny','text-18'])
        self.setContrast(255)

    def logo(self):
        self.load_bpm('msb.pbm')
        self.show()

    def message(self, message, message2 = ''):
        self.fill(0)
        self.load_bpm('msb1.pbm')
        self.select_font('tiny')
        self.text(message, 0, 55, horiz_align=1)
        self.text(message2, 0, 55, horiz_align=1)
        self.show()
        time.sleep(0.3)

    def status(self, time, msb_status):
        self.fill(0)
        self.setContrast(255)
        self.select_font('text-18')
        self.text(time, 0, 0, horiz_align=2)
        if msb_status:
            self.load_bpm('msb2.pbm', 0, 0)
            self.text('offen' if msb_status['open'] else 'zu', 0, 22, c=2, horiz_align=2)
            if ('openUntil' in msb_status):
                self.text('bis ' + msb_status['openUntil'], 0, 44 , horiz_align=2)


        self.show()

    def selectTime(self, time):
        self.setContrast(255)
        self.fill(0)
        self.select_font('tiny')
        self.text('offen bis:', 0, 0, horiz_align=1)
        self.select_font('largeNum')
        self.text(time, 0, 10, horiz_align=1)
        self.show()