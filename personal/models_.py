import decimal, datetime, math
from .import message
from django.conf import settings
from django.db import models
from django.db.models.fields import related
from django.contrib import messages
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _
from wheezy.validation import Validator
from wheezy.validation.rules import required, length

def getdict(o):
    dic = {}
    
    if o is None:
        return None
    
    for k, v in o.__dict__.items():
        if isinstance(v, decimal.Decimal):
            dic[k] = float(v)
            
        elif isinstance(v, datetime.datetime):
            dic[k] = str(v)
            
        else:
            dic[k] = v
            
    return dic

class JsonModel(object):
    
    def tojson(self):
        return getdict(self)

# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), max_length=100, unique=True, db_index=True)
    email = models.EmailField(_('email address'), max_length=255, unique=True, db_index=True)
    is_approver = models.BooleanField(_('approver'), default=False)
    is_staff = models.BooleanField(_('staff'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    dept = models.CharField(_('department'), max_length=100)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
 
    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])

    def get_short_name(self):
        return self.email

    def get_full_name(self):
        return self.email
        
    def __unicode__(self):
        return unicode(self.email)

class App(models.Model):
    name = models.CharField(max_length=100)
    user_email = models.CharField(max_length=100)

    def __unicode__(self):
        return u'{0} - {1}'.format(self.id, self.name)
        #return self.name.decode('utf8')
        #return self.name
class comment(models.Model):
    appsid = models.IntegerField()
    comment = models.CharField(max_length=400)
    email = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ['comment']

    def validate(self):
        v = Validator({
            'comment': [required(message_template=message.required_msg('Comment'))]
           
        })
        errors = {}
        b = v.validate(self, results=errors)
        l = message.get_error_list(errors)
        return l

class logact(models.Model):
    log_time = models.DateTimeField(auto_now_add=True)
    log_action = models.CharField(max_length=400)
    log_req_id = models.CharField(max_length=100)
    user_id = models.CharField(max_length=400)
    name = models.CharField(max_length=400)


    REQUIRED_FIELDS = ['user_id']

    def setfromdic(self, d):
        user_id = int(d.get('user_id')) if d.get('user_id') not in [None, ''] else None
        

class tempform(models.Model):
    req_id = models.IntegerField()
    creator = models.IntegerField()
    assigntoid = models.IntegerField()#models.ForeignKey(User, related_name='+')
    app_name = models.CharField(max_length=300)
    approver = models.IntegerField()
    title = models.CharField(max_length=3000)
    description = models.CharField(max_length=3000)
    remark = models.CharField(max_length=3000, null=True)
    createddate = models.DateTimeField(auto_now_add=False)
    usedate = models.DateTimeField(auto_now_add=True)
    tempstatus = models.IntegerField(default=9)
  
    
    REQUIRED_FIELDS = ['req_id', 'approver', 'creator', 'description', 'title']

    def setfromdic(self, d):
        assigntoid = int(d.get('assigntoid')) if d.get('assigntoid') not in [None, ''] else None

        if assigntoid is not None:
            self.assigntoid = User.objects.get(pk=assigntoid)

class ReqForm(models.Model):
    requser = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    approver = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    app = models.ForeignKey(App, related_name='+',on_delete=models.CASCADE )
    reqstatus = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=3000)
    remark = models.CharField(max_length=3000, null=True)
    description = models.CharField(max_length=3000)
    description1 = models.CharField(max_length=3000, null=True)
    description2 = models.CharField(max_length=3000, null=True)
    assignto = models.CharField(max_length=3000, null=True)
    reqdate = models.DateTimeField(auto_now_add=True)
    vstatus = models.PositiveIntegerField(default=1)
    verified = models.BooleanField(_('verified'), default=False)



    REQUIRED_FIELDS = ['requserid', 'approverid', 'appid', 'description', 'title']

    def setfromdic(self, d):
        approver = int(d.get('approver')) if d.get('approver') not in [None, ''] else None
        app = int(d.get('app')) if d.get('app') not in [None, ''] else None
        reqstatus = d.get('reqstatus')
        self.assignto = d.get('assignto')
        self.title = d.get('title')
        self.remark = d.get('remark')
        self.description = d.get('description')
        self.description1 = d.get('description1')
        self.description2 = d.get('description2')
       
        self.vstatus = d.get('vstatus')

        if approver is not None:
            self.approver = User.objects.get(pk=approver)

        if app is not None:
            self.app = App.objects.get(pk=app)

        if reqstatus is not None:
            self.reqstatus = int(reqstatus)

        
        
    @property
    def reqstatusstr(self):
        if self.reqstatus == 1:
            return 'Approved by RND'

        elif self.reqstatus == 2:
            return 'Rejected'

        elif self.reqstatus == 3:
            return 'Cancel'

        elif self.reqstatus == 4:
            return 'Approved by Head'

        elif self.reqstatus == 5:
            return 'In Progress'

        elif self.reqstatus == 6:
            return 'Fixed/Done'

        elif self.reqstatus == 9:
            return 'Draft'
        
        else:
            return 'Open'

    def title_line(self):
        #self.title ='test'
        if self.title is not None:
       
            counter = self.title
            titlecount = len(counter)
            if titlecount > 30:
                word = counter[0:34] + '......'
                return word
 
            else:
                return counter
        else :
            return 'None'
       

    def validate(self):
        v = Validator({
            'approver_id': [required(message_template=message.required_msg('Approve By field'))],
            'app_id': [required(message_template=message.required_msg('Application Name field'))],
            'description': [required(message_template=message.required_msg('Description field'))],
            #'assignto': [required(message_template=message.required_msg('Assign To field'))]
        })
        errors = {}
        b = v.validate(self, results=errors)
        l = message.get_error_list(errors)
        return l

  

    def __unicode__(self):
        return u'{0} - {1} - {2}'.format(self.id, self.title, self.reqstatusstr, self.description, self.description1, self.description2)

