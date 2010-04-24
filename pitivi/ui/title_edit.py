
import gtk

from pitivi.ui.glade import GladeWindow

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

        self.widgets['color_button'].connect('clicked', self._run_color_dialog)
        self.widgets['font_button'].connect('clicked', self._run_font_dialog)

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

    def set(self, **kw):
        self.__dict__.update(kw)

    def _copy_to_dialog(self):
        buffer = self.widgets['textview'].props.buffer
        buffer.set_text(self.text)

        for i, (x_alignment, y_alignment) in enumerate(alignments):
            if (self.x_alignment == x_alignment and
                self.y_alignment == y_alignment):
                self.widgets['radiobutton%d' % (i + 1)].props.active = True

    def _copy_from_dialog(self):
        buffer = self.widgets['textview'].props.buffer
        self.text = buffer.get_text(*buffer.get_bounds())

        for i, (x_alignment, y_alignment) in enumerate(alignments):
            if self.widgets['radiobutton%d' % (i + 1)].props.active:
                break

        self.x_alignment = x_alignment
        self.y_alignment = y_alignment

    def run(self):
        self._copy_to_dialog()
        response = gtk.Dialog.run(self.window)
        self._copy_from_dialog()
        return response

