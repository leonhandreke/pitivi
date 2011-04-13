
# XXX: allow centering the text horizontally and vertically

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

    def __init__(self, text, font_name, text_position_x, text_position_y, videowidth, videoheight):
        gtk.EventBox.__init__(self)
        self.add_events(
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.BUTTON1_MOTION_MASK)
        self.text = text
        self.project_width = videowidth 
        self.project_height = videoheight
        self.last_x = None
        self.last_y = None

        self.canvas = goocanvas.Canvas()
        self.canvas.props.background_color = 'black'
        self.scale = 1
        self.mouse_over = False
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

        if text_position_x is None:
            self.text_position_x = (self.project_width - text_size(self.text_item)[0])/ 2
        else:
            self.text_position_x = text_position_x
        if text_position_y is None:
            self.text_position_y = (self.project_height - text_size(self.text_item)[1]) / 2
        else:
            self.text_position_y

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
        self.connect('size-allocate', self.size_allocate)

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
        self._change_cursor(event)

        if self.last_x is None:
            return False
 
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        self.update_position(dx, dy)
        self.last_x = event.x
        self.last_y = event.y

    def _change_cursor(self, event):
        bounds = self.group.get_bounds()
        if ((bounds.x1 <= event.x/self.scale <= bounds.x2) and
            (bounds.y1 <= event.y/self.scale <= bounds.y2)):
            if self.mouse_over == False:
                self.mouse_over = True
                self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
        else:
            if self.mouse_over == True and self.last_x is None:
                self.mouse_over = False
                self.window.set_cursor(None)

    def update_justification(self, justification):
        """Update justification/alignment of text inside text box.
    
        Keyword arguments:
        justification -- Pango Alignment Constants
        """
        self.text_item.props.alignment = justification    
    
    def set_font(self, font_name):
        """Update text font in the preview box.

        Keyword arguments:
        font_name -- usualy from gtk.FontSelection.get_font_name()
        """
        self.text_item.props.font = font_name
        self._update_text()

    def set_text(self, text):
        self.text_item.props.text = text
        self._update_text()    

    def _update_text(self):
        """Update the box sourounding the text"""
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

    """def set_project_size(self, width, height):
        self.project_width = width
        self.project_height = height"""

    def size_allocate(self, widget, allocation):
        self.scale = float(allocation.height)/float(self.project_height)
        self.canvas.set_scale(self.scale)
        self.canvas.set_bounds(0, 0, self.project_width, self.project_height)

        self.background.props.height = self.project_height
        self.background.props.width = self.project_width
        self.chessboard.props.height = self.project_height
        self.chessboard.props.width = self.project_width

        chess_pixbuff = gtk.gdk.Pixbuf(colorspace=gtk.gdk.COLORSPACE_RGB,
            has_alpha=True, bits_per_sample=8, height=self.project_height, width=self.project_width)
        chess_pixbuff = chess_pixbuff.composite_color_simple(self.project_width, self.project_height,
                    gtk.gdk.INTERP_TILES, 255, 8, 0x777777, 0x999999)  
        self.chessboard.props.pixbuf = chess_pixbuff
        
        self.update_position(0, 0)

    def update_position(self, dx=0, dy=0):
        canvas_bounds = goocanvas.Bounds(0, 0, self.project_width, self.project_height)
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
        self.text_position_x = (self.group.get_bounds().x1  / self.project_width)
        self.text_position_y = (self.group.get_bounds().y1  / self.project_height)
        return False

