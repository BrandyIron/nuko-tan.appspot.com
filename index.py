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
        template_values = {'records': [record for record in NukotanLive().query()]}
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
            # ndb.put_multi(entities)
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