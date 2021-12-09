import logging, os, requests, traceback, datetime, json
from . import models, helpers, make_json_serializable
from django.core import serializers
from django.shortcuts import render, redirect
from django.http.response import HttpResponseServerError, JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.template import RequestContext
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.mail import EmailMultiAlternatives#send_mail
from django.db import transaction
from os import listdir
from os.path import isfile, join
from mysite import constants

logger = logging.getLogger(__name__)

# Create your views here.
def loginview(req, error=None):
    # q = ('https://accounts.google.com/o/oauth2/auth'
    #     '?response_type=code'
    #     '&client_id={0}'
    #     '&redirect_uri={1}'
    #     '&scope=openid%20profile%20email'
    #     '&login_hint=email'
    #     '&hd=redtone.com'
    #     '&state={2}')

    sign_in_url, state = get_sign_in_url()
    print(sign_in_url)
    q = sign_in_url
  # Save the expected state so we can validate in the callback
    req.session['auth_state'] = state
  # Redirect to the Azure sign-in page
  #return HttpResponseRedirect(sign_in_url)
    nexturl = req.GET.get('next', 'home')
    url = q.format(nexturl)
    ctx = {
        'next': nexturl,
        'url': url,
        'debug': settings.DEBUG
    }
    if error is not None:
        ctx['error'] = error
        
    return render(req, 'personal/login.html', context=ctx)

@login_required
def home(request):
    try:
        q, o = helpers.getsearchquery(request)
        
        opened = helpers.countlist(0)
        approved = helpers.countlist(4)
        rejected = helpers.countlist(2)
        cancel = helpers.countlist(3)
        rndapproved = helpers.countlist(1)
        inprogress = helpers.countlist(5)
        settle = helpers.countlist(6)

        ctx = {
            'open': opened,
            'approve': approved,
            'reject': rejected,
            'rndapproved':rndapproved,
            'inprogress' : inprogress,
            'done' : settle,
            #'list': reqlistx,
            #'querylist' : ai,
            
        
        }
        

        return render(request, 'personal/home.html', context=ctx)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

def oauthcallback(req):
    # code = req.GET.get('code')
    # state = req.GET.get('state')
    # url = 'https://ccaccounts.google.com/o/oauth2/token'
    # k = {
    #     'code': code,
    #     'client_id': settings.CLIENT_ID,
    #     'client_secret': settings.CLIENT_SECRET,
    #     'redirect_uri': settings.REDIRECT_URI,
    #     'grant_type': 'authorization_code'
    # }
    # r = requests.post(url, data=k)
    # d = r.json()
    
    # url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    # k = {
    #     'access_token': d.get('access_token')
    # }
    # r = requests.get(url, params=k)
    # m = r.json()
  expected_state = req.session.pop('auth_state', '')
  # Make the token request
  token = get_token_from_code(req.get_full_path(), expected_state)

  # Get the user's profile
  user_m = get_user(token)
  print(user_m)

  # Save token and user
  store_token(req, token)
  store_user(req, user_m)

  #return HttpResponseRedirect(reverse('home'))

#   if 'email' in user_m:
  email = user_m['mail']
  print(email)
    
  try:
   user = authenticate(email=email)

   if user is None:
    return loginview(req, 'Invalid login')

   if user.email is not None:
    login(req, user)
    req.session['email'] = user_m
    nexturl = 'home' if expected_state in [None, 'None'] else expected_state
    #return redirect(nexturl)
    return HttpResponseRedirect(reverse('home'))

    
  except Exception as e:
    logger.exception(str(e))
    return loginview(req, traceback.format_exc())

  return loginview(req, 'Invalid login')


def auth(req):
    try:
        email = req.POST.get('email')
        nexturl = req.POST.get('next', 'home')

        user = authenticate(email=email)

        if user is not None:
            login(req, user)
            if nexturl in [None, 'None']:
                nexturl = 'home'

            return redirect(nexturl)

    except Exception as e:
        logger.exception(e)
        return loginview(req, traceback.format_exc())

    return loginview(req, 'Invalid login')

def logoff(request):
    logout(request)
    return redirect('loginview')

