
# XXX: stop updating last_x/last_y when pointer is outside widget
# XXX: set cursor to indicate draggability when over text item
# XXX: allow centering the text horizontally and vertically
# XXX: maintain right margin position when text is right aligned

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

    def __init__(self, text, font_name, text_position_x, text_position_y):
        gtk.EventBox.__init__(self)
        self.add_events(
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.BUTTON1_MOTION_MASK)

        self.text = text
        self.text_position_x = text_position_x
        self.text_position_y = text_position_y
        self.last_x = None
        self.last_y = None
        self.canvas = goocanvas.Canvas()
        self.canvas.props.background_color = 'black'
        self.scale = 1
        self.text_item = goocanvas.Text(
            fill_color_rgba=0xffffffff,
            x=self.PADDING,
            y=self.PADDING,
            font=font_name,
            text=self.text,
            use_markup=True)
        text_w, text_h = text_size(self.text_item)
        self.background = goocanvas.Rect(
            radius_x=0,
            radius_y=0,
            fill_color_rgba=0x000000ff)
        self.chessboard = goocanvas.Image()
        #chessboard is the background that shows up when the background becomes transparent
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
        root.add_child(self.chessboard)
        root.add_child(self.background)
        root.add_child(self.group)
        self.add(self.canvas)

        self.group.translate(self.text_position_x, self.text_position_y)

        self.connect('button-press-event', self.button_press)
        self.connect('button-release-event', self.button_release)
        self.connect('motion-notify-event', self.motion_notify)
        self.connect('size-allocate', self.size_allocate )

    def set_text(self, text):
        if hasattr(self, 'text_item'):
            text_w0, text_h0 = text_size(self.text_item)
            self.text_item.props.text = text
            text_w1, text_h1 = text_size(self.text_item)
            # Update rectangle sizes to match text.
            self.rect1.props.width = text_w1 + 2 * self.PADDING
            self.rect1.props.height = text_h1 + 2 * self.PADDING
            self.rect2.props.width = text_w1 + 2 * self.PADDING
            self.rect2.props.height = text_h1 + 2 * self.PADDING
            self.update_position(0, 0)

    def button_press(self, widget, event):
        bounds = self.group.get_bounds()
        if ((bounds.x1 <= event.x/self.scale <= bounds.x2) and
            (bounds.y1 <= event.y/self.scale <= bounds.y2)):
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

    def update_justification(self, justification):
        """Update justification/alignment of text inside text box.
    
        Keyword arguments:
        justification -- Pango Alignment Constants
        """
        self.text_item.props.alignment = justification    
    
    def update_font(self, font_name):
        """Update text font in the preview box.

        Keyword arguments:
        font_name -- usualy from gtk.FontSelection.get_font_name()
        """
        self.text_item.props.font = font_name
        if hasattr(self, 'text_item'):
            text_w1, text_h1 = text_size(self.text_item)

            # Update rectangle sizes to match new font type or font size.
            self.rect1.props.width = text_w1 + 2 * self.PADDING
            self.rect1.props.height = text_h1 + 2 * self.PADDING
            self.rect2.props.width = text_w1 + 2 * self.PADDING
            self.rect2.props.height = text_h1 + 2 * self.PADDING

            self.update_position(0, 0)

    def update_color(self, fg_color=None, bg_color=None):
        """Update color of text and background in the preview box.
        
        Keyword arguments:
        fg_color_string -- 32bit color RGBA
        fg_color_string -- 32bit color RGBA
        """
        if fg_color != None:
            self.text_item.props.fill_color_rgba = fg_color
        if bg_color != None:
            self.background.props.fill_color_rgba = bg_color

    def set_preset_size(self, width, height):
        self.preset_width = width
        self.preset_height = height

    def _get_preset_size(self):
        return gtk.gdk.Rectangle(x=0, y=0, width=self.preset_width, height=self.preset_height)

    def size_allocate(self, widget, allocation):
        bounds = self.canvas.get_bounds()
        #print_bounds(bounds)
        self.scale = float(allocation.height)/float(self.preset_height)
        self.canvas.set_scale(self.scale)
        self.canvas.set_bounds(0, 0, self.preset_width, self.preset_height)
        alloc_preset = self._get_preset_size()

        self.background.props.height = self.preset_height
        self.background.props.width = self.preset_width
        self.chessboard.props.height = self.preset_height
        self.chessboard.props.width = self.preset_width

        chess_pixbuff = gtk.gdk.Pixbuf(colorspace=gtk.gdk.COLORSPACE_RGB,
            has_alpha=True, bits_per_sample=8, height=self.preset_height, width=self.preset_width)
        chess_pixbuff = chess_pixbuff.composite_color_simple(self.preset_width, self.preset_height,
                    gtk.gdk.INTERP_TILES, 255, 8, 0x777777, 0x999999)  
        self.chessboard.props.pixbuf = chess_pixbuff
        
        #print_bounds(bounds)
        self.update_position(0, 0)

    def update_position(self, dx=0, dy=0):
        #print 'before', (dx, dy)
        alloc_preset = self._get_preset_size()
        canvas_bounds = goocanvas.Bounds(0, 0, alloc_preset.width, alloc_preset.height)
        group_bounds = self.group.get_bounds()
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

        self.group.translate(dx/self.scale, dy/self.scale)
        self.text_position_x = (self.group.get_bounds().x1  / alloc_preset.width)
        self.text_position_y = (self.group.get_bounds().y1  / alloc_preset.height)
        return False

