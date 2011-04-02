
import gtk

from pitivi.ui.glade import GladeWindow
from pitivi.ui.title_preview import TitlePreview

def get_color(c):
    return (
        c.props.current_color.red_float,
        c.props.current_color.green_float,
        c.props.current_color.blue_float,
        c.props.current_alpha / 65535.0)

def set_color(c, t):
    c.props.current_color = gtk.gdk.Color(
        int(t[0] * 65535.0), int(t[1] * 65535.0), int(t[2] * 65535.0))
    c.props.current_alpha = int(t[3] * 65535.0)

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

        self.preview = TitlePreview(text=self.text)
        self.widgets['preview_frame'].add(self.preview)
        # XXX: set preview_frame's aspect ratio
        self.preview.set_size_request(400, 300)

        self.widgets['color_button'].connect('clicked', self._run_color_dialog)
        self.widgets['font_button'].connect('clicked', self._run_font_dialog)

        buffer = self.widgets['textview'].get_buffer()
        buffer.connect('changed', self._buffer_changed)

        # Hack: GladeWindow hides TitleEditDialog's run() with gtk.Dialog's;
        # undo that.
        del self.run

    def _run_color_dialog(self, _button):
        dialog = gtk.Dialog()
        content_area = dialog.get_content_area()

        fg_frame = gtk.Frame("Foreground color")
        fg_color_selection = gtk.ColorSelection()
        fg_color_selection.props.has_opacity_control = True
        set_color(fg_color_selection, self.fg_color)

        bg_frame = gtk.Frame("Background color")
        bg_color_selection = gtk.ColorSelection()
        bg_color_selection.props.has_opacity_control = True
        set_color(bg_color_selection, self.bg_color)

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
            self.fg_color = get_color(fg_color_selection)
            self.bg_color = get_color(bg_color_selection)

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
            print (self.font, self.text_size)
            self.preview.text_item.props.font = font_selection.get_font_name()
            self.preview.update_font()

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

