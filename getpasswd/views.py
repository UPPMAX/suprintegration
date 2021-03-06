from django.shortcuts import render
import django.http
import ConfigParser
import supr
import time
import logging

from django.template import loader, Context

# Create your views here.

UPPMAX_ID = 4
SPOOL_DIR = "/var/spool/getpasswd/"
TIMEOUT = 300
LOGGER_NAME = "getpasswd"

cp = ConfigParser.ConfigParser()
cp.read('/etc/supr.ini')



def index(request):
    
    request.session['start'] = time.time()
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

    if not 'start' in request.session.keys() or time.time()-request.session['start'] > TIMEOUT:
        return django.http.HttpResponseRedirect('/getpasswd/')

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
            # Look for rackham account for now
            if p['resource']['id'] == 51:
                account = p['username']

        if account:

            f = open('%s/%s-%f' % (SPOOL_DIR, account, time.time()), 'w')
            f.write('%s\n' % account)
            f.close()

            logging.getLogger(LOGGER_NAME).info("New password requested for user %s" % (account))

            return render(request, 'getpasswd/message.html', {'title': 'New password requested', 
                                                              'message':'A new password will be sent to %s shortly.' % account })

        syslog.syslog(syslog.LOG_INFO, "New password requested for supr id %d but no local account found." % (r['person']['id']))
        return render(request, 'getpasswd/message.html', 
                      {'title': 'No user found in SUPR', 
                       'message':'We looked as best we could, but we '  +
                       'could not find an UPPMAX user corresponding to '+ 
                       'your SUPR identity. Please contact support@uppmax.uu.se ' +
                       'and ask that they link your UPPMAX account to your SUPR ' +
                       'identity.'
                   })
                   
    
    except Exception:
        logging.getLogger(LOGGER_NAME).error("Failure while finishing password request, this is what we know: %s" % ( str(request.session)))

    return render(request, 'getpasswd/message.html', {'title': 'An error occured',                                                                                                            
                                                          'message':'An error occured during the password request, please retry.'})

