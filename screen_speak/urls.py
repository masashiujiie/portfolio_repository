from django.contrib import admin  # Djangoの管理サイト機能をインポート
from django.urls import path, include  # URLパターン定義のための関数をインポート
from django.conf import settings
from django.conf.urls.static import static
from flick_seeker.views import portfolio


urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理サイトへのURLパターンを定義
    path('screen_speak/', include('flick_seeker.urls', namespace='flick_seeker')),  
    path('', portfolio, name='portfolio'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)