# -*- coding: utf8 -*-
#!/usr/bin/env python

# [START imports]
import os
import json
import jinja2
import webapp2
from webapp2_extras import sessions
from datetime import datetime as dt
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), 
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

# Models
class NukotanLive(ndb.Model):
    song = ndb.StringProperty(indexed=False)
    tour = ndb.StringProperty()
    place = ndb.StringProperty()
    date = ndb.DateTimeProperty()

class NukotanLiveAll(ndb.Model):
    song = ndb.StringProperty()
    count = ndb.IntegerProperty()

class NukotanSong(ndb.Model):
    title = ndb.StringProperty()
    album = ndb.StringProperty()
    release = ndb.DateTimeProperty()

# [START index_page]
class IndexPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())
# [END index_page]        

# [START live_count]
class LiveCount(webapp2.RequestHandler):
    def get(self):
        setlists_count = {}
        tours = ['']
        places = ['']
        conditions = {}
        
        if len(self.request.GET) != 0:
            # With filtering
            conditions = self.request.GET
            isfirst = True
            if self.request.GET.has_key('tour') and self.request.GET['tour'] != '':
                query = NukotanLive.query(NukotanLive.tour == self.request.GET['tour'].strip())
                isfirst = False
            if self.request.GET.has_key('place') and self.request.GET['place'] != '':
                if isfirst:
                    query = NukotanLive.query(NukotanLive.place == self.request.GET['place'].strip())
                    isfirst = False
                else:
                    query = query.query(NukotanLive.place == self.request.GET['place'].strip())
            if self.request.GET.has_key('date_from') and self.request.GET['date_from'] != '':
                if isfirst:
                    query = NukotanLive.query(NukotanLive.date >= dt.strptime(self.request.GET['date_from'].strip(), "%Y-%m-%d"))
                    isfirst = False
                else:
                    query = query.filter(NukotanLive.date >= dt.strptime(self.request.GET['date_from'].strip(), "%Y-%m-%d"))
            if self.request.GET.has_key('date_to') and self.request.GET['date_to'] != '':
                if isfirst:
                    query = NukotanLive.query(NukotanLive.date <= dt.strptime(self.request.GET['date_to'].strip(), "%Y-%m-%d"))                    
                else:
                    query = query.filter(NukotanLive.date <= dt.strptime(self.request.GET['date_to'].strip(), "%Y-%m-%d"))

            if isfirst:
                # Get All Songs from NukotanLiveAll entity
                for record in NukotanLiveAll.query():
                    # self.response.out.write(record.song)
                    setlists_count[record.song] = record.count
            else:
                for record in query:
                    song = record.song.replace(u'（新曲）', '').strip()
                    if setlists_count.has_key(song):
                        setlists_count[song] += 1
                    else:
                        setlists_count[song] = 1
        else:
            # Get All Songs from NukotanLiveAll entity
            for record in NukotanLiveAll.query():
                # self.response.out.write(record.song)
                setlists_count[record.song] = record.count
            
        # Get tour titles, places ordering by date desc
        for record in NukotanLive.query():
            tours.append(record.tour)
            places.append(record.place)

        places_uniq = list(set(places))
        tours_uniq = list(set(tours))

        template_values = {'setlists_count': setlists_count, 'places_uniq': places_uniq, 'tours_uniq': tours_uniq, 'conditions': conditions}
        template = JINJA_ENVIRONMENT.get_template('live_count.html')
        self.response.write(template.render(template_values))
# [END live_count]

class PutDatastore(webapp2.RequestHandler):
    def get(self):
        if self.request.get('f'):
            entities = []
            for record in json.load(open(os.path.dirname(__file__) + '/tmp/' + self.request.get('f') + '.json')):
                entity = NukotanLive()
                entity.date = dt.strptime(record['date'], '%Y-%m-%d')
                entity.place = record['place']
                entity.tour = record['tour']
                entity.song = record['song']
                entities.append(entity)
            # ndb.put_multi(entities)
            self.redirect('/live_count/put_datastore')
        elif self.request.get('NukotanLiveAll_update') == "true":
            setlists_count = {}
            for record in NukotanLive.query():
                song = record.song.replace(u'（新曲）', '').strip()
                if setlists_count.has_key(song):
                    setlists_count[song] += 1
                else:
                    setlists_count[song] = 1
            setlists_count = sorted(setlists_count.items(), key=lambda x: x[0])
            songs = [song for record.song in NukotanLiveAll().query()]
            entities = []
            for key, val in setlists_count:
                if key in songs:
                    deleted = NukotanLiveAll(song=key)
                    deleted.key.delete()
                entity = NukotanLiveAll()
                entity.song = key
                entity.count = val
                entities.append(entity)
                
            # ndb.put_multi(entities)
            self.redirect('/live_count/put_datastore')
        elif self.request.get('NukotanSong_update') == "true":
            entities = []
            for record in json.load(open(os.path.dirname(__file__) + '/tmp/' + 'songs.json')):
                entity = NukotanSong()
                entity.title = record['title']
                entity.album = record['album']
                entity.release = dt.strptime(record['release'], '%Y-%m-%d')
                entities.append(entity)
            ndb.put_multi(entities)
            self.redirect('/live_count/put_datastore')
        else:
            template = JINJA_ENVIRONMENT.get_template('put_datastore.html')
            self.response.write(template.render())

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            # Dispatch the request
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key
        return self.session_store.get_session()

class SongRanking(webapp2.RequestHandler):
    def get(self):
        records = [record for record in NukotanSong.query()]
        nsong = len(records)
        template = JINJA_ENVIRONMENT.get_template('song_ranking.html')
        template_values = {'records': records, 'nsong': nsong}
        self.response.write(template.render(template_values))

class SongRankingDo(BaseHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('song_ranking_do.html')
        self.response.write(template.render())

class TestView(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('testview.html')
        self.response.write(template.render())

# [START app]
app = webapp2.WSGIApplication([
    ('/', IndexPage),
    ('/live_count', LiveCount),
    ('/live_count/put_datastore', PutDatastore),
    ('/song_ranking', SongRanking),
    ('/song_ranking/do', SongRankingDo),
    ('/testview', TestView)
    ], debug=True)
# [END app]