@login_required
def create(request, o=None, showsubmit=False):
    ctx = {
        'applist': models.App.objects.all().order_by('name'),
        'userlist': models.User.objects.filter(dept="rnd"),
        'apprvlist': models.User.objects.filter(is_approver=True),
        'assignlist': models.Assign.objects.filter(req_id=o.id) if o is not None else [],
        'userlistx': models.User.objects.all().order_by('dept'),
        'listtemp': models.ReqForm.objects.filter(reqstatus=9).filter(assignto=request.user.id) #if o is not None else []

    }

    #print(ctx)
    if showsubmit:
        ctx['showsubmit'] = showsubmit
        
    if o is not None:
        ctx['model'] = o

    else:
        #o = models.ReqForm.objects.filter(assignto=request.user.id).filter(reqstatus=9)
        o = models.ReqForm.objects.filter(reqstatus=9).filter(assignto=request.user.id)
        o.reqstatus = 0
        ctx['model'] = o

    return render(request, 'personal/form.html', context=ctx)

@login_required
def tempcreate(request):
    
    if request.method == 'POST':
        try:
            o = models.ReqForm()
            o.requser = models.User.objects.get(pk=request.user.id)
            o.setfromdic(request.POST)

            
            if len(o.assignto) == False:
                #print(o.assignto)
                messages.add_message(request, messages.ERROR, 'Assign to field is Required')
                return tempsubmit(request,o)

            o.reqstatus = 9
            o.vstatus = 1
    
            o.save()

            messages.add_message(request, messages.SUCCESS, 'Your Draft Has been Saved!!')   

            
        except Exception as e:
            #logger.exception(str(e))
            return HttpResponseServerError(traceback.format_exc())
    #return render(request, 'personal/tempform.html', context=ctx)
    return tempsubmit(request)



@login_required
def tempsubmit(request, o=None, showsubmit=False):
    
    ctx = {
        'applist': models.App.objects.all().order_by('name'),
        #'userlist': models.User.objects.filter(dept="rnd"),
        'userlistx': models.User.objects.all().order_by('dept'),
        'apprvlist': models.User.objects.filter(is_approver=True),
        'assignlist': models.Assign.objects.filter(req_id=o.id) if o is not None else [],
        'listtemp': models.ReqForm.objects.filter(assignto=request.user.id) #if o is not None else []

    }
    if showsubmit:
        ctx['showsubmit'] = showsubmit
        
    if o is not None:
        ctx['model'] = o

    else:
        o = models.ReqForm()
        o.reqstatus = 9
        ctx['model'] = o

    return render(request, 'personal/tempform.html', context=ctx)


@login_required
def viewtemplist(req):
        q, o = helpers.getsearchquerytemp(req)

        return render(req, 'personal/viewtemplist.html')

def templist(req):
    try:
        q, o = helpers.getsearchquerytemp(req)

        pagenum = int(req.GET.get('pagenum', 1)) #return1
        pagesize = constants.PAGE_SIZE #return 5record

        total = q.count() #return 8
        pager = models.Pager(total, pagenum, pagesize)
        reqlistx = models.ReqForm.objects.filter(requser_id=req.user.id).filter(reqstatus=9).order_by('-reqdate')
        #print(req.user.id)
        #usedlist = models.tempform.objects.filter(creator=req.user.id).order_by('-createddate')


        page_length = range(1, total)
        ctx = {
            'listed': reqlistx,
            #'usedlist': usedlist,
            'paging': pager,
            'total': total,
            'plen' : page_length
        }
        if o is not None:
            ctx['search'] = o

        return render(req, 'personal/templatelist.html', context=ctx)

        
    except Exception as e:
        #logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
@transaction.atomic
def submit(req):
    if req.method == 'POST':
        try:
           
            o = models.ReqForm()
            o.requser = models.User.objects.get(pk=req.user.id)
            o.setfromdic(req.POST)
          
            le = o.validate()
            if len(le) > 0:
                s = render_to_string('personal/_errorlist.html', { 'errorlist': le })
                messages.add_message(req, messages.ERROR, s)
                return create(req, o)
               
            o.reqstatus = 0
            o.vstatus = 1
            #z = models.logact()
            o.save()
  
            
            helpers.movefile(o, req)                   

            email = o.approver.email

            
            dic = {
                'o': o,
                'url': settings.EDIT_URI
            }
            
            sendemail(render_to_string('personal/email.html', dic), email, '')


            messages.add_message(req, messages.SUCCESS, 'Your Request Has been Submitted!!')   

        except Exception as e:
            logger.exception(str(e))
            return HttpResponseServerError(traceback.format_exc())

        return redirect('create')
            
    return create(req)

