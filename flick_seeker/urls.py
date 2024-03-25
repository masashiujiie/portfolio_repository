from django.urls import path  # DjangoのURLパターンを定義するためのモジュールから、path関数をインポート
from django.contrib.auth import views as auth_views  # Djangoの認証システム関連のビューをインポート
from django.urls import path, include  # URLパス関連の機能をインポート
from .views import top, signup, login_view,  signup_complete, dashboard, movie_list, mypage, my_reviews, my_favorites,movie_register,movie_register_complete, movie_list, movie_detail, add_review, movie_detail_edit, review_vote, toggle_favorite, edit_review, all_movie_reviews, search_results, PasswordChangeView, PasswordChangeDoneView, delete_user, edit_profile, portfolio  # アプリケーションのビュー関数をインポート
from . import views

app_name = 'flick_seeker'  # アプリケーションの名前空間を設定

urlpatterns = [     
    path('top/', top, name='top'),  # '/top/' URL を 'top' ビューにマッピング
    path('signup/', signup, name='signup'),  # '/signup/' URL を 'signup' ビューにマッピング
    path('login/', login_view, name='login'),  # '/login/' URL を 'login_view' ビューにマッピング
    path('signup_complete/', signup_complete, name='signup_complete'),  # '/signup_complete/' URL を 'signup_complete' ビューにマッピング、トークンをパラメータとして受け取る
    path('dashboard/', dashboard, name='dashboard'),  # '/dashboard/' URL を 'dashboard' ビューにマッピング
    path('movies/', movie_list, name='movie_list'),  # '/movies/' URL を 'movie_list' ビューにマッピング
    path('mypage/', mypage, name='mypage'),  # '/mypage/' URL を 'mypage' ビューにマッピング
    path('my_reviews/', my_reviews, name='my_reviews'),  # '/my_reviews/' URL を 'my_reviews' ビューにマッピング
    path('my_favorites/', my_favorites, name='my_favorites'),  # '/my_favorites/' URL を 'my_favorites' ビューにマッピング
    path('logout/', auth_views.LogoutView.as_view(next_page='flick_seeker:top'), name='logout'),  # '/logout/' URL を Djangoのログアウトビューにマッピング、ログアウト後は 'top' ビューにリダイレクト
    path('movie_register/', movie_register, name='movie_register'),
    path('movie_register_complete/', movie_register_complete, name='movie_register_complete'),
    path('movie_list/', movie_list, name='movie_list'),
    path('movie_detail/<int:movie_id>/', movie_detail, name='movie_detail'),
    path('movie/<int:movie_id>/add_review/', add_review, name='add_review'),
    path('movie_detail_edit/<int:movie_id>/', movie_detail_edit, name='movie_detail_edit'), 
    path('review/<int:review_id>/vote/<str:vote_type>/', review_vote, name='review_vote'),
    path('movie/<int:movie_id>/toggle_favorite/', toggle_favorite, name='toggle_favorite'),
    path('edit_review/<int:review_id>/', edit_review, name='edit_review'),
    # path('movie_reviews/<int:movie_id>/', movie_reviews, name='movie_reviews'),
    path('all_movie_reviews/<int:movie_id>/', all_movie_reviews, name='all_movie_reviews'),
    path('search_results/', search_results, name='search_results'),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('delete_user/', delete_user, name='delete_user'),
    path('edit_profile/', edit_profile, name='edit_profile'),
]