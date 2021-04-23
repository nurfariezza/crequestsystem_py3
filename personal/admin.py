from django.contrib import admin
from.import models

# Register your models here.
@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
	#list_display = ['username', 'dept','userstatus']
	pass

@admin.register(models.ReqForm)
class ReqFormAdmin(admin.ModelAdmin):
	list_display = ['id', 'title','requser','reqstatusstr']
	#pass

@admin.register(models.ReqFile)
class ReqFileAdmin(admin.ModelAdmin):
	list_display = ['id', 'uploaduser','filename','uploaddate']
	#pass

@admin.register(models.App)
class AppAdmin(admin.ModelAdmin):
	pass

@admin.register(models.Assign)
class AppAdmin(admin.ModelAdmin):
	pass

@admin.register(models.logact)
class AppAdmin(admin.ModelAdmin):
	pass

@admin.register(models.comment)
class commentAdmin(admin.ModelAdmin):
	pass
