import datetime, time
import urllib2
import json
from IPython.lib.pretty import pprint
import facebook
from numpy import mean
from django.core.exceptions import FieldError
from django.shortcuts import render, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.db.models import Count, Q, F
from django.conf import settings
from mks.models import Knesset
from facebook_feeds.models import Facebook_Status, Facebook_Feed, Tag, User_Token, Feed_Popularity
from mks.models import Party, Member
from kikar_hamedina.settings import CURRENT_KNESSET_NUMBER

HOURS_SINCE_PUBLICATION_FOR_SIDE_BAR = 3

NUMBER_OF_WROTE_ON_TOPIC_TO_DISPLAY = 3

NUMBER_OF_TAGS_TO_PRESENT = 3


class HomepageView(ListView):
    model = Tag
    template_name = 'core/homepage.html'

    def get_queryset(self):
        queryset = Tag.objects.filter(is_for_main_display=True).annotate(number_of_posts=Count('statuses')).order_by(
            '-number_of_posts')[:NUMBER_OF_TAGS_TO_PRESENT]
        return queryset

    def get_context_data(self, **kwargs):
        context = super(HomepageView, self).get_context_data(**kwargs)
        wrote_about_tag = dict()
        for tag in context['object_list']:
            list_of_writers = Facebook_Feed.objects.filter(facebook_status__tags__id=tag.id).distinct()
            list_of_writers_with_latest_fan_count = list()
            for feed in list_of_writers:
                list_of_writers_with_latest_fan_count.append({'feed': feed,
                                                              'fan_count': feed.current_fan_count})
            sorted_list_of_writers = sorted(list_of_writers_with_latest_fan_count,
                                            key=lambda x: x['fan_count'],
                                            reverse=True)
            wrote_about_tag[tag] = [feed['feed'] for feed in sorted_list_of_writers][
                                   :NUMBER_OF_WROTE_ON_TOPIC_TO_DISPLAY]
        context['wrote_about_tag'] = wrote_about_tag
        return context


class AllStatusesView(ListView):
    model = Facebook_Status
    template_name = 'core/all_results.html'
    # paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super(AllStatusesView, self).get_context_data(**kwargs)
        feeds = Facebook_Feed.objects.filter(
            facebook_status__published__gte=(
                datetime.date.today() - datetime.timedelta(hours=HOURS_SINCE_PUBLICATION_FOR_SIDE_BAR))).distinct()
        context['side_bar_list'] = Member.objects.filter(
            id__in=[feed.persona.object_id for feed in feeds]).distinct().order_by('name')
        context['side_bar_parameter'] = HOURS_SINCE_PUBLICATION_FOR_SIDE_BAR
        return context


#
class SearchView(ListView):
    model = Facebook_Status
    # paginate_by = 10
    context_object_name = 'filtered_statuses'
    template_name = "core/search.html"

    # def get_queryset(self):
    #
    #     members = []
    #     if 'members' in self.request.GET.keys():
    #         members = [int(member_id) for member_id in self.request.GET['members'].split(',')]
    #     if 'parties' in self.request.GET.keys():
    #         parties_ids = [int(party_id) for party_id in self.request.GET['parties'].split(',')]
    #         parties = Party.objects.filter(id__in=parties_ids)
    #         for party in parties:
    #             for member in party.current_members():
    #                 if member.id not in members:
    #                     members.append(member.id)
    #
    #     member_query = Member.objects.filter(id__in=members)
    #     feeds = Facebook_Feed.objects.filter(persona__object_id__in=[member.id for member in member_query])
    #     tags_ids = []
    #     if 'tags' in self.request.GET.keys():
    #         tags_ids = [int(tag_id) for tag_id in self.request.GET['tags'].split(',')]
    #
    #     query_Q = Q(feed__in=feeds) | Q(tags__in=tags_ids)
    #
    #     if 'search_str' in self.request.GET.keys():
    #         search_str = self.request.GET['search_str']
    #         query_str_Q = Q(content__contains=search_str)
    #         search_words = search_str.strip().split(' ')
    #         for word in search_words:
    #             query_str_Q = Q(content__contains=word) | query_str_Q
    #         query_Q = query_Q & query_str_Q
    #
    #     print query_Q
    #     return_queryset = Facebook_Status.objects.filter(query_Q).order_by("-published")
    #     print 'number of results: %d' % len(return_queryset)
    #     return return_queryset

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)

        members = []
        if 'members' in self.request.GET.keys():
            members = [int(member_id) for member_id in self.request.GET['members'].split(',')]
        context['members'] = Member.objects.filter(id__in=members)

        parties_ids = []
        if 'parties' in self.request.GET.keys():
            parties_ids = [int(party_id) for party_id in self.request.GET['parties'].split(',')]
            parties = Party.objects.filter(id__in=parties_ids)
            for party in parties:
                for member in party.current_members():
                    if member.id not in members:
                        members.append(member.id)
        context['parties'] = Party.objects.filter(id__in=parties_ids)

        member_query = Member.objects.filter(id__in=members)
        feeds = Facebook_Feed.objects.filter(persona__object_id__in=member_query)

        tags_ids = []
        if 'tags' in self.request.GET.keys():
            tags_ids = [int(tag_id) for tag_id in self.request.GET['tags'].split(',')]
        context['tags'] = Tag.objects.filter(id__in=tags_ids)

        if feeds and tags_ids:
            query_q_objecs = Q(feed__in=feeds) | Q(tags__in=tags_ids)
        elif tags_ids:
            query_q_objecs = Q(tags__in=tags_ids)
        elif feeds:
            query_q_objecs = Q(feed__in=feeds)
        else:
            query_q_objecs = None

        query_q_words = None
        search_str = None
        if 'search_str' in self.request.GET.keys():
            search_str = self.request.GET['search_str']
            query_q_words = Q(content__contains=search_str)
            search_words = search_str.strip().split(' ')
            for word in search_words:
                query_q_words = Q(content__contains=word) | query_q_words

        if query_q_objecs and query_q_words:
            query_q = query_q_objecs & query_q_words
        elif query_q_words:
            query_q = query_q_words
        elif query_q_objecs:
            query_q = query_q_objecs
        else:
            query_q = Q(content__contains='')

        context['search_str'] = search_str

        print query_q
        return_queryset = Facebook_Status.objects.filter(query_q).order_by("-published")
        print len(return_queryset)
        self.queryset = return_queryset
        context['number_of_results'] = return_queryset.count()
        context['side_bar_parameter'] = HOURS_SINCE_PUBLICATION_FOR_SIDE_BAR

        return context


