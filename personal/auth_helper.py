# import yaml
from requests_oauthlib import OAuth2Session
import os,sys
import time


print(sys.path)
# This is necessary for testing with non-HTTPS localhost
# Remove this if deploying to production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# This is necessary because Azure does not guarantee
# to return scopes in the same case and order as requested
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

# Load the oauth_settings.yml file

app_id = "7dc6285a-83e3-4a27-a883-fc01a006c93c"
app_secret = "UVX1.1g77MT3E3f.HmNzZlDP.uh3mG9~QF"
redirect =  "http://localhost:8000/callback"
scopes = "openid profile offline_access user.read calendars.read"
authority = "https://login.microsoftonline.com/common"
authorize_endpoint = "/oauth2/v2.0/authorize"
token_endpoint=  "/oauth2/v2.0/token"

# settings = open('oauth_settings.yml', 'r')
# settings = yaml.load(stream, yaml.SafeLoader)
authorize_url = '{0}{1}'.format(authority, authorize_endpoint)
token_url = '{0}{1}'.format(authority, token_endpoint)

# Method to generate a sign-in url
def get_sign_in_url():
  # Initialize the OAuth client
  aad_auth = OAuth2Session(app_id,
    scope=scopes,
    redirect_uri=redirect)

  sign_in_url, state = aad_auth.authorization_url(authorize_url, prompt='login')
  #print(sign_in_url)

  return sign_in_url, state

# Method to exchange auth code for access token
def get_token_from_code(callback_url, expected_state):
  # Initialize the OAuth client
  aad_auth = OAuth2Session(app_id,
    state=expected_state,
    scope=scopes,
    redirect_uri=redirect)

  token = aad_auth.fetch_token(token_url,
    client_secret = app_secret,
    authorization_response=callback_url)

  return token

def store_token(request, token):
      request.session['oauth_token'] = token

def store_user(request, user):
  request.session['user'] = {
    'is_authenticated': True,
    'name': user['displayName'],
    'email': user['mail'] if (user['mail'] != None) else user['userPrincipalName']
  }



def get_token(request):
  token = request.session['oauth_token']
  if token != None:
    # Check expiration
    now = time.time()
    # Subtract 5 minutes from expiration to account for clock skew
    expire_time = token['expires_at'] - 300
    if now >= expire_time:
      # Refresh the token
      aad_auth = OAuth2Session(app_id,
        token = token,
        scope=scopes,
        redirect_uri=edirect)

      refresh_params = {
        'client_id': app_id,
        'client_secret': app_secret,
      }
      new_token = aad_auth.refresh_token(token_url, **refresh_params)

      # Save new token
      store_token(request, new_token)

      # Return new access token
      return new_token

    else:
      # Token still valid, just return it
      return token

def remove_user_and_token(request):
  if 'oauth_token' in request.session:
    del request.session['oauth_token']

  if 'user' in request.session:
    del request.session['user']