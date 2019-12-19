from django import forms


class CoursesForm(forms.Form):
    coursesRaw = forms.CharField(widget=forms.Textarea(attrs={'style':'width:98%; height:400px; max-width:100%'}),label='Copy and paste your courses', required= False)