@login_required
def createcomment(req, pid):
    if req.method == 'POST':
        try:
            o = models.comment()

            o.email = req.POST.get('email')
            o.appsid = pid# req.POST.get('appsid')
            o.comment = req.POST.get('comment')
           
            #print o.appsid 
            o.save()
           

        except Exception as e:
            logger.exception(str(e))
            return HttpResponseServerError(traceback.format_exc())

        #return redirect('comment')
            
    return comment(req,pid)
        
    

@login_required
def list(req):
    try:
        q, o = helpers.getsearchquery(req)

        pagenum = int(req.GET.get('pagenum', 1)) #return1
        pagesize = constants.PAGE_SIZE #return 5record

        total = q.count() #return 8
        pager = models.Pager(total, pagenum, pagesize) 

        reqlistx = q.all().order_by('-reqdate')[pager.lowerbound:pager.upperbound]
        #reqlistuser = q.all().filter(requser_id=pid).order_by('-reqdate')[pager.lowerbound:pager.upperbound]
        

        page_length = range(1, total)
        ctx = {
            #'list': reqlistuser,
            'listed': reqlistx,
            'paging': pager,
            'total': total,
            'plen' : page_length
        }
        #print reqlistuser
        if o is not None:
            ctx['search'] = o

        #return render(req,'personal/historylist.html', context=ctx)
        return render(req, 'personal/list.html', context=ctx)

        
    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())
        #return render(req, 'personal/list.html')

@login_required
def search(req):
    if req.method == 'POST':
        try:
            o = models.Search()
            o.setfromdic(req.POST)
            #print o.statuslist
            #a = models.ReqForm.objects.filter(requser_id=pid)
            #ai = models.ReqForm.objects.filter(app_id=pid).order_by('-reqdate')

            
            if o.isempty and req.session.has_key('search'):
                del req.session['search']

            elif not o.isempty:
                req.session['search'] = o

            return redirect('list')#, pid=requser.id 
     
        except Exception as e:
            logger.exception(str(e))
            #return render(req, 'personal/list.html')
            return HttpResponseServerError(traceback.format_exc())

    return SuspiciousOperation()

def history(req, pid):
    try:
        ai = models.logact.objects.filter(log_req_id=pid).order_by('-log_time')
        
        #c = models.User.objects.get(pk=a.user_id)

        ctx = {
            'list': ai,
            #'user': c
            
        }
      
        return render(req, 'personal/historylist.html', context=ctx)


    except Exception as e:
        #logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())


