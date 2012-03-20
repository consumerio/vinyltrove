import jinja2
import json
import os
import urllib
import urllib2
import webapp2
from google.appengine.ext import db
from google.appengine.api import users
import private

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Profile(db.Model):
    """ A profile corresponds to a GAE user and stores associated metadata for 
        that user.  The key is user.user_id(). """
    access_token = db.StringProperty()

class ConnectPage(webapp2.RequestHandler):
    """ A demo of using OAuth to connect a user's Consumer Notebook account. """
    def get(self):
        user = users.get_current_user()
        if user:
            profile = Profile.get_or_insert(user.user_id())
            template_values = {
                'nickname': user.nickname()
            }
            template = jinja_environment.get_template('connect.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class ManagePage(webapp2.RequestHandler):
    """ Continuation of the OAuth demo. """
    def get(self):
        user = users.get_current_user()
        if user:
            # Get the access token (TODO: only get it if needed)
            code = self.request.get('code')
            url = '{0}/oauth2/access_token/'.format(private.CN_HOST)
            params = {
                'client_id': private.CLIENT_ID,
                'client_secret': private.CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'redirect_uri': private.REDIRECT_URI, 
                'code': code
            }
            try:
                f = urllib2.urlopen(url, urllib.urlencode(params))
            except urllib2.HTTPError:
                f = None
            access_token = None
            if f:
                access_token_response = f.read()
                if access_token_response:
                    access_token_json = json.loads(access_token_response)
                    access_token = access_token_json[u'access_token']
                    profile = Profile.get_or_insert(user.user_id())
                    profile.access_token = access_token
                    profile.save()

            # Use the Lists API
            cn_username = 'audreyr'
            records_url = '{0}/api/v1/lists/{1}/my-vinyl-records'.format(
                    private.CN_HOST, 
                    cn_username)

            vinyl_records = ['The Doors', 'The Dark Side of the Moon']

            template_values = {
                'nickname': user.nickname(),
                'vinyl_records': vinyl_records
            }
            template = jinja_environment.get_template('manage.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp2.WSGIApplication([
        ('/', ConnectPage),
        ('/manage', ManagePage)],
        debug=True)
