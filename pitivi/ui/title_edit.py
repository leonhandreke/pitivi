
import gtk
import pango

from pitivi.ui.glade import GladeWindow
from pitivi.ui.title_preview import TitlePreview

def set_current_color(color_selection, color):
    color_selection.props.current_color = gtk.gdk.Color(
        int(color[0] * 65535.0), int(color[1] * 65535.0), int(color[2] * 65535.0))
    color_selection.props.current_alpha = int(color[3] * 65535.0)

alignments = [
        (0.0, 0.0), (0.5, 0.0), (1.0, 0.0),
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5),
        (0.0, 1.0), (0.5, 1.0), (1.0, 1.0)]

class TitleEditDialog(GladeWindow):
    glade_file = "title_edit.glade"

    def __init__(self, **kw):
        GladeWindow.__init__(self)

        self.text = kw.get('text', 'Hello, World!')
        self.font = kw.get('font', 'Sans')
        self.text_size = kw.get('text_size', 64)
        self.bg_color = kw.get('bg_color', (0, 0, 0, 1))
        self.fg_color = kw.get('fg_color', (1, 1, 1, 1))
        # Centre alignment is the default.
        self.x_alignment = 0.5
        self.y_alignment = 0.5
        self.justification = gtk.JUSTIFY_LEFT

        self.preview = TitlePreview(text=self.text)
        self.widgets['preview_frame'].add(self.preview)
        # XXX: set preview_frame's aspect ratio
        self.preview.set_size_request(400, 300)

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
            self.preview.update_color(self.fg_color_string, self.bg_color_string)

    def _run_font_dialog(self, _button):
        dialog = gtk.Dialog()
        content_area = dialog.get_content_area()

        font_selection = gtk.FontSelection()
        content_area.pack_start(font_selection, True)
        font_selection.props.font_name = '%s %d' % (self.font, self.text_size)

        dialog.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_OK:
            (self.font, size_str) = \
                font_selection.props.font_name.rsplit(None, 1)
            self.text_size = int(size_str)
            self.preview.update_font(font_selection.get_font_name())

    def _set_bg_color(self, color_selection):
        self.bg_color = ((color_selection.props.current_color.red_float),
            (color_selection.props.current_color.green_float),
            (color_selection.props.current_color.blue_float),
            (color_selection.props.current_alpha / 65535.0))
        self.bg_color_string = color_selection.props.current_color.to_string()

    def _set_fg_color(self, color_selection):
        self.fg_color = ((color_selection.props.current_color.red_float),
            (color_selection.props.current_color.green_float),
            (color_selection.props.current_color.blue_float),
            (color_selection.props.current_alpha / 65535.0))
        self.fg_color_string = color_selection.props.current_color.to_string()

    def get_fg_color_bgra(self):
        # The color-order has to be reversed for cairo.Context
        # BGRA
        return self.fg_color[2], self.fg_color[1], self.fg_color[0], self.fg_color[3]     

    def get_bg_color_bgra(self):
        # The color-order has to be reversed for cairo.Context
        # BGRA
        return self.bg_color[2], self.bg_color[1], self.bg_color[0], self.bg_color[3] 

    def _buffer_changed(self, buffer):
        text = buffer.get_text(*buffer.get_bounds())
        self.preview.props.text = text

    def set(self, **kw):
        self.__dict__.update(kw)

    def _copy_to_dialog(self):
        buffer = self.widgets['textview'].props.buffer
        buffer.set_text(self.text)

    def _copy_from_dialog(self):
        buffer = self.widgets['textview'].props.buffer
        self.text = buffer.get_text(*buffer.get_bounds())
        self.x_alignment = self.preview.x
        self.y_alignment = self.preview.y

    def run(self):
        self._copy_to_dialog()
        self.window.show_all()
        response = gtk.Dialog.run(self.window)
        self._copy_from_dialog()
        return response

    def _justify_text(self, _button, justification):
        if justification == gtk.JUSTIFY_LEFT or gtk.JUSTIFY_RIGHT or gtk.JUSTIFY_CENTER:
            self.widgets['textview'].set_justification(justification)
            if justification == gtk.JUSTIFY_LEFT:
                self.preview.update_justification(_convert_to_pango_justification(justification))
            elif justification == gtk.JUSTIFY_RIGHT:
                self.preview.update_justification(_convert_to_pango_justification(justification))
            elif justification == gtk.JUSTIFY_CENTER:
                self.preview.update_justification(_convert_to_pango_justification(justification))
            
            self.justification = justification
        return

    def get_justification_pango(self):
        return _convert_to_pango_justification(self.justification)

def _convert_to_pango_justification(gtk_justification):
    if gtk_justification == gtk.JUSTIFY_LEFT:
        return pango.ALIGN_LEFT
    elif gtk_justification == gtk.JUSTIFY_RIGHT:
        return pango.ALIGN_RIGHT
    elif gtk_justification == gtk.JUSTIFY_CENTER:
        return pango.ALIGN_CENTER

