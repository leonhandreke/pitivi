
import gtk
import pango

from pitivi.ui.glade import GladeWindow
from pitivi.ui.title_preview import TitlePreview

def set_current_color(color_selection, color):
    """" Set color as the selected color in GTK color_selector.

    Keyword arguments:
    color_selection -- gtk.ColorSelection
    color -- tuple with four values (RGBA) Range: 0.0 - 1.0
    """
    color_selection.props.current_color = gtk.gdk.Color(
        int(color[0] * 65535), int(color[1] * 65535), int(color[2] * 65535))
    color_selection.props.current_alpha = int(color[3] * 65535)

def _convert_to_pango_justification(gtk_justification):
    """Convert gtk alignment to pango alignment.
    
    Keyword arguments:
    gtk_justification -- one of three static vars: 
    (gtk.JUSTIFY_LEFT, gtk.JUSTIFY_RIGHT, gtk.JUSTIFY_CENTER)
    """
    if gtk_justification == gtk.JUSTIFY_LEFT:
        return pango.ALIGN_LEFT
    elif gtk_justification == gtk.JUSTIFY_RIGHT:
        return pango.ALIGN_RIGHT
    elif gtk_justification == gtk.JUSTIFY_CENTER:
        return pango.ALIGN_CENTER

class TitleEditDialog(GladeWindow):
    glade_file = "title_edit.glade"

    def __init__(self, project, **kw):
        GladeWindow.__init__(self)
        settings = project.getSettings()
        self.text = kw.get('text', 'Hello, World!')
        self.font_name = kw.get('fontname', 'Sans 24')
        self.bg_color = kw.get('bg_color', (0, 0, 0, 1))
        self.fg_color = kw.get('fg_color', (1, 1, 1, 1))
        self.text_position_x = None
        self.text_position_y = None
        self.justification = gtk.JUSTIFY_LEFT

        self.preview = TitlePreview(text=self.text, 
                font_name=self.font_name, 
                text_position_x=self.text_position_x,
                text_position_y=self.text_position_y,
                videowidth=settings.videowidth, 
                videoheight=settings.videoheight)
        self.widgets['preview_frame'].add(self.preview)
        #self.preview.set_project_size(settings.videowidth, settings.videoheight)
        self.preview.set_size_request( int(300.0*(float(settings.videowidth)/float(settings.videoheight))), 300)


        self.widgets['color_button'].connect('clicked', self._run_color_dialog)
        self.widgets['font_button'].connect('clicked', self._run_font_dialog)
        self.widgets['align_left_button'].connect('clicked', self._justify_text, gtk.JUSTIFY_LEFT)
        self.widgets['align_center_button'].connect('clicked', self._justify_text, gtk.JUSTIFY_CENTER)
        self.widgets['align_right_button'].connect('clicked', self._justify_text, gtk.JUSTIFY_RIGHT)

        buffer = self.widgets['textview'].get_buffer()
        buffer.connect('changed', self._buffer_changed)

        # Hack: GladeWindow hides TitleEditDialog's run() with gtk.Dialog's;
        # undo that.
        del self.run

    def _run_color_dialog(self, _button):
        """Show color selection dialog."""
        dialog = gtk.Dialog()
        content_area = dialog.get_content_area()

        fg_frame = gtk.Frame("Text color")
        fg_color_selection = gtk.ColorSelection()
        fg_color_selection.props.has_opacity_control = True
        set_current_color(fg_color_selection, self.fg_color)

        bg_frame = gtk.Frame("Background color")
        bg_color_selection = gtk.ColorSelection()
        bg_color_selection.props.has_opacity_control = True
        set_current_color(bg_color_selection, self.bg_color)

        fg_frame.add(fg_color_selection)
        bg_frame.add(bg_color_selection)
        content_area.pack_start(fg_frame, True)
        content_area.pack_start(bg_frame, True)
        dialog.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            self._set_fg_color(fg_color_selection)
            self._set_bg_color(bg_color_selection)
            self.preview.update_color(self.get_fg_color_rgba(), self.get_bg_color_rgba())

    def _run_font_dialog(self, _button):
        """Show font selection dialog."""
        dialog = gtk.Dialog()
        content_area = dialog.get_content_area()

        font_selection = gtk.FontSelection()
        content_area.pack_start(font_selection, True)
        font_selection.props.font_name = self.font_name

        dialog.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            self.font_name = font_selection.get_font_name()
            self.preview.set_font(font_selection.get_font_name())

    def _set_bg_color(self, color_selection):
        """Save color selected with gtk.ColorSelection as the background color.

            Keyword arguments:
            color_selection -- gtk.ColorSelection

            Color is saved both as gtk.gdk.Color.to_string and 
            as a tuple with four values (RGBA).
        """
        self.bg_color = ((color_selection.props.current_color.red_float),
            (color_selection.props.current_color.green_float),
            (color_selection.props.current_color.blue_float),
            (color_selection.props.current_alpha / 65535.0))
        self.bg_color_string = color_selection.props.current_color.to_string()

    def _set_fg_color(self, color_selection):
        """Save color selected with gtk.ColorSelection as the foreground color.

            Keyword arguments:
            color_selection -- gtk.ColorSelection
            
            Color is saved both as gtk.gdk.Color.to_string and 
            as a tuple with four values (RGBA).
        """
        self.fg_color = ((color_selection.props.current_color.red_float),
            (color_selection.props.current_color.green_float),
            (color_selection.props.current_color.blue_float),
            (color_selection.props.current_alpha / 65535.0))
        self.fg_color_string = color_selection.props.current_color.to_string()

    def get_fg_color_argb(self):
        """Get the background color as a tuple with four values (ARGB).
        
        Values range: 0.0 - 1.0"""
        return self.fg_color[2], self.fg_color[1], self.fg_color[0], self.fg_color[3]     

    def get_bg_color_argb(self):
        """Get the foreground color as a tuple with four values (ARGB).

        Values range: 0.0 - 1.0"""
        return self.bg_color[2], self.bg_color[1], self.bg_color[0], self.bg_color[3] 
    
    def get_fg_color_rgba(self):
        """Get the background color as a 32bit number (RGBA)."""
        return (int(self.fg_color[3] * 255) + int(self.fg_color[2] * 255)*pow(2,8) + 
            int(self.fg_color[1] * 255)*pow(2,16) + int(self.fg_color[0] * 255)*pow(2,24))

    def get_bg_color_rgba(self):
        """Get the foreground color as a 32bit number (RGBA)."""
        return (int(self.bg_color[3] * 255) + int(self.bg_color[2] * 255)*pow(2,8) + 
            int(self.bg_color[1] * 255)*pow(2,16) + int(self.bg_color[0] * 255)*pow(2,24))

    def _buffer_changed(self, buffer):
        """Update text in preview box to correspond to buffer."""
        text = buffer.get_text(*buffer.get_bounds())
        self.preview.set_text(text)

    def set(self, **kw):
        self.__dict__.update(kw)

    def _copy_to_dialog(self):
        buffer = self.widgets['textview'].props.buffer
        buffer.set_text(self.text)

    def _copy_from_dialog(self):
        """Put last changes from dialog into variables."""
        buffer = self.widgets['textview'].props.buffer
        self.text = buffer.get_text(*buffer.get_bounds())
        self.text_position_x = self.preview.text_position_x
        self.text_position_y = self.preview.text_position_y

    def run(self):
        """Show TitleEdit dialog."""
        self._copy_to_dialog()
        self.window.show_all()
        response = gtk.Dialog.run(self.window)
        self._copy_from_dialog()
        return response

    def _justify_text(self, _button, justification):
        """Justify/align text.
        
            Keyword arguments:
            justification -- the justification, 
            one of three static vars (gtk.JUSTIFY_LEFT, gtk.JUSTIFY_RIGHT, gtk.JUSTIFY_CENTER)  
        """
        if justification == gtk.JUSTIFY_LEFT or gtk.JUSTIFY_RIGHT or gtk.JUSTIFY_CENTER:
            self.justification = justification
            if justification == gtk.JUSTIFY_LEFT:
                self.preview.update_justification(self.get_justification_pango())
            elif justification == gtk.JUSTIFY_RIGHT:
                self.preview.update_justification(self.get_justification_pango())
            elif justification == gtk.JUSTIFY_CENTER:
                self.preview.update_justification(self.get_justification_pango())
            
            
        return

    def get_justification_pango(self):
        """Return text justification/alignment inside textbox in pango compliant format."""
        return _convert_to_pango_justification(self.justification)

    def get_font_name(self):
        return self.font_name