def comment(req, pid):
    try:
        ai = models.comment.objects.filter(appsid=pid).order_by('-date')

        ctx = {
            'list': ai
            
        }  

        return render(req, 'personal/comment.html', context=ctx)


    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def download(req):
    try:
        b = helpers.queryexcellist(req)
        r = helpers.sendfile(b, 'request_list.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        return r

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def edit(req, pid):
    Flag = False
    try:
       
        matched = False
        a = models.ReqForm.objects.get(pk=pid)
        b = models.Assign.objects.filter(req_id=pid)
        #print b
        if b is None: b = []
        for x in b:
            if x.assignto == req.user.email:
                matched = True

        if a.requser.id == req.user.id and  a.reqstatus == 0 or a.requser.id == '' or a.reqstatus == 9:
            Flag = True
        elif  matched == True and a.reqstatus < 6 :
            Flag = True
        elif req.user.is_approver and req.user.id == a.approver_id and  a.reqstatus == 0:
            Flag = True
        elif req.user.id == 10 and  a.reqstatus == 4:
            Flag = True

        #print b
        ctx = {
           'list': a

          
        }  
        return create(req, a, showsubmit=Flag)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def getedittemplatedata(req, pid):
    res = {}

    try:
        a = models.ReqForm.objects.get(pk=pid)
        #b = models.Assign.objects.filter(req_id=pid)
        c = models.User.objects.get(pk=a.requser_id)
        d = models.App.objects.get(pk=a.app_id)


        k = serializers.serialize('json', [a])
        j = json.loads(k)
        model = j[0]

        #k = serializers.serialize('json', b)
        #j = json.loads(k)
        #assign = j[0]

        k = serializers.serialize('json', [c])
        j = json.loads(k)
        user = j[0]

        k = serializers.serialize('json', [d])
        j = json.loads(k)
        app = j[0]

      
        if a.reqstatus == 1:
            status = 'Approved by RND'

        elif a.reqstatus == 2:
            status = 'Rejected'

        elif a.reqstatus == 3:
            status = 'Cancel'

        elif a.reqstatus == 4:
            status = 'Approved by Head'

        elif a.reqstatus == 5:
            status = 'In Progress'

        elif a.reqstatus == 6:
            status = 'Fixed/Done'

        elif a.reqstatus == 9:
            status = 'Draft'

        res = {
            'model': model,
            #'assign': assign,
            'user': user,
            'app': app,
            'status': status,
            'success': 1
            
        }

    except Exception as e:
        logger.exception(e)
        res['error'] = 1
        res['message'] = traceback.format_exc()

    return JsonResponse(res)

@login_required
def edittemplate(req, pid):
    
    try:
       
        a = models.ReqForm.objects.get(pk=pid)
        b = models.Assign.objects.filter(req_id=pid)

        #print b
        ctx = {
           'list': a
        }  
        #print (a)
        return tempsubmit(req, a)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def edittemplate2(req, pid):
    
    try:
       
        a = models.tempform.objects.get(pk=pid)
        b = models.Assign.objects.filter(req_id=pid)

        #print b
        ctx = {
           'list': a
          
        }  
        #print (a)
        return tempsubmit(req, a)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def assign(req, pid):
    try:
        ai = models.Assign.objects.filter(req_id=pid)
        
        ctx = {
            'list': ai
            
        }  

        return render(req, 'personal/form_drop.html', context=ctx)
        #return render(req, context=ctx)
        #return create(req, a)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def update(req, pid):
    if req.method == 'POST':

        try:
            o = models.ReqForm.objects.get(pk=int(pid))
            if o.reqstatus == 6 or  o.reqstatus == 2 or o.reqstatus == 3 :
                messages.add_message(req, messages.ERROR, 'You are not allowed to change the status after APPROVE/REJECT/CANCEL')
                return redirect('list')


            o.setfromdic(req.POST)
            email = o.requser.email
            rndemail = 'mingching.tiew@redtone.com'#'mingching.tiew@redtone.com'
           
            
            b = models.Assign()#.objects.get(req_id=int(pid))
            b.setfromdic(req.POST)
            b.req_id = o.id
            success_noti = b.assignto #b.assigntolist
            o.vstatus = 1
        
            log = models.logact()
            log.setfromdic(req.POST)

            assignemail = ', '.join(str(e) for e in success_noti)
            
            
            if o.reqstatus == 4:
                    dic = {
                        'o': o,
                        'url': settings.EDIT_URI
                    }

                    log.log_action ='Request approved by Head Department '
                    log.log_req_id = o.id
                    log.user_id = req.user.id
                    log.name = req.user.username

                    
                    sendemail(render_to_string('personal/_noti.html', dic), rndemail,'') #rnd approver
                    sendemail(render_to_string('personal/note.html', dic), email,'') #requestor 

            elif o.reqstatus == 9: 
                o.requser = models.User.objects.get(pk=req.user.id)
                o.assignto =req.user.id
               
                le = o.validate()
                if len(le) > 0:
                    s = render_to_string('personal/_errorlist.html', { 'errorlist': le })
                    messages.add_message(req, messages.ERROR, s)
                    return create(req, o)
                else:
                    dic = {
                            'o': o,
                            'url': settings.EDIT_URI
                        }

                    
                    o.reqstatus = 0
                    o.vstatus = 1

                    m = models.tempform()
                    #m.setdic(req.POST)
                    m.req_id = o.id
                    m.creator= o.requser.id
                    m.app_name = o.app_id
                    m.assigntoid= o.assignto
                    m.approver = o.approver.id
                    m.title= o.title
                    m.description= o.description
                    m.remark = o.remark
                    m.createddate = o.reqdate
                    m.tempstatus= 10
                    m.save()
                    head = o.approver.email

                    log.log_action ='Modify draft to request.'
                    log.log_req_id = o.id
                    log.user_id = req.user.id
                    log.name = req.user.username


                    sendemail(render_to_string('personal/_noti.html', dic), head,'')

            
            
            elif o.reqstatus == 1:
                head = o.approver.email  
                if len(assignemail) == False:
                    o.reqstatus = 4
                    
                    messages.add_message(req, messages.ERROR, 'Assign to field is Required')
                    return create(req,o)
                else:

                    dic = {
                        'o': o,
                        'url': settings.EDIT_URI
                    } 
                   

                    i = 0 
                    for index in range(len(success_noti)):
                        sendemail(render_to_string('personal/notification.html', dic),  success_noti[index], '') 
                    while (i < len(success_noti)):
                            w = models.Assign()
                            w.setdic(req.POST)
                            w.req_id = o.id
                            w.assignto = success_noti[i]
                            w.save()

                            i = i + 1   
                    log.log_action ='Request approved by RND Head '
                    log.log_req_id = o.id
                    log.user_id = req.user.id
                    log.name = req.user.username

                    
                    sendemail(render_to_string('personal/note.html', dic), email, head)
            
            elif o.reqstatus == 2:
                    dic = {
                        'o': o,
                        'url': settings.EDIT_URI
                    }
                    
                    log.log_action ='Request rejected by '
                    log.log_req_id = o.id
                    log.user_id = req.user.id
                    log.name = req.user.username

                    sendemail(render_to_string('personal/note.html', dic), head, email)     


            elif o.reqstatus == 6:#complete
                    dic = {
                        'o': o,
                        'url': settings.EDIT_URI
                    }
                    o.completeddate =datetime.datetime.now()
                    
                    
                    log.log_action ='Request completed by '
                    log.log_req_id = o.id
                    log.user_id = req.user.id
                    log.name = req.user.username
                    sendemail(render_to_string('personal/workdone_verify.html', dic), email, '') #requestor

            elif o.reqstatus == 5:#complete
                    dic = {
                        'o': o,
                        'url': settings.EDIT_URI
                    }
                    
                    
                    log.log_action ='Request in progress.Update by'
                    log.log_req_id = o.id
                    log.user_id = req.user.id
                    log.name = req.user.username
            log.save()
            o.save()
           

            
            messages.add_message(req, messages.SUCCESS, 'Successfully Update!!')
            
                 
            return redirect('list')

        except Exception as e:
            #logger.exception(str(e))
            return HttpResponseServerError(traceback.format_exc())

    return SuspiciousOperation()

@login_required
def pushnotify(req, pid):
    try:
        o = models.ReqForm.objects.get(pk=int(pid))
       
        email = o.requser.email
        rndemail = 'mingching.tiew@redtone.com'
        head = o.approver.email


        messages.add_message(req, messages.SUCCESS, 'Notification Sent!!')

        if o.reqstatus == 4:
                dic = {
                    'o': o,
                    'url': settings.EDIT_URI
                }
               
                sendemail(render_to_string('personal/pushnoti.html', dic), rndemail, email) #rnd approver

                
        elif o.reqstatus == 0:
                dic = {
                    'o': o,
                    'url': settings.EDIT_URI
                }
               
                sendemail(render_to_string('personal/pushnoti.html', dic), head, email)#head approver

        elif o.reqstatus == 1:
                dic = {
                    'o': o,
                    'url': settings.EDIT_URI
                }
                b = models.Assign.objects.get(req_id=int(pid))
                success_noti = b.assignto
               
                sendemail(render_to_string('personal/notification.html', dic), success_noti, '')

          

        return redirect('list')

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

    return SuspiciousOperation()

@login_required
def verified(req, pid):
    try:
        o = models.ReqForm.objects.get(pk=int(pid))
        o.verified= 1
        o.save()
        messages.add_message(req, messages.SUCCESS, 'Verification Done!!')

        b = models.Assign.objects.get(req_id=int(pid))
        success_noti = b.assignto

        log = models.logact()
        log.setfromdic(req.POST)

        if o.reqstatus == 6:
                dic = {
                    'o': o,
                    'b': b,
                    'url': settings.EDIT_URI
                }

                sendemail(render_to_string('personal/verification.html', dic), success_noti, '')

                log.log_action ='Has been verified by'
                log.log_req_id = o.id
                log.user_id = req.user.id
                log.name = req.user.username

        log.save()

        return redirect('list')

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

    return SuspiciousOperation()





def verify_reminder(req):
    try:
        b = helpers.verify_filter(req)
        print(b)
       
        for o in b:

            email = o.requser.email

            a = models.User.objects.get(id=o.approver_id)
            head = a.email

            log = models.logact()
            log.setfromdic(req.POST)

            
            
            if o.reqstatus == 6 :
                    dic = {
                        'o': o,
                        'url': settings.EDIT_URI
                    }
                    if o.verified == 0 :
                        #log.user_id = 'Auto Sytem Generated'
                        #log.name = a.username

                        log.log_action ='Reminder to perform verification has been sent!'
                        log.log_req_id = o.id
                        log.user_id = 'Auto Sytem Generated'
                        log.name = o.requser.username

                        log.save()
                       # print(o.id)
                        sendemail(render_to_string('personal/autonotiuser.html', dic), email, '')#verified pending
                    

        ctx = {
            'listed': b
        }
 
        return render(req, 'personal/templatelist.html', context=ctx)

        
    except Exception as e:
        return HttpResponseServerError(traceback.format_exc())


def auto_verified(req):
    try:
        b = helpers.autov_filter(req)
        listverified = b.all().order_by('-completeddate')

        #print(listverified)
       
        for o in b:

            email = 'ainur.fadzil@redtone.com'

            log = models.logact()
            log.setfromdic(req.POST)
         
            if o.reqstatus == 6 :
                    dic = {
                        'o': o,
                        'listed':listverified,
                        'url': settings.EDIT_URI
                    }
                    if o.verified == 0 :
                        #log.user_id = 'Auto Sytem Generated'
                        #log.name = a.username
                        o.verified =1
                        
                        log.log_action ='Auto verified performed!'
                        log.log_req_id = o.id
                        log.user_id = 'System Generated'
                        log.name = 'By System'

                        log.save()
                        o.save()
                        #print(o.id)
                        
                        
                        
        sendemail(render_to_string('personal/autoverifiedlist.html', dic), email, '')#verified alert
                    

        ctx = {
            'listed':listverified
        }
 
        return render(req, 'personal/autoverifiedlist.html', context=ctx)

        
    except Exception as e:
        return HttpResponseServerError(traceback.format_exc())

@login_required
def cancelstatus(req, pid):
    try:
        o = models.ReqForm.objects.get(pk=int(pid))
        o.reqstatus = 3
        o.save()

        messages.add_message(req, messages.SUCCESS, 'Your request has been successfully Cancelled!!')
        return redirect('list')

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def uploadcreate(req):
    if req.method == 'POST':
        try:
            x = req.FILES.get('file')
            if x is not None:
                path = join(settings.TMP_UPLOAD_PATH, helpers.getuserdir(req))
                helpers.upload_file(req, path)

            return redirect('uploadcreatelist')

        except Exception as e:
            logger.exception(str(e))
            return HttpResponseServerError(traceback.format_exc())
        
    return SuspiciousOperation()

@login_required
def uploadcreatelist(req):
    try:
        path = join(settings.TMP_UPLOAD_PATH, helpers.getuserdir(req))

        if not os.path.exists(path):
            filelist = []
            
        else:
            filelist = [f for f in listdir(path) if isfile(join(path, f))]
            
        ctx = {
            'list': filelist,
            'id': 0
        }
        return render(req, 'personal/uploadfilelist.html', context=ctx)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def uploadedit(req, pid):
    if pid is not None and req.method == 'POST':
        try:
            path = join(settings.UPLOAD_PATH, helpers.getreqdir(pid))
            filename = helpers.upload_file(req, path)

            x = models.ReqFile()
            x.reqform_id = int(pid)
            x.filename = filename
            x.uploaduser_id = req.user.id
            x.save()
            
            return redirect('uploadeditlist', pid=pid)

        except Exception as e:
            logger.exception(str(e))
            return HttpResponseServerError(traceback.format_exc())

    return SuspiciousOperation()

def uploadeditlist(req, pid):
    try:
        path = join(settings.UPLOAD_PATH, helpers.getreqdir(pid))

        if not os.path.exists(path):
            filelist = []

        else:
            filelist = [f for f in listdir(path) if isfile(join(path, f))]

        ctx = {
            'list': filelist,
            'id': pid
        }
        return render(req, 'personal/uploadfilelist.html', context=ctx)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def getuploadfile(req):
    try:
        fn = req.GET.get('fn')
        pid = req.GET.get('id')

        if pid == '0':
            path = join(settings.TMP_UPLOAD_PATH, helpers.getuserdir(req))

        else:
            path = join(settings.UPLOAD_PATH, helpers.getreqdir(pid))

        filename = join(path, fn)
        f = open(filename, 'rb')
        b = f.read()
        f.close()

        return helpers.sendfile(b, fn, 'application/octet-stream')

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def uploaddelete(req):
    try:
        fn = req.GET.get('fn')
        pid = req.GET.get('id')

        if pid == '0':
            path = join(settings.TMP_UPLOAD_PATH, helpers.getuserdir(req))

        else:
            path = join(settings.UPLOAD_PATH, helpers.getreqdir(pid))

        models.ReqFile.objects.filter(filename__iexact=fn, reqform_id=int(pid)).delete()

        filename = join(path, fn)
        os.remove(filename)

        if pid == '0':
            return uploadcreatelist(req)#uploadfilelist(req)

        else:
            return uploadeditlist(req, pid)

    except Exception as e:
        logger.exception(str(e))
        return HttpResponseServerError(traceback.format_exc())

@login_required
def createuser(req):

    if req.method == 'POST':
        try:
            o = models.User()

            o.email = req.POST.get('email')
            o.username = req.POST.get('username')
            o.password = req.POST.get('username')

            o.is_staff = req.POST.get('is_staff')
            if o.is_staff is None: o.is_staff = 0
    
            o.is_approver = req.POST.get('is_approver') #req.POST.get('is_approver')
            if o.is_approver is None: o.is_approver = 0
            
            o.is_active = 1
            o.dept = req.POST.get('dept')

            o.save()
            messages.add_message(req, messages.SUCCESS, 'Account Created!!')  

            dic = {
                'o': o,
                'url': settings.EDIT_URI
            }
            
            sendemail(render_to_string('personal/createnoti.html', dic), o.email, '')


        except Exception as e:
            #logger.exception(str(e))
            return HttpResponseServerError(traceback.format_exc())
       
    return createusersubmit(req)


@login_required
def createusersubmit(request, o=None, showsubmit=False):
    
    ctx = {
        'applist': models.App.objects.all().order_by('name'),
        #'userlist': models.User.objects.filter(dept="rnd"),
        'userlistx': models.User.objects.all().order_by('dept'),
        'apprvlist': models.User.objects.filter(is_approver=True),
        'assignlist': models.Assign.objects.filter(req_id=o.id) if o is not None else [],
        'listtemp': models.ReqForm.objects.filter(assignto=request.user.id) #if o is not None else []

    }
    

    return render(request, 'personal/createuser.html', context=ctx)

def sendemail(body, emailto, cc):

    try:
        strfrom = settings.SERVER_EMAIL
        tolist = [emailto]

        cclist = [cc]
        bcc_email = ['ainur.fadzil@redtone.com']
       
        subject = 'Change Form Request System'
        ms = EmailMultiAlternatives(subject=subject, body='', from_email=strfrom, to=tolist, cc=cclist, bcc=bcc_email)
        ms.attach_alternative(body, 'text/html')
        ms.content_subtype = "html"
        ms.send()

    except Exception as e:
        raise
        logger.exception(str(e))

        

