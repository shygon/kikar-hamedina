from mks.models import Party, Member
from facebook_feeds.models import Tag, Facebook_Status, Facebook_Feed, Feed_Popularity
from django.db.models import F, Count
from kikar_hamedina.settings import FACEBOOK_APP_ID, CURRENT_KNESSET_NUMBER


NUMBER_OF_TOP_PARTIES_TO_BRING = 12
NUMBER_OF_TOP_POLITICIANS_TO_BRING = 12
NUMBER_OF_TOP_TAGS_TO_BRING = 12


def generic(request):

    members = Member.objects.filter(is_current=True)
    members_with_persona = [member for member in members if member.facebook_persona]
    members_with_feed = [member for member in members_with_persona if member.facebook_persona.feeds.all()]
    list_of_members = list()
    for member in members_with_feed:
        try:
            feed_popularity = member.facebook_persona.get_main_feed.current_fan_count
            list_of_members.append({'member': member, 'popularity': feed_popularity})
        except:
            pass
    sorted_list_of_members = sorted(list_of_members, key=lambda x: x['popularity'], reverse=True)

    return {
        'navMembers': [x['member'] for x in sorted_list_of_members][:NUMBER_OF_TOP_POLITICIANS_TO_BRING],
        'navParties': Party.objects.filter(knesset__number=CURRENT_KNESSET_NUMBER)
                    .order_by('-number_of_members')[:NUMBER_OF_TOP_PARTIES_TO_BRING],
        'navTags': Tag.objects.filter(is_for_main_display=True)
                    .annotate(number_of_posts=Count('statuses'))
                    .order_by('-number_of_posts')[:NUMBER_OF_TOP_TAGS_TO_BRING],
        'facebook_app_id': FACEBOOK_APP_ID,
    }
