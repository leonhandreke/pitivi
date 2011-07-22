
# XXX: stop updating last_x/last_y when pointer is outside widget
# XXX: set cursor to indicate draggability when over text item
# XXX: allow centering the text horizontally and vertically
# XXX: maintain right margin position when text is right aligned

import gobject
import goocanvas
import gtk
import pango

from gettext import gettext as _

def print_bounds(b):
    print '<(%r, %r) (%r, %r)>' % (b.x1, b.y1, b.x2, b.y2)

def text_size(text):
    ink, logical = text.get_natural_extents()
    x1, y1, x2, y2 = [pango.PIXELS(x) for x in logical]
    return x2 - x1, y2 - y1

class TitlePreview(gtk.EventBox):
    PADDING = 1

    __gproperties__ = {
        'text': (
            gobject.TYPE_STRING, 'text', 'text', _('Hello'),
            gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'x': (
            gobject.TYPE_UINT, 'x position', 'x position', 0, 0xffff, 10,
            gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'y': (
            gobject.TYPE_UINT, 'y position', 'y position', 0, 0xffff, 10,
            gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'alignment': (
            gobject.TYPE_UINT, 'alignment', 'alignment', 0, 2, 0,
            gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'foreground-color': (
            gobject.TYPE_UINT, 'foreground color', 'foreground color',
            0, 0xffffffff, 0xffffffff,
            gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'background-color': (
            gobject.TYPE_UINT, 'background color', 'background color',
            0, 0xffffffff, 0,
            gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
    }

    def __init__(self, **kw):
        gtk.EventBox.__init__(self)
        self.add_events(
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.BUTTON1_MOTION_MASK)

        self.set_properties(**kw)
        self.last_x = None
        self.last_y = None

        self.canvas = goocanvas.Canvas()
        self.canvas.props.background_color = 'black'

        self.text_item = goocanvas.Text(
            fill_color_rgba=0xffffffff,
            x=self.PADDING,
            y=self.PADDING,
            font='Sans Bold 24',
            text=self.text)

        text_w, text_h = text_size(self.text_item)

        # XXX: Ideally we'd invert the colour underneath the outline.
        self.rect1 = goocanvas.Rect(
            stroke_color_rgba=0xffffffff,
            width=text_w + 2 * self.PADDING,
            height=text_h + 2 * self.PADDING,
            radius_x=0,
            radius_y=0)
        self.rect2 = goocanvas.Rect(
            stroke_color_rgba=0x000000ff,
            line_dash=goocanvas.LineDash([3.0, 3.0]),
            width=text_w + 2 * self.PADDING,
            height=text_h + 2 * self.PADDING,
            radius_x=0,
            radius_y=0)

        self.group = goocanvas.Group()
        self.group.add_child(self.rect1)
        self.group.add_child(self.rect2)
        self.group.add_child(self.text_item)
        root = self.canvas.get_root_item()
        root.add_child(self.group)
        self.add(self.canvas)

        #print (self.x, self.y)
        #print (self.group.get_bounds().x1, self.group.get_bounds().y1)
        self.group.translate(self.props.x, self.props.y)
        #print (self.group.get_bounds().x1, self.group.get_bounds().y1)

        self.connect('button-press-event', self.button_press)
        self.connect('button-release-event', self.button_release)
        self.connect('motion-notify-event', self.motion_notify)
        self.connect('size-allocate', lambda w, a: self.update_position(0, 0))

    def do_get_property(self, property):
        if property.name == 'text':
            return self.text
        elif property.name == 'x':
            return self.x
        elif property.name == 'y':
            return self.y
        elif property.name == 'alignment':
            return self.alignment
        else:
            raise AttributeError

    def do_set_property(self, property, value):
        if property.name == 'text':
            self.text = value

            if hasattr(self, 'text_item'):
                text_w0, text_h0 = text_size(self.text_item)
                self.text_item.props.text = value
                text_w1, text_h1 = text_size(self.text_item)

                # Update rectangle sizes to match text.
                self.rect1.props.width = text_w1 + 2 * self.PADDING
                self.rect1.props.height = text_h1 + 2 * self.PADDING
                self.rect2.props.width = text_w1 + 2 * self.PADDING
                self.rect2.props.height = text_h1 + 2 * self.PADDING

                self.update_position(0, 0)
        elif property.name == 'x':
            # XXX: sync to canvas items
            self.x = value
        elif property.name == 'y':
            # XXX: sync to canvas items
            self.y = value
        elif property.name == 'alignment':
            self.alignment = value

            if hasattr(self, 'text_item'):
                self.text_item.props.alignment = value
        else:
            raise AttributeError(property.name)

    def button_press(self, widget, event):
        bounds = self.group.get_bounds()

        if ((bounds.x1 <= event.x <= bounds.x2) and
            (bounds.y1 <= event.y <= bounds.y2)):
            self.last_x = event.x
            self.last_y = event.y

        return False

    def button_release(self, widget, event):
        self.last_x = None
        self.last_y = None
        return False

    def motion_notify(self, widget, event):
        if self.last_x is None:
            return False

        dx = event.x - self.last_x
        dy = event.y - self.last_y
        self.update_position(dx, dy)
        self.last_x = event.x
        self.last_y = event.y

    def update_position(self, dx, dy):
        #print 'before', (dx, dy)
        alloc = self.canvas.get_allocation()
        canvas_bounds = goocanvas.Bounds(0, 0, alloc.width, alloc.height)
        group_bounds = self.group.get_bounds()
        #print_bounds(canvas_bounds)
        #print_bounds(group_bounds)
        canvas_width = canvas_bounds.x2 - canvas_bounds.x1
        canvas_height = canvas_bounds.y2 - canvas_bounds.y1
        group_width = group_bounds.x2 - group_bounds.x1
        group_height = group_bounds.y2 - group_bounds.y1

        if canvas_height == 1:
            # This happens when starting up. Avoid moving the text around
            # before we get a proper size allocation.
            return

        if group_width > canvas_width:
            dx = (canvas_width - group_width) / 2 - group_bounds.x1
        elif group_bounds.x1 + dx < canvas_bounds.x1:
            dx = canvas_bounds.x1 - group_bounds.x1
        elif group_bounds.x2 + dx > canvas_bounds.x2:
            dx = canvas_bounds.x2 - group_bounds.x2

        if group_height > canvas_height:
            dy = (canvas_height - group_height) / 2 - group_bounds.y1
        elif group_bounds.y1 + dy < canvas_bounds.y1:
            dy = canvas_bounds.y1 - group_bounds.y1
        elif group_bounds.y2 + dy > canvas_bounds.y2:
            dy = canvas_bounds.y2 - group_bounds.y2

        self.group.translate(dx, dy)
        #print 'after', (dx, dy)
        #print
        #print
        return False

