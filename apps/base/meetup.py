#!/usr/bin/env python
from __future__ import with_statement

import datetime
import time
import cgi
import types
import logging
from urllib import urlencode
from urllib2 import HTTPError, HTTPErrorProcessor, urlopen, Request, build_opener

import MultipartPostHandler as mph

# This is an example of a client wrapper that you can use to
# make calls to the Meetup.com API. It requires that you have
# a JSON parsing module available.

API_JSON_ENCODING = 'ISO-8859-1'

try:
    try:
        import cjson
        parse_json = lambda s: cjson.decode(s.decode(API_JSON_ENCODING), True)
    except ImportError:
        try:
            import json
            parse_json = lambda s: json.loads(s.decode(API_JSON_ENCODING))
        except ImportError:
            import simplejson
            parse_json = lambda s: simplejson.loads(s.decode(API_JSON_ENCODING))
except:
    print "Error - your system is missing support for a JSON parsing library."

GROUPS_URI = 'groups'
EVENTS_URI = 'events'
CITIES_URI = 'cities'
TOPICS_URI = 'topics'
PHOTOS_URI = 'photos'
MEMBERS_URI = 'members'
RSVPS_URI = 'rsvps'
RSVP_URI = 'rsvp'
COMMENTS_URI = 'comments'
PHOTO_URI = 'photo'
MEMBER_PHOTO_URI = '2/member_photo'


class MeetupHTTPErrorProcessor(HTTPErrorProcessor):
    def http_response(self, request, response):
        try:
            return HTTPErrorProcessor.http_response(self, request, response)
        except HTTPError, e:
            error_json = parse_json(e.read())
            if e.code == 401:
                raise UnauthorizedError(error_json)
            elif e.code in ( 400, 500 ):
                raise BadRequestError(error_json)
            else:
                raise ClientException(error_json)

what_types = ('groups'
'2/groups'
'events'
'cities'
'topics'
'photos'
'members'
'rsvps'
'rsvp'
'comments'
'photo'
'2/member_photo'
)

class MeetUpAPI(object):
    def __init__(self, access_token):
        self.access_token = access_token

    def get(self, what, **kwargs ):
        kwargs['access_token'] = self.access_token
        what = what+'.json/'
        url = 'https://api.meetup.com' + what + "?" + urllib.urlencode(kwargs)

        file = urllib.urlopen(url)
        data = file.read()
        response = json.loads(data)
        return


class API_Item(object):
    """Base class for an item in a result set returned by the API."""

    def __init__(self, properties):
         """load properties that are relevant to all items (id, etc.)"""
         for field in properties.keys():
             self.__setattr__(field, properties[field])

    def __repr__(self):
         return self.__str__();

class Member(API_Item):
    datafields = ['bio', 'name', 'link','id','photo_url', 'zip','lat','lon','city','state','country','joined','visited']

    def get_groups(self, apiclient, **extraparams):
        extraparams.update({'member_id':self.id})
        return apiclient.get_groups(extraparams);

    def __str__(self):
        return "Member %s (url: %s)" % (self.name, self.link)

class Photo(API_Item):
    datafields = ['albumtitle', 'link', 'member_url', 'descr', 'created', 'photo_url', 'photo_urls', 'thumb_urls']

    def __str__(self):
        return "Photo located at %s posted by member at %s: (%s)" % (self.link, self.member_url, self.descr)


class Event(API_Item):
    datafields = ['id', 'name', 'updated', 'time', 'photo_url', 'event_url', 'description', 'status', \
        'rsvpcount', 'no_rsvpcount', 'maybe_rsvpcount', \
        'venue_id', 'venue_name', 'venue_phone', 'venue_address1', 'venue_address3', 'venue_address2', 'venue_city', 'venue_state', 'venue_zip', \
        'venue_map', 'venue_lat', 'venue_lon', 'venue_visibility']

    def __str__(self):
        return 'Event %s named %s at %s (url: %s)' % (self.id, self.name, self.time, self.event_url)

    def get_rsvps(self, apiclient, **extraparams):
        extraparams['event_id'] = self.id
        return apiclient.get_rsvps(**extraparams)

class Rsvp(API_Item):
    datafields = ['name', 'link', 'comment','zip','coord','lon','city','state','country','response','guests','answers','updated','created']

    def __str__(self):
        return 'Rsvp by %s (%s) with comment: %s' % (self.name, self.link, self.comment)

class Group(API_Item):
    datafields = [ 'id','name','group_urlname','link','updated',\
                   'members','created','photo_url',\
                   'description','zip','lat','lon',\
                   'city','state','country','organizerProfileURL', \
                   'topics']

    def __str__(self):
         return "%s (%s)" % (self.name, self.link)

    def get_events(self, apiclient, **extraparams):
        extraparams['group_id'] = self.id
        return apiclient.get_events(**extraparams)

    def get_photos(self, apiclient, **extraparams):
        extraparams['group_id'] = self.id
        return apiclient.get_photos(**extraparams)

    def get_members(self, apiclient, **extraparams):
        extraparams['group_id'] = self.id
        return apiclient.get_members(**extraparams)

class City(API_Item):
    datafields = ['city','country','state','zip','members','lat','lon']

    def __str__(self):
         return "%s %s, %s, %s, with %s members" % (self.city, self.zip, self.country, self.state, self.members)

    def get_groups(self,apiclient,  **extraparams):
        extraparams.update({'city':self.city, 'country':self.country})
        if self.country=='us': extraparams['state'] = self.state
        return apiclient.get_groups(**extraparams)

    def get_events(self,apiclient,  **extraparams):
        extraparams.update({'city':self.city, 'country':self.country})
        if self.country=='us': extraparams['state'] = self.state
        return apiclient.get_events(**extraparams)

class Topic(API_Item):
    datafields = ['id','name','description','link','updated',\
                  'members','urlkey']

    def __str__(self):
         return "%s with %s members (%s)" % (self.name, self.members,
                                             self.urlkey)

    def get_groups(self, apiclient, **extraparams):
         extraparams['topic'] = self.urlkey
         return apiclient.get_groups(**extraparams)

    def get_photos(self, apiclient, **extraparams):
         extraparams['topic_id'] = self.id
         return apiclient.get_photos(**extraparams)

class Comment(API_Item):
    datafields = ['name','link','comment','photo_url',\
                  'created','lat','lon','country','city','state']

    def __str__(self):
         return "Comment from %s (%s)" % (self.name, self.link)

########################################

class ClientException(Exception):
    """
         Base class for generic errors returned by the server
    """
    def __init__(self, error_json):
         self.description = error_json['details']
         self.problem = error_json['problem']

    def __str__(self):
         return "%s: %s" % (self.problem, self.description)

class UnauthorizedError(ClientException):
    pass;

class BadRequestError(ClientException):
    pass;

