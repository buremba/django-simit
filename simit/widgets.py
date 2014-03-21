from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe


class ColorPicker(forms.TextInput):
    class Media:
        css = {'all': (settings.STATIC_URL + 'colorpicker/css/colorpicker.css',)}
        js = ( settings.STATIC_URL + 'colorpicker/js/colorpicker.js',)

    def render(self, name, value, attrs=None):
        id = attrs['id']
        attrs['type'] = 'hidden'
        attrs['id'] = id + '_input'
        rendered = super(ColorPicker, self).render(name, value, attrs)
        return rendered + mark_safe(u'''
        <div id="%(div_id)s" class="colorSelector" style="background:%(value)s"></div>
        <script type="text/javascript">
            $("#%(div_id)s").ColorPicker({
            color: $('#%(input_id)s').val(),
            onSubmit: function(hsb, hex, rgb, el) {
                $('#%(input_id)s').val('#'+hex);
                $("#%(div_id)s").css('background', '#'+hex);
                $(el).ColorPickerHide();
            }
        });
        </script>''' % {'input_id': attrs['id'], 'div_id': id, 'value': value})