from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from facebook_feeds.models import Facebook_Status, Facebook_Feed, Tag
from mks.models import Party, Member
from kikar_hamedina.settings import CURRENT_KNESSET_NUMBER
from tastypie.api import Api
from api import *


v1_api = Api(api_name='v1')
v1_api.register(MemberResource())
v1_api.register(PartyResource())
v1_api.register(KnessetResource())
v1_api.register(Facebook_StatusResource())
v1_api.register(Facebook_FeedResource())
v1_api.register(TagResource())

urlpatterns = patterns('',
                       url(r'^$', views.HomepageView.as_view(), name='index'),
                       url(r'^all-statuses/$',
                           views.AllStatusesView.as_view(queryset=Facebook_Status.objects.order_by('-published')),
                           kwargs={'context_object': 'index'},
                           name='all-statuses'),
                       url(r'^untagged/$', views.AllStatusesView.as_view(
                           queryset=Facebook_Status.objects.filter(tags=None).order_by('-published')),
                           kwargs={'context_object': 'untagged'},
                           name='untagged'),
                       url(r'^add-tag/(?P<id>\d+)/$', views.add_tag,
                           name='add-tag'),
                       url(r'^party/(?P<id>\d+)/$', views.PartyView.as_view(),
                           kwargs={'variable_column': 'feed__person__party__id',  # TODO: refactor!
                                   'context_object': 'party'},
                           name='party'),
                       url(r'^member/(?P<id>\d+)/$', views.MemberView.as_view(),
                           kwargs={'variable_column': 'feed__persona__object_id',
                                   'context_object': 'member'},
                           name='member'),
                       url(r'^tag/(?P<search_field>\w+)/(?P<id>[\w\s\-:"\'!\?&\.#]+)/$', views.TagView.as_view(),
                           kwargs={'variable_column': 'tags',
                                   'context_object': 'tag'},
                           name='tag'),
                       url(r'^search/$', views.SearchView.as_view(),
                           kwargs={'variable_column': 'content', 'context_object': 'search'}, name='search'),
                       url(r'^searchgui/$', views.SearchGuiView.as_view(), name="search-gui"),
                       url(r'^members/$',
                           views.AllMembers.as_view(queryset=Member.objects.filter(is_current=True)),
                           name='all-members'),
                       url(r'^parties/$', views.AllParties.as_view(
                           queryset=Party.objects.filter(knesset__number=CURRENT_KNESSET_NUMBER)),
                           name='all-parties'),
                       url(r'^tags/$', views.AllTags.as_view(queryset=Tag.objects.all()),
                           name='all-tags'),
                       url(r'^about/$', views.about_page, name='about', ),
                       url(r'^fblogin/$', views.login_page, name='fblogin'),
                       url(r'^fblogin/get-data/$', views.get_data_from_facebook, name='get-data-from-facebook'),
                       url(r'^status_update/(?P<status_id>\w+)/$', views.status_update),
                       url(r'^add_tag_to_status/$', views.add_tag_to_status),
                       url(r'^search_bar/$', views.search_bar),
                       url(r'^api/',include(v1_api.urls)),
                       url(r'^status_permalink/(?P<slug>[-_\w]+)/$', views.FacebookStatusDetailView.as_view(), name='status-detail'),
)

urlpatterns = format_suffix_patterns(urlpatterns)

