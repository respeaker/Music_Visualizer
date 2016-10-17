
import os
import re
import Queue

from PySide import QtGui
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

GObject.threads_init()
Gst.init(None)


class Spectrum(QtGui.QWidget):
    delay = 16

    def __init__(self, music):
        super(Spectrum, self).__init__()

        self.bars_number = 16
        self.bars = [1] * self.bars_number
        self.padding = 2
        self.resolution = 255

        self.setMinimumSize(240, 320)

        self.queue = Queue.Queue()

        player = Gst.ElementFactory.make('playbin', 'player')
        spectrum = Gst.ElementFactory.make('spectrum', 'spectrum')
        sink = Gst.ElementFactory.make('directsoundsink', 'sink')

        player.set_property('audio-sink', sink)

        spectrum.set_property('bands', 20)
        spectrum.set_property('interval', 100000000)
        spectrum.set_property('post-messages', True)
        spectrum.set_property('message-magnitude', True)

        player.set_property('audio-filter', spectrum)
        player.set_property('uri', 'file:///' + os.path.realpath(music))

        bus = player.get_bus()
        bus.add_signal_watch()

        # A message has been posted on the bus.
        # This signal is emitted from a GSource added to the mainloop.
        # this signal will only be emitted when there is a mainloop running.
        # bus.connect('message::element', self.on_message)

        # A message has been posted on the bus.
        # This signal is emitted from the thread that posted the message
        # so one has to be careful with locking.
        # Note: This signal will not be emitted by default,
        # you have to call gst_bus_enable_sync_message_emission() before.
        bus.connect('sync-message::element', self.on_message)

        bus.enable_sync_message_emission()
        # bus.set_sync_handler(self.sync_message_handler, None, None)

        player.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        struct = message.get_structure()
        if struct and struct.get_name() == 'spectrum':
            struct_str = struct.to_string()
            magnitude_str = re.match(r'.*magnitude=\(float\){(.*)}.*', struct_str)
            if magnitude_str:
                magnitude = map(float, magnitude_str.group(1).split(','))
                # print magnitude

                bars = [int(x * 10) + 600 for x in magnitude][2:-2]
                self.queue.put(bars)
                if self.queue.qsize() >= self.delay:
                    bars = self.queue.get()
                    self.setBars(bars)

    # def sync_message_handler(self, bus, message, user_data, unknown):
    #     struct = message.get_structure()
    #     if struct and struct.get_name() == 'spectrum':
    #         struct_str = struct.to_string()
    #         magnitude_str = re.match(r'.*magnitude=\(float\){(.*)}.*', struct_str)
    #         if magnitude_str:
    #             magnitude = map(float, magnitude_str.group(1).split(','))
    #             # print magnitude
    #
    #             bars = [int(x * 10) + 600 for x in magnitude][2:-2]
    #             self.setBars(bars)
    #
    #     return 0

    def setBars(self, bars):
        # print(bars)
        self.bars_number = len(bars)
        for index, value in enumerate(bars):
            if value > self.resolution:
                bars[index] = self.resolution
        self.bars = bars
        self.update()

    def paintEvent(self, e):

        painter = QtGui.QPainter()
        painter.begin(self)
        self.drawBars(painter)
        painter.end()

    def drawBars(self, painter):
        size = self.size()
        width = size.width()
        height = size.height()

        bar_width = float(width - self.padding) / self.bars_number

        color = QtGui.QColor(0, 0, 0)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, width, height)
        for bar, value in enumerate(self.bars):
            bar_height = (height - self.padding) * value / self.resolution
            if not bar_height:
                bar_height = 1
            painter.setBrush(self.barColor(bar))
            painter.drawRect(
                bar * bar_width + self.padding,
                height - bar_height,
                bar_width - self.padding,
                bar_height - self.padding)

    def barColor(self, bar):
        position = int((bar + 0.5) * 255 / self.bars_number)
        return self.palette(position)

    def blue2red(self, position):
        position &= 0xFF
        if position < 128:
            return QtGui.QColor(0, position * 2, 255 - position * 2)
        else:
            position -= 128
            return QtGui.QColor(position * 2, 255 - position * 2, 0)

    palette = blue2red


def main():
    import sys

    if len(sys.argv) < 2:
        print('Usage: python {} music.mp3'.format(sys.argv[0]))
        sys.exit(1)

    app = QtGui.QApplication(sys.argv)
    spectrum = Spectrum(sys.argv[1])
    spectrum.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
