import pprint
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from .forms import CoursesForm
from .utils import *
# 'title' var required for all renders using base.html
# 'errors' is an array of lines to print as an error

def index(request):
    return render(request, 'index.html', {'title' : "Unofficial Carleton Scheduler"})

def generateNewClasses(request):
    if not request.user.is_authenticated: return redirect('index')

    content = {'title': "New Courses Results"}

    if (request.method == "POST"):
        form = CoursesForm(request.POST)
        if (form.is_valid()):
            (found,errors)= dissect(form.cleaned_data['coursesRaw'])
            found.insert(0,"Number of courses parsed: {}".format(len(found)))
            content['courses'] = found
            content['form'] = CoursesForm(request.POST)

            if 'push' in request.POST.keys():
                for c in found[1:]:
                    c.save()
                    print("{} saved!".format(c))

            if (errors != None):
                content['errors'] = errors
            return render(request, 'input.html', content)
        else:
            content['errors'] = 'Invalid Input'

    content['form'] = CoursesForm()
    return render(request, 'input.html', content)