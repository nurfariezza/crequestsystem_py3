from personal import models

class ClientAuthBackend(object):
    
    def authenticate(self, username=None, password=None, email=None):
        user = None
        
        try:
            if email is not None:
                user = models.User.objects.get(email=email)
                user.save()

        except models.User.DoesNotExist:
            user = None
            
        except Exception:
            raise

        return user

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        
        except models.User.DoesNotExist:
            return None
