# -*- coding: utf-8 -*-
"""Main File for the basic handlers."""

import httplib2
import jinja2
import logging
import os
import webapp2

from apiclient import discovery
from oauth2client import appengine
from oauth2client import client
from google.appengine.api import memcache

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
                               autoescape=True)

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
http = httplib2.Http(memcache)
service = discovery.build("drive", "v2", http=http)
decorator = appengine.oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/drive',
    message='NO CLIENT SECRET MESSAGE FOUND')

class BaseHandler(webapp2.RequestHandler):
  
  def render_str(self, template, params):
    t = JINJA_ENV.get_template(template)
    return t.render(params)
  
  def render(self, template, kw):
    self.response.out.write(self.render_str(template, kw))
    
    
class IndexHandler(BaseHandler):
  
  @decorator.oauth_required
  def get(self):
    self.render("index.html", {})
    
    
class ProcessHandler(BaseHandler):
  
  @decorator.oauth_required
  def download_file(self, service, drive_file):
    download_url = drive_file['exportLinks']['text/plain']
    if download_url:
      resp, content = service._http.request(download_url)
      if resp.status == 200:
        return content
      else:
        logging.warning('Status is ' + str(resp.status))
        logging.warning('An error occurred: %s' % resp)
        return None
    else:
      # The file doesn't have any content stored on Drive.
      return None
  
  @decorator.oauth_required
  def get(self):
    fileId = self.request.get('fileId')
    try:
      http = decorator.http()
      service = discovery.build("drive", "v2", http=http)
      drive_file = service.files().get(fileId=fileId).execute(http=http)
      
      code_file = self.download_file(service, drive_file)
      code = code_file.decode('utf8')[1:]
      code = code.replace(u'”','"')
      code = code.replace(u'“','"')
      code = code.replace(u'’','\'')
      code = code.replace(u'‘','\'')
      self.render('process.html', dict(code = code))
    except client.AccessTokenRefreshError:
      self.redirect('/')
      
      
app = webapp2.WSGIApplication([
                                ('/', IndexHandler),
                                ('/process', ProcessHandler), 
                                (decorator.callback_path, decorator.callback_handler())
                              ], debug=True)
