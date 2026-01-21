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

    def screensaver(self, frame, msb_status=None):
        """
        Display bouncing logo with status to prevent OLED burn-in.
        Frame counter determines position.
        """
        self.setContrast(50)  # Dim the display
        self.fill(0)

        # Content block dimensions
        # With time: icon (16) + text at x+18 (~30px) = ~50px total
        # Without time: just logo (14) + icon (16)
        has_time = msb_status and msb_status.get('openUntil')
        block_width = 50 if has_time else 16
        block_height = 36

        # Calculate bounce area
        max_x = self.width - block_width
        max_y = self.height - block_height

        # Slow down animation: divide frame by 4 for smoother movement
        slow_frame = frame // 4

        # Bouncing animation using frame counter (reduced speed)
        x = slow_frame % (max_x * 2) if max_x > 0 else 0
        y = (slow_frame * 2 // 3) % (max_y * 2) if max_y > 0 else 0

        # Bounce back when hitting edges
        if x >= max_x and max_x > 0:
            x = max_x * 2 - x
        if y >= max_y and max_y > 0:
            y = max_y * 2 - y

        # Ensure bounds
        x = int(max(0, min(max_x, x)))
        y = int(max(0, min(max_y, y)))

        # Draw small logo (14x16)
        self.load_bpm('msb-small.pbm', x, y)

        # Draw status with padlock icon (moves with logo)
        if msb_status:
            icon = 'lock-open.pbm' if msb_status.get('open') else 'lock-closed.pbm'
            self.load_bpm(icon, x, y + 20)

            # Show closing time next to icon if set
            if msb_status.get('openUntil'):
                self.select_font('tiny')
                self.text(msb_status['openUntil'], x + 18, y + 24, horiz_align=0)

        self.show()