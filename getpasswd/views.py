from django.shortcuts import render
import django.http
import ConfigParser
import supr
import time

from django.template import loader, Context

# Create your views here.

UPPMAX_ID = 4
SPOOL_DIR = "/var/spool/getpasswd/"

cp = ConfigParser.ConfigParser()
cp.read('/etc/supr.ini')

def index(request):
    
    try:
        s = supr.SUPR(cp.get('SUPR','user'),
                      cp.get('SUPR','password'),
                      cp.get('SUPR','url'))
    
        d = { 'return_url': 'https://suprintegration.uppmax.uu.se/getpasswd/back',
              'message': 'UPPMAX wants to know who to send the new password to.'
          }

        r = s.post('/centreauthentication/initiate/', d)

    
        request.session['token'] = r['token']   

        return django.http.HttpResponseRedirect(r['authentication_url'])
    except Exception,p:
        return render(request, 'getpasswd/message.html', {'title': 'An error occured',                                                                                                            
                                                         'message':'An error occured during the password request, please retry.'})

def back(request):

    try:
        s = supr.SUPR(cp.get('SUPR','user'),
                      cp.get('SUPR','password'),
                      cp.get('SUPR','url'))
    
        if not 'token' in request.session.keys() or request.session['token'] != request.GET['token']:
            return django.http.HttpResponseRedirect('/getpasswd/')

        d = { 'token': request.session['token'] }

        del request.session['token']
        r = s.post('/centreauthentication/check/', d)
   
        account = None
        
        for p in r['person']['accounts']:
            if p['resource']['centre']['id'] == 4:
                account = p['username']

        if account:

            f = open('%s/%s-%f' % (SPOOL_DIR, account, time.time()), 'w')
            f.write('%s\n' % account)
            f.close()

            return render(request, 'getpasswd/message.html', {'title': 'New password requested', 
                                                                      'message':'A new password will be sent to %s shortly.' % account })

    
    except Exception:
        pass

    return render(request, 'getpasswd/message.html', {'title': 'An error occured',                                                                                                            
                                                          'message':'An error occured during the password request, please retry.'})