class ReqFile(models.Model):
    reqform = models.ForeignKey(ReqForm, related_name='reqform', on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    uploaduser = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    uploaddate = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'{0} - {1} ---{2}'.format(self.id, self.uploaduser, self.uploaddate)
    
class Search(JsonModel):

    def __init__(self):
        self.keyword = None
        self.statuslist = None

    def setfromdic(self, d):
        k = d.get('keyword')
        self.keyword = None if k in [None, ''] else k


        s = d.getlist('status')
        if len(s) > 0:
            self.statuslist = [int(i) for i in s]
            #print s
    def setfromsessiondic(self, d):
        k = d.get('keyword')
        self.keyword = None if k in [None, '', 'None'] else k

        s = d.get('statuslist')
        if s is not None:
            self.statuslist = s

    @property
    def isempty(self):
        return True if self.keyword is None and self.statuslist is None else False

class Assign(models.Model):

    req_id = models.IntegerField()
    assignto = models.CharField( max_length=255)#_('assigntolist'),
    assign_time = models.DateTimeField(auto_now_add=True)
    

    REQUIRED_FIELDS = ['req_id', 'assignto']

   
    def setfromdic(self, d):
 
        req_id = int(d.get('req_id')) if d.get('req_id') not in [None, ''] else None
        #assigntolist = d.get('assignto') if d.get('assignto') not in [None, ''] else None
        #self.assignto = d.get('assignto')
   
        s = d.getlist('assignto')
        if len(s) > 0:
            self.assignto= s #assignto
      

        if req_id is not None:
            self.req_id = ReqForm.objects.get(pk=req_id)

    def setdic(self, d):
        self.assignto = d.get('assignto')
     
    #def __unicode__(self):
        #return unicode(self.assignto)
    #def __unicode__(self):
        #return self.assignto if self.assignto is not None else ''
    def __unicode__(self):
        return u'{0} - {1} - {2}'.format(self.id, self.req_id, self.assignto)
    

class Pager(object):
    
    def __init__(self, total, pagenum, pagesize):
        self.total = total
        self.pagenum = pagenum
        self.setpagesize(pagesize)
        
     
    @property
    def pagesize(self):
        return self._pagesize
    
    @property 
    def page_range(self):
        return range(1, self.totalpages + 1)   

    @pagesize.setter
    def pagesize(self):
        self.setpagesize()
        
    @property
    def lowerbound(self):
        return (self.pagenum - 1) * self.pagesize
    
    @property
    def upperbound(self):
        upperbound = self.pagenum * self.pagesize
        
        if self.total < upperbound:
            upperbound = self.total
            #print upperbound
        return upperbound
    
    @property
    def hasnext(self):
        return True if self.total > self.upperbound else False
    
    @property
    def hasprev(self):
        return True if self.lowerbound > 0 else False
        
    @property
    def totalpages(self):
        return int(math.ceil(self.total / float(self.pagesize)))
    
    @property
    def itemmessage(self):
        return self.getitemmessage(self.total, self.pagenum, self.pagesize)
        
    def setpagesize(self, pagesize):
        if (self.total < pagesize or pagesize < 1) and self.total > 0:
            self._pagesize = self.total
            
        else:
            self._pagesize = pagesize
            
        if self.totalpages < self.pagenum:
            self.pagenum = self.totalpages
            
        if self.pagenum < 1:
            self.pagenum = 1
            
    def getitemmessage(self, total, pagenum, pagesize):
        x = (pagenum - 1) * pagesize + 1
        y = pagenum * pagesize
        
        if total < y:
            y = total
            
        if total < 1:
            return ''
        
        s = 'items' if total > 1 else 'item'
        return '{0} to {1} of {2} {3}'.format(x, y, total, s)
