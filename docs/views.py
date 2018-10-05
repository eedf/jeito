from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML
from haystack.query import SearchQuerySet
from . import forms as docs_forms
from . import models as docs_models
from .signals import post_form_save


class IndexView(LoginRequiredMixin, ListView):
    template_name = 'docs/index.html'
    model = docs_models.Document
    limit = 50

    def get_queryset(self):
        qs = SearchQuerySet().models(docs_models.Document)
        self.form = docs_forms.DocumentSearchForm(data=self.request.GET)
        if self.form.is_valid():
            q = self.form.cleaned_data.get('q', '')
            qs = qs.filter(content=q)
        qs = qs.filter(visible=True)
        self.count = qs.count()
        qs = qs[:self.limit]
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['more'] = self.count > self.limit
        context['limit'] = self.limit
        return context


class CrispyFormViewMixin(object):
    glyphicon = 'ok-sign'
    submit_text = u"OK"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.helper = FormHelper()
        form.helper.layout = Layout(*self.fields)
        form.helper.layout.append(
            HTML(u"""<button type="submit" class=\"btn btn-success\">
                       <span class="glyphicon glyphicon-{glyphicon}"></span> {text}
                     </button>""".format(glyphicon=self.glyphicon, text=self.submit_text))
        )
        form.helper.layout.append(
            HTML(u"""<a href=\"{href}\" class=\"btn btn-default\">
                       <span class="glyphicon glyphicon-remove-sign"></span> Annuler
                     </a>""".format(href=self.success_url))
        )
        return form


class SaveSignalMixin(object):
    def form_valid(self, form):
        response = super().form_valid(form)
        post_form_save.send(sender=self.model, instance=self.object)
        return response


class DocumentCreateView(LoginRequiredMixin, SaveSignalMixin, CrispyFormViewMixin, CreateView):
    model = docs_models.Document
    fields = ('file', 'title', 'tags')
    success_url = reverse_lazy('docs:index')
    glyphicon = 'plus'
    submit_text = u"Ajouter"


class DocumentUpdateView(LoginRequiredMixin, SaveSignalMixin, CrispyFormViewMixin, UpdateView):
    model = docs_models.Document
    fields = ('file', 'title', 'tags')
    success_url = reverse_lazy('docs:index')
    submit_text = u"Modifier"


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = docs_models.Document
    success_url = reverse_lazy('docs:index')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.visible = False
        self.object.save()
        post_form_save.send(sender=self.model, instance=self.object)
        return HttpResponseRedirect(success_url)
