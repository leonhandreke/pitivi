
import cairo
import pango
import pangocairo
import gobject
import gst

class TitleSource(gst.BaseSrc):
    __gsttemplates__ = (
        gst.PadTemplate("src",
                        gst.PAD_SRC,
                        gst.PAD_ALWAYS,
                        #gst.Caps("video/x-raw-rgb,depth=24,bpp=32"))
                        # XXX: hardcoded width and height
                        gst.Caps("video/x-raw-rgb,depth=32,bpp=32,width=720,height=576"))
        )

    def __init__(self, text='title',
            font_name='Sans 24',
            x_alignment=0.5,
            y_alignment=0.5,
            bg_color=None,
            fg_color=None,
            justification=pango.ALIGN_LEFT,
            project=None,
            width=720,
            height=576):
        #width and height is not yet used. Its hardcoded on line 15
        gst.BaseSrc.__init__(self)
        self.start = 0
        self.stop = gst.CLOCK_TIME_NONE
        self.curpos = 0
        # let's put the granularity at 10 msgs per second
        self.granularity = gst.SECOND / 10
        self.set_live(False)
        self.set_format(gst.FORMAT_TIME)

        self.text = text
        self.font_name = font_name
        self.x_alignment = x_alignment
        self.y_alignment = y_alignment
        self.bg_color = bg_color if bg_color is not None else (0, 0, 0, 1)
        self.fg_color = fg_color if fg_color is not None else (1, 1, 1, 1)
        self.justification = justification

    def do_create(self, offset, size):
        gst.debug("offset: %r, size:%r" % (offset, size))

        pad = self.get_pad('src')
        caps = pad.get_negotiated_caps()

        assert caps[0].has_field('width')
        assert caps[0].has_field('height')
        width, height = caps[0]['width'], caps[0]['height']

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)

        # background
        cr.set_source_rgba(*self.bg_color)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # text
        cr.set_source_rgba(*self.fg_color)
        pcr = pangocairo.CairoContext(cr)
        layout = pcr.create_layout()
        layout.set_font_description(pango.FontDescription(self.font_name))
        layout.set_markup(self.text)
        layout.set_alignment(self.justification)
        (ink, (x_bearing, y_bearing, t_width, t_height)) = \
            layout.get_pixel_extents()
        x = (width) * self.x_alignment - x_bearing
        y = (height) * self.y_alignment - y_bearing
        cr.move_to(x, y)
        pcr.show_layout(layout)

        b = gst.Buffer(surface.get_data())
        b.timestamp = self.curpos
        b.duration = self.granularity
        self.curpos += b.duration
        gst.debug("timestamp:%s" % gst.TIME_ARGS(b.timestamp))
        gst.debug("duration:%s" % gst.TIME_ARGS(b.duration))
        # set timestamps
        return gst.FLOW_OK, b

    def do_is_seekable(self):
        return True

    # FIXME : implement seeking
    def do_do_seek(self, segment):
        gst.debug("start %r stop %r" % (segment.start,
                                        segment.stop))
        self.start = segment.start
        self.curpos = segment.start
        self.stop = segment.stop
        return True

gobject.type_register(TitleSource)
