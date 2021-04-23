from django.contrib import admin
from.import models

# Register your models here.
@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
	pass

@admin.register(models.ReqForm)
class ReqFormAdmin(admin.ModelAdmin):
	pass

@admin.register(models.ReqFile)
class ReqFileAdmin(admin.ModelAdmin):
	pass

@admin.register(models.App)
class AppAdmin(admin.ModelAdmin):
	pass

@admin.register(models.Assign)
class AppAdmin(admin.ModelAdmin):
	pass

@admin.register(models.logact)
class AppAdmin(admin.ModelAdmin):
	pass
