from django.contrib import admin  # Djangoの管理サイト機能をインポート
from .models import User, Movie, Review, Hashtag, ReviewHashtag, FavoriteMovie, ReviewReaction  # 同じアプリケーション内のUserモデルをインポート
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin  # DjangoのデフォルトUserAdminをインポート

class UserAdmin(DefaultUserAdmin):
    # デフォルトのUserAdmin設定をカスタマイズするクラス
    model = User  # このUserAdminが扱うモデルを指定
    list_display = ['email', 'is_staff', 'is_active']  # 管理画面のリスト表示に使用するフィールド
    list_filter = ['email', 'is_staff', 'is_active']  # リスト画面でフィルター可能なフィールド
    search_fields = ['email']  # リスト画面で検索可能なフィールド
    ordering = ['email']  # リスト画面でのデフォルトの並び順
    
admin.site.register(User, UserAdmin)  # Djangoの管理サイトにUserモデルとUserAdminを登録

# 映画モデルを管理画面に登録
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'director', 'release_year', 'created_at', 'updated_at')
    search_fields = ('title', 'director', 'cast')
    list_filter = ('director', 'release_year')  # フィルタに使用するフィールド

# レビューモデルを管理画面に登録
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'title', 'created_at', 'updated_at')
    search_fields = ('title', 'comment')
    list_filter = ('rating',)

# ハッシュタグモデルを管理画面に登録
@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ('label', 'created_at')
    search_fields = ('label',)

# レビューとハッシュタグの関連モデルを管理画面に登録
@admin.register(ReviewHashtag)
class ReviewHashtagAdmin(admin.ModelAdmin):
    list_display = ('review', 'hashtag', 'created_at')
    list_filter = ('hashtag',)

# お気に入り映画モデルを管理画面に登録
@admin.register(FavoriteMovie)
class FavoriteMovieAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'created_at')
    list_filter = ('user', 'movie')

# レビューリアクションモデルを管理画面に登録
@admin.register(ReviewReaction)
class ReviewReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'rating_type', 'created_at')
    list_filter = ('rating_type',)

