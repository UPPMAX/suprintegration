from django.shortcuts import render
import django.http
import ConfigParser
import supr

import random
import base64

import qrcode

import django.forms
import qrcode.image.svg

import hmac, base64, struct, hashlib, time

import logging

UPPMAX_ID = 4
TOKEN_LEN = 25

# How long may a session be open?
TIMEOUT = 300

# How much error allowed in clock (times 30 seconds)
TIMEWINDOW = 3 

cp = ConfigParser.ConfigParser()
cp.read('/etc/supr.ini')

ctab = [ unichr(x) for x in range(48,127)]

SPOOL_DIR = "/var/spool/bootstrapotp/"

LOGGER_NAME = "bootstrapotp"

# Utitlity functions
# Some code taken from
# http://stackoverflow.com/questions/8529265/google-authenticator-implementation-in-python
#



def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = ord(h[19]) & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return h

def get_totp_token(secret):
    return get_hotp_token(secret, intervals_no=int(time.time())//30)

def verify_totp_token(secret, window, given_token):
  for p in range(-window,window+1):
      calc = get_hotp_token(secret, intervals_no=int(time.time())//30+p)

      if int(given_token) == calc:
          return True

  return False





def index(request):
    
    try:
        s = supr.SUPR(cp.get('SUPR','user'),
                      cp.get('SUPR','password'),
                      cp.get('SUPR','url'))
    
        d = { 'return_url': 'https://suprintegration.uppmax.uu.se/bootstrapotp/back',
              'message': 'UPPMAX wants to know who the OTP token is for.'
          }

        r = s.post('/centreauthentication/initiate/', d)
    
        request.session['token'] = r['token']
        request.session['start'] = int(time.time())

        return django.http.HttpResponseRedirect(r['authentication_url'])
    except Exception,p:
        return render(request, 'bootstrapotp/base.html', {'title': 'An error occured',                                                                                                            
                                                         'message':'An error occured during OTP bootstrap, please retry.'})


class totpForm( django.forms.Form ):
    code = django.forms.IntegerField(widget=django.forms.TextInput, max_value=int(1e7))

def back(request):

    if not 'token' in request.session.keys()  or not 'token' in request.GET.keys() or request.session['token'] != request.GET['token']:
        return django.http.HttpResponseRedirect('/bootstrapotp/')

    if not 'start' in request.session.keys() or time.time()-request.session['start'] > TIMEOUT:
        return django.http.HttpResponseRedirect('/bootstrapotp/')

    try:

        s = supr.SUPR(cp.get('SUPR','user'),
                      cp.get('SUPR','password'),
                      cp.get('SUPR','url'))
    

        d = { 'token': request.session['token'] }
        del request.session['token']

        r = s.post('/centreauthentication/check/', d)
   
        account = None
        
        for p in r['person']['accounts']:
            if p['resource']['centre']['id'] == 4:
                account = p['username']
                
        
        if account:
            secret = u''.join(random.SystemRandom().choice(ctab) for _ in range(TOKEN_LEN))
            b32secret = base64.b32encode(secret)
            request.session['secret'] = b32secret
            request.session['account'] = account
            return render(request, 'bootstrapotp/showandverify.html', {'title': 'TOTP ', 
                                                                       'message':'',
                                                                       'form': totpForm() })

    except Exception:
        pass

    return render(request, 'bootstrapotp/base.html', {'title': 'An error occured',                                                                                                            
                                                         'message':'An error occured during OTP bootstrap, please retry.'})


def image(request):
    if not 'start' in request.session.keys() or time.time()-request.session['start'] > TIMEOUT:
        return django.http.HttpResponseRedirect('/bootstrapotp/')

    if not 'secret' in request.session.keys() or not 'account' in request.session.keys():
        return django.http.HttpResponseRedirect('/bootstrapotp/')

    urlsecret = request.session['secret']
    account = request.session['account']
    url = "otpauth://totp/%s@SNIC-SENS?secret=%s&issuer=UPPMAX" % (account, urlsecret)
  
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)        

    response = django.http.HttpResponse(mimetype="image/svg+xml")
    img.save(response, "SVG")
    return response



def finish(request):
    if not 'start' in request.session.keys() or time.time()-request.session['start'] > TIMEOUT:
        return django.http.HttpResponseRedirect('/bootstrapotp/')

    if not 'secret' in request.session.keys() or not 'account' in request.session.keys():
        return django.http.HttpResponseRedirect('/bootstrapotp/')

    account = request.session['account']

    totp = totpForm(request.POST)

    if not totp.is_valid() or not 'code' in totp.cleaned_data.keys():
        return django.http.HttpResponseRedirect('/bootstrapotp/')

    if not verify_totp_token(request.session['secret'], TIMEWINDOW, totp.cleaned_data['code']):

        return render(request, 'bootstrapotp/showandverify.html', {'title': 'TOTP ', 
                                                                   'message':'That was not correct, please retry.',
                                                                   'form': totpForm() })



    try:
        f = open('%s/%s-%f' % (SPOOL_DIR, account, time.time()), 'w')
        f.write('%s %s\n' % (account, request.session['secret']))
        f.close()
    except:
        return render(request, 'bootstrapotp/base.html', 
                      {'title': 'OTP token registration failed', 
                       'message':'Thanks for verifying, unfortunately, ' +
                    'we could not record your token. Please retry later.' })

    del request.session['secret']

    logging.getLogger(LOGGER_NAME).info("New OTP registered for user %s" % (account))

    return render(request, 'bootstrapotp/base.html', 
                  {'title': 'OTP token registered', 
                   'message':'Thanks for verifying, ' +
                   'your OTP token will be registered.' })
    
