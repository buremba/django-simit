# -*- coding: utf-8 -*-
import json

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from tinymce.widgets import TinyMCE
from simit.widgets import ColorPicker


class VariableForm(forms.Form):
    classes = ""
    name = ""
    description = ""

    def __init__(self, *args, **kwargs):
        fieldQuerySet = kwargs['fieldQuerySet']
        del kwargs['fieldQuerySet']
        super(VariableForm, self).__init__(*args, **kwargs)
        for i in fieldQuerySet:
            if i.type == 1:
                self.fields[i.slug] = forms.CharField(label=i.name, initial=i.value, help_text=i.description)
            elif i.type == 2:
                self.fields[i.slug] = forms.DateTimeField(label=i.name, initial=i.value, help_text=i.description, widget=AdminDateWidget)
            elif i.type == 3:
                self.fields[i.slug] = forms.IntegerField(label=i.name, initial=i.value, help_text=i.description)
            elif i.type == 4:
                self.fields[i.slug] = forms.CharField(label=i.name, initial=i.value, help_text=i.description, widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
            elif i.type == 5:
                self.fields[i.slug] = forms.BooleanField(required=False, label=i.name, initial=i.value, help_text=i.description)
            elif i.type == 6:
                choices = json.loads(i.extra)

                self.fields[i.slug] = forms.ChoiceField(label=i.name, choices=choices, initial=i.value, help_text=i.description)
            elif i.type == 7:
                self.fields[i.slug] = forms.CharField(label=i.name, initial=i.value, help_text=i.description, widget=forms.Textarea)
            elif i.type == 8:
                self.fields[i.slug] = forms.CharField(label=i.name, initial=i.value, help_text=i.description, widget=ColorPicker)
            elif i.type == 9:
                self.fields[i.slug] = forms.CharField(label=i.name, initial=i.value, help_text=i.description, widget=forms.Textarea)
            self.fields[i.slug].row_id = i.id