class SearchGuiView(ListView):
    model = Facebook_Status
    template_name = "core/searchgui.html"


class StatusFilterUnifiedView(ListView):
    model = Facebook_Status
    # paginate_by = 10
    context_object_name = 'filtered_statuses'

    def get_queryset(self):
        variable_column = self.kwargs['variable_column']
        search_string = self.kwargs['id']
        if self.kwargs['context_object'] == 'tag':
            search_field = self.kwargs['search_field']
            if search_field == 'id':
                search_field = 'id'
            else:
                search_field = 'name'
            selected_filter = variable_column + '__' + search_field
            try:
                query_set = Facebook_Status.objects.filter(**{selected_filter: search_string}).order_by(
                    '-published')
            except FieldError:
                selected_filter = variable_column + '__' + 'name'
                query_set = Facebook_Status.objects.filter(**{selected_filter: search_string}).order_by(
                    '-published')
                # TODO: Replace with redirect to actual url with 'name' in path, and HttpResponseRedirect()
            return query_set
        else:
            selected_filter = variable_column
            return Facebook_Status.objects.filter(**{selected_filter: search_string}).order_by('-published')

    def get_context_data(self, **kwargs):
        context = super(StatusFilterUnifiedView, self).get_context_data(**kwargs)

        object_id = self.kwargs['id']
        search_field = self.kwargs.get('search_field', 'id')
        context['object'] = self.parent_model.objects.get(**{search_field: object_id})
        return context


class MemberView(StatusFilterUnifiedView):
    template_name = "core/member.html"
    parent_model = Member

    def get_queryset(self, **kwargs):
        search_string = self.kwargs['id']
        query_set = Member.objects.get(
            id=search_string).facebook_persona.get_main_feed.facebook_status_set.all().order_by(
            '-published')
        return query_set

    def get_context_data(self, **kwargs):
        context = super(MemberView, self).get_context_data(**kwargs)
        stats = dict()
        member_id = self.kwargs['id']
        feed = Facebook_Feed.objects.get(persona__object_id=member_id)

        # Statistical Data for member - PoC

        statuses_for_member = Facebook_Status.objects.filter(feed__persona__object_id=member_id).order_by('-like_count')

        df_statuses = statuses_for_member.to_dataframe('like_count', index='published')
        mean_monthly_popularity_by_status_raw = df_statuses.resample('M', how='mean').to_dict()

        mean_monthly_popularity_by_status_list_unsorted = [{'x': time.mktime(key.timetuple()) * 1000, 'y': value} for
                                                           # *1000 - seconds->miliseconds
                                                           key, value in
                                                           mean_monthly_popularity_by_status_raw['like_count'].items()]
        mean_monthly_popularity_by_status_list_sorted = sorted(mean_monthly_popularity_by_status_list_unsorted,
                                                               key=lambda x: x['x'])
        mean_monthly_popularity_by_status = json.dumps(mean_monthly_popularity_by_status_list_sorted)
        print mean_monthly_popularity_by_status
        mean_like_count_all = mean([status.like_count for status in statuses_for_member])
        mean_like_count_all_series = [{'x': time.mktime(key.timetuple()) * 1000, 'y': mean_like_count_all} for
                                      # *1000 - seconds->miliseconds
                                      key, value in
                                      mean_monthly_popularity_by_status_raw['like_count'].items()]
        mean_like_count_all_series_json = json.dumps(mean_like_count_all_series)

        mean_like_count_last_month = mean([status.like_count for status in statuses_for_member.filter(
            published__gte=timezone.now() - timezone.timedelta(days=30))])

        tags_for_member = Tag.objects.filter(statuses__feed__persona__object_id=member_id).annotate(
            number_of_posts=Count('statuses')).order_by(
            '-number_of_posts')
        tags_for_member_list = [{'label': tag.name, 'value': tag.number_of_posts} for tag in tags_for_member]
        tags_for_member_json = json.dumps(tags_for_member_list)

        stats['tags_for_member'] = tags_for_member_json
        stats['mean_monthly_popularity_by_status'] = mean_monthly_popularity_by_status
        # stats['total_monthly_post_frequency'] = total_monthly_post_frequency
        stats['mean_like_count_all'] = mean_like_count_all_series_json

        context['stats'] = stats

        return context


class PartyView(StatusFilterUnifiedView):
    template_name = "core/party.html"
    parent_model = Party

    def get_queryset(self, **kwargs):
        search_string = self.kwargs['id']
        all_members_for_party = Party.objects.get(id=search_string).current_members()
        all_feeds_for_party = [Member.objects.get(id=member.id).facebook_persona.get_main_feed for member in
                               all_members_for_party]
        query_set = Facebook_Status.objects.filter(feed__id__in=[feed.id for feed in all_feeds_for_party]).order_by(
            '-published')
        return query_set


class TagView(StatusFilterUnifiedView):
    template_name = "core/tag.html"
    parent_model = Tag

    def get_context_data(self, **kwargs):
        context = super(TagView, self).get_context_data(**kwargs)
        all_feeds_for_tag = Facebook_Feed.objects.filter(facebook_status__tags__id=context['object'].id).distinct()
        context['side_bar_list'] = Member.objects.filter(
            id__in=[feed.persona.object_id for feed in all_feeds_for_tag]).distinct().order_by('name')
        return context


class FacebookStatusDetailView(DetailView):
    template_name = 'core/facebook_status_detail.html'

    model = Facebook_Status
    slug_field = 'status_id'

    def get_context_data(self, **kwargs):
        context = super(FacebookStatusDetailView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['member'] = Member.objects.get(id=context['object'].feed.facbook_persona.object_id)
        return context


class AllMembers(ListView):
    template_name = 'core/all_members.html'
    model = Member


class AllParties(ListView):
    template_name = 'core/all_parties.html'
    model = Party


class AllTags(ListView):
    template_name = 'core/all_tags.html'
    model = Tag


def about_page(request):
    return render(request, 'core/about.html')


def add_tag(request, id):
    status = Facebook_Status.objects.get(id=id)
    tagsString = request.POST['tag']
    tagsList = tagsString.split(',')
    for tagName in tagsList:
        strippedTagName = tagName.strip()
        if strippedTagName:
            tag, created = Tag.objects.get_or_create(name=strippedTagName)
            if created:
                tag.name = strippedTagName
                tag.is_for_main_display = True
                tag.save()
                # add status to tag statuses
            tag.statuses.add(status)
            tag.save()

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


# Views for getting facebook data using a user Token
def login_page(request):
    return render(request, 'core/login_page.html')


def get_data_from_facebook(request):
    """
    This Function creates or updates within our db a facebook token recieved from a user.
    After receiving the token, it is first extended into  a long-term user token
    (see https://developers.facebook.com/docs/facebook-login/access-tokens#extending for mored details)

    Next the token is saved in our db. Afterwards, the token is tested on all of our user-profile feeds, for each
    feed that the token works for, their relation will be saved in our db, for future use.

    At the end, the function redirects backwards into referrer url.
    """
    user_access_token = request.POST['access_token']
    graph = facebook.GraphAPI(access_token=user_access_token)
    # Extension into long-term token
    extended_access_token = graph.extend_access_token(settings.FACEBOOK_APP_ID, settings.FACEBOOK_SECRET_KEY)
    print 'access token, changed \nfrom: %s \nto: %s ' % (user_access_token, extended_access_token)
    graph.access_token = extended_access_token['access_token']
    # create or update token for user in db
    user = graph.get_object('me')
    token, created = User_Token.objects.get_or_create(user_id=user['id'])
    if created:
        token.token = extended_access_token['access_token']
        token.user_id = user['id']
    token.token = extended_access_token['access_token']
    token.date_of_creation = timezone.now()
    token.date_of_expiration = timezone.now() + timezone.timedelta(seconds=int(extended_access_token['expires']))
    token.save()

    # add or update relevant feeds for token
    user_profile_feeds = Facebook_Feed.objects.filter(feed_type='UP')
    # user_profile_feeds = ['508516607', '509928464']  # Used for testing
    relevant_feeds = []
    print 'working on %d user_profile feeds.' % len(user_profile_feeds)
    for feed in user_profile_feeds:
        statuses = graph.get_connections(feed.vendor_id, 'statuses')
        if statuses['data']:
            print 'feed %s returns at least one result.' % feed
            relevant_feeds.append(feed)
    for feed in relevant_feeds:
        token.feeds.add(feed)
    print 'adding %d feeds to token' % len(relevant_feeds)
    token.save()
    # Redirect
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


#A handler for status_update ajax call from client
def status_update(request, status_id):
    status = Facebook_Status.objects.get(status_id=status_id)

    url = "https://graph.facebook.com/"
    url += str(status.status_id)
    url += "?access_token=" + facebook.get_app_access_token(settings.FACEBOOK_APP_ID, settings.FACEBOOK_SECRET_KEY)
    url += "&fields=shares,likes.limit(1).summary(true),comments.limit(1).summary(true)"

    try:
        responseText = urllib2.urlopen(url).read()
        responseJson = json.loads(responseText)

        response_data = dict()
        response_data['likes'] = responseJson['likes']['summary']['total_count']
        response_data['comments'] = responseJson['comments']['summary']['total_count']
        response_data['shares'] = responseJson['shares']['count']
        response_data['id'] = status.status_id
        try:
            status.like_count = int(response_data['likes'])
            status.comment_count = int(response_data['comments'])
            status.share_count = int(response_data['shares'])
            status.save()
        finally:
            return HttpResponse(json.dumps(response_data), content_type="application/json")
    finally:
        response_data = dict()
        response_data['likes'] = status.like_count
        response_data['comments'] = status.comment_count
        response_data['shares'] = status.share_count
        response_data['id'] = status.status_id

        return HttpResponse(json.dumps(response_data), content_type="application/json")

#A handler for add_tag_to_status ajax call from client
def add_tag_to_status(request):

    response_data = dict()
    response_data['success'] = False
    status_id=request.GET["id"]
    response_data['id'] = status_id
    tagName=request.GET["tag_str"]
    strippedTagName = tagName.strip()
    try:
        if strippedTagName:
            tag, created = Tag.objects.get_or_create(name=strippedTagName)
            if created:
                tag.name = strippedTagName
                tag.is_for_main_display = True
                tag.save()
                # add status to tag statuses
            tag.statuses.add(status_id)
            tag.save()
            response_data['tag'] = {'id':tag.id,'name':tag.name}
        response_data['success'] = True
    except:
        print "ERROR AT ADDING STATUS TO TAG"
        print status_id

    finally:
        return HttpResponse(json.dumps(response_data), content_type="application/json")


#A handler for the search bar request from the client
def search_bar(request):
    searchText = request.GET['text']

    response_data = dict()
    response_data['number_of_results'] = 0
    response_data['results'] = []
    if searchText.strip() == "":
        print "NO STRING"
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    members = Member.objects.filter(name__contains=searchText, is_current=True)
    for member in members:
        newResult = dict()
        newResult['id'] = member.id
        newResult['name'] = member.name
        newResult['party'] = member.current_party.name
        newResult['type'] = "member"
        response_data['results'].append(newResult)
        response_data['number_of_results'] += 1

    tags = Tag.objects.filter(name__contains=searchText)
    for tag in tags:
        newResult = dict()
        newResult['id'] = tag.id
        newResult['name'] = tag.name
        newResult['type'] = "tag"
        response_data['results'].append(newResult)
        response_data['number_of_results'] += 1

    parties = Party.objects.filter(name__contains=searchText, knesset__number=CURRENT_KNESSET_NUMBER)
    for party in parties:
        newResult = dict()
        newResult['id'] = party.id
        newResult['name'] = party.name
        newResult['type'] = "party"
        response_data['results'].append(newResult)
        response_data['number_of_results'] += 1

    print 'number of results:', response_data['number_of_results']
    pprint(response_data)
    return HttpResponse(json.dumps(response_data), content_type="application/json")

