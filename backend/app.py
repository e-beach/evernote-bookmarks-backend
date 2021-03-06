import os
import config
from flask import Flask, request, session, redirect
from flask_cors import cross_origin

import _evernote as evernote

app = Flask(__name__)

# encrypt our sessions with the secret.
app.secret_key = config.secret_key

def get_hostname(request):
    host = request.headers['Host']
    protocol = request.url.split('/')[0] + '//'
    return protocol + host

@app.route('/')
def index():
    res = "Evernote Note Creator!"
    return res

@app.route('/bookmarks')
def bookmarks():
    res = "Loading your bookmarks!"
    return res

### <Authentication> ###

@app.route('/auth')
def auth():
    callbackUrl = get_hostname(request) + '/auth_callback'
    client = evernote.auth_client()
    request_token = client.get_request_token(callbackUrl)
    # Save the request token information for later
    session['oauth_token'] = request_token['oauth_token']
    session['oauth_token_secret'] = request_token['oauth_token_secret']
    # Redirect the user to the Evernote authorization URL
    return redirect(client.get_authorize_url(request_token))


@app.route('/auth_callback')
def callback():
    try:
        client = evernote.auth_client()
        access_token = client.get_access_token(
            session['oauth_token'],
            session['oauth_token_secret'],
            # The oauth_verifier will == None if user declined to authorize.
            request.args.get('oauth_verifier', '')
        )
    except KeyError:
        return redirect('/')
    session['access_token'] = access_token
    return redirect('/bookmarks')

### <\Authentication> ###


@app.route('/create', methods=['POST'])
@cross_origin(origin=config.ALLOWED_ORIGIN)
def create():
    token = session.get('access_token')
    if not token:
        return 'Access Denied', 403
    note_client = evernote.NoteClient(token)
    try:
        notebook_uid = note_client.get_notebook('Bookmarks').guid
    except evernote.NoteBookNotFoundError:
        notebook_uid = note_client.create_notebook('Bookmarks')
    bookmarks = request.json
    note_client.send_bookmarks(bookmarks, notebook_uid)
    return 'OK'

if __name__ == "__main__":
	app.run(port=config.port)
