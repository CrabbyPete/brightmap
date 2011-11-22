
from django							import forms
from django.utils.encoding			import force_unicode

class ChoiceWithOtherRenderer(forms.RadioSelect.renderer):
	def __init__(self, *args, **kwargs):
		super(ChoiceWithOtherRenderer, self).__init__(*args, **kwargs)

	def __iter__(self):
		for inp in self.choices:
			id = '%s_%s' % (self.attrs['id'], inp[0]) if 'id' in self.attrs else ''
			label_for = ' for="%s"' % id if id else ''
			checked = '' if not force_unicode(inp[0]) == self.value else 'checked="true" '
			html = '<label%s><input type="radio" id="%s" value="%s" name="%s" %s/> %s</label> %%s' %	\
			(label_for, id, inp[0], self.name, checked, inp[1])

			yield html

class ChoiceWithOtherWidget(forms.MultiWidget):
	def __init__(self, choices):
		widgets = [forms.RadioSelect(choices=choices, renderer=ChoiceWithOtherRenderer),]
		for choice in choices:
			widgets.append(choice[2])

		super(ChoiceWithOtherWidget, self).__init__(widgets)

	def decompress(self, value):
		if not value:
			return [None, None]
		return value

	def format_output(self, rendered_widgets):
		render = []
		for widget in rendered_widgets[1:]:
			render.append(widget)

		render = tuple(render)
		return rendered_widgets[0] %	render

class ChoiceWithOtherField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
		fields = [
		forms.ChoiceField(widget=forms.RadioSelect(renderer=ChoiceWithOtherRenderer), *args, **kwargs),
		]
		widget = ChoiceWithOtherWidget(choices=kwargs['choices'])
		kwargs.pop('choices')
		self._was_required = kwargs.pop('required', True)
		kwargs['required'] = False
		super(ChoiceWithOtherField, self).__init__(widget=widget, fields=fields, *args, **kwargs)

    def compress(self, value):
		if self._was_required and not value or value[0] in (None, ''):
			raise forms.ValidationError(self.error_messages['required'])
		if not value:
			return [None, u'']
		return (value[0], value[1] if force_unicode(value[0]) == force_unicode(self.fields[0].choices[-1][0]) else u'')

    def validate(self,value):
        return True