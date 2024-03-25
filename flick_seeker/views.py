import uuid  # 一意のID生成のためのライブラリ
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordChangeView as BasePasswordChangeView, PasswordChangeDoneView as BasePasswordChangeDoneView
from django.shortcuts import render, redirect,get_object_or_404  # HTMLテンプレートをレンダリングとリダイレクトのための関数、オブジェクトを取得、なければ404エラーを返す
from django.contrib.auth.decorators import login_required  # ログイン要求のデコレータ
from .models import Movie, Review, FavoriteMovie, ReviewReaction, ReviewHashtag, Hashtag  # アプリケーションのモデルをインポート
from .forms import CustomUserCreationForm, PasswordForm, MovieForm, ReviewForm, CustomPasswordChangeForm, UserDeleteConfirmForm, CustomUserChangeForm
from django.urls import reverse_lazy, reverse  
from django.contrib import messages  # メッセージフレームワーク
from django.contrib.auth import get_user_model, logout  
from django.db import IntegrityError  # データベース整合性エラー
from django.http import HttpResponse, JsonResponse  # HTTPレスポンス、Jsonレスポンスを生成する関数
from django.db.models import Avg, F, Count, Q, Prefetch  
import pdb
import logging
from django.views.decorators.http import require_POST

User = get_user_model()  # 現在アクティブなユーザーモデルを取得
logger = logging.getLogger(__name__)

def portfolio(request):
    return render(request, 'portfolio.html')

def top(request):
    # トップページのビュー。'top.html' テンプレートをレンダリングして表示
    return render(request, 'top.html')

def signup(request):   
    # サインアップ（ユーザー登録）ページのビュー
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # フォームのデータを保存し、ユーザーを作成
            request.session['registration_complete'] = True  # セッションにフラグを設定
            return redirect('flick_seeker:signup_complete')  # ユーザー登録完了ページへリダイレクト
        else:
            # ユーザーにエラーメッセージを表示
            messages.error(request, '登録に失敗しました。内容を確認してください。')
            # リダイレクトではなく、フォームを再表示
            return render(request, 'signup.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def signup_complete(request):
    # セッションからフラグを確認
    if request.session.get('registration_complete'):
        # 登録完了フラグ をセッションから削除
        del request.session['registration_complete']
        #　アカウントが作成されたメッセージを表示
        # messages.success(request, 'アカウントが正常に作成されました。下記リンクよりログインしてください。')
        # 登録完了ページを表示
        return render(request, 'signup_complete.html')
    else:
        # フラグがセットされていない場合、ユーザーをログインページにリダイレクト
        return redirect('flick_seeker:login')  

class CustomLoginView(LoginView):
    # カスタムログインビュー。ログインページ用のクラスベースビュー
    template_name = 'login.html'  # 使用するテンプレートを指定
    redirect_authenticated_user = True  # 既に認証されているユーザーはリダイレクト
    success_url = reverse_lazy('flick_seeker:dashboard')  # ログイン成功後のリダイレクト先を指定

login_view = CustomLoginView.as_view()
    
@login_required(login_url='screen_speak:login')
def dashboard(request):
    # ダッシュボードビューが呼び出されたらメッセージをクリア
    # これにより、前のリクエストから残っているメッセージは表示されない
    storage = messages.get_messages(request)
    for _ in storage:  # メッセージを読み込むことでクリアされる
        pass
    storage.used = True  # メッセージが既に表示されたとマーク    
    
     # ジャンルとシチュエーションのデータを取得
    genres = Hashtag.objects.filter(category='genre')
    situations = Hashtag.objects.filter(category='situation')
    
    # お気に入り数で注釈した映画リストから、最大3件のみを取得します。
    movies = Movie.objects.annotate(favorites_count=Count('favoritemovie')).order_by('-favorites_count')[:3]

    # コンテキストにジャンルとシチュエーションを追加
    context = {
        'movies': movies,
        'genres': genres,
        'situations': situations,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='screen_speak:login')
def search_results(request):
    # 検索条件を取得
    query = request.GET.get('query')
    selected_genres = request.GET.getlist('genre')
    selected_situations = request.GET.getlist('situation')
    rating_from = request.GET.get('rating_from')

    # 基本の映画クエリセット
    movies_qs = Movie.objects.all()

    # キーワードによる検索
    if query:
        movies_qs = movies_qs.filter(
            Q(title__icontains=query) |
            Q(director__icontains=query) |
            Q(cast__icontains=query)
        )

    # ジャンルによるフィルタリング
    if selected_genres:
        movies_qs = movies_qs.filter(
            review__reviewhashtag__hashtag__label__in=selected_genres,
            review__reviewhashtag__hashtag__category='genre'
        ).distinct()

    # シチュエーションによるフィルタリング
    if selected_situations:
        movies_qs = movies_qs.filter(
            review__reviewhashtag__hashtag__label__in=selected_situations,
            review__reviewhashtag__hashtag__category='situation'
        ).distinct()

    # 評価によるフィルタリング
    if rating_from:
        movies_qs = movies_qs.filter(review__rating__gte=rating_from).distinct()

    # 映画の平均レーティングで注釈
    movies_qs = movies_qs.annotate(average_rating=Avg('review__rating'))
    
    # 平均評価を小数点第一位まで四捨五入
    for movie in movies_qs:
        movie.average_rating = round(movie.average_rating, 1) if movie.average_rating else 0
    
    # 検索結果をコンテキストに追加
    context = {
        'movies': movies_qs,
        'query': query,
        'selected_genres': selected_genres,
        'selected_situations': selected_situations,
        'rating_from': rating_from,
    }

    return render(request, 'search_results.html', context)

@login_required
def movie_list(request):
    # 映画一覧ページのビュー。データベースから映画のリストを取得し表示
    movies = Movie.objects.all() # 全ての映画を取得
    return render(request, 'movie_list.html', {'movies': movies})

@login_required
def movie_register(request):
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        print(request.FILES)  # ファイルの内容をログに出力する
        if form.is_valid():
            title = form.cleaned_data['title']
            if Movie.objects.filter(title=title).exists():
                messages.error(request, 'この映画は既に登録されています。')
            else:
                form.save()
                # 登録完了ページへのリダイレクトに変更
                return redirect('flick_seeker:movie_register_complete')
    else:
        form = MovieForm()
    return render(request, 'movie_register.html', {'form': form})

@login_required
def movie_register_complete(request):
    return render(request, 'movie_register_complete.html')

@login_required
def movie_detail(request, movie_id):
    # 映画詳細ページのビュー。指定されたIDの映画の詳細情報を表示
    movie = get_object_or_404(Movie, pk=movie_id)
    reviews = Review.objects.filter(movie=movie).prefetch_related(
        Prefetch(
            'reviewhashtag_set',
            queryset=ReviewHashtag.objects.select_related('hashtag'),
            to_attr='hashtags'
        )
    ).order_by('-created_at')
    all_reviews_count = Review.objects.filter(movie=movie).count()  # 全てのレビュー数をカウント
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] 
    
    # Noneでなければ、小数点第一位まで四捨五入します。
    if average_rating is not None:
        average_rating = round(average_rating, 1)   # 平均評価がある場合に丸める
        
    else:
        # レビューがない場合は "評価なし" を表示するため、テンプレートに渡す前に適切な値に設定します。
        average_rating = "評価なし"
        
    # お気に入り状態を確認
    is_favorited = FavoriteMovie.objects.filter(user=request.user, movie=movie).exists()

    context = {
        'movie': movie,
        'reviews': reviews,
        'average_rating': average_rating,
        'all_reviews_count': all_reviews_count,
        'is_favorited': is_favorited,  # お気に入り状態をコンテキストに追加
    }

    return render(request, 'movie_detail.html', context)

@login_required
def movie_detail_edit(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            print(form.cleaned_data)  # クリーンなデータをログに出力
            form.save()
            return redirect('flick_seeker:movie_detail', movie_id=movie.id)
        else:
            print(form.errors)  # フォームのエラーをログに出力
    else:
        form = MovieForm(instance=movie)
    return render(request, 'movie_detail_edit.html', {'form': form, 'movie': movie})
   
@login_required
def mypage(request):
    # マイページのビュー。ログインユーザーの情報を表示
    user = request.user

    # マイページに必要なデータを辞書に格納
    context = {
        'user': user,
        # 他の必要なデータを追加
    }

    return render(request, 'mypage.html', context)

@login_required
def my_reviews(request):
    # ユーザーのレビュー一覧ページのビュー。ログインユーザーのレビューを表示（モデルによって異なる）
    print("Logged in user:", request.user)  # デバッグ出力
    reviews = Review.objects.filter(user=request.user)
    return render(request, 'my_reviews.html', {'reviews': reviews})

@login_required
def my_favorites(request):
    # ユーザーのお気に入り映画一覧ページのビュー。ログインユーザーのお気に入り映画を表示（モデルによって異なる）
    favorites = FavoriteMovie.objects.filter(user=request.user)
    return render(request, 'my_favorites.html', {'favorites': favorites})

@login_required
def add_review(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    
    # ジャンルとシチュエーションのハッシュタグを渡す
    genre_hashtags = Hashtag.objects.filter(category='genre')
    situation_hashtags = Hashtag.objects.filter(category='situation')
    
    # 同一ユーザーによる同一映画へのレビューが存在するかチェック
    if Review.objects.filter(user=request.user, movie=movie).exists():
        # メッセージを追加
        messages.info(request, 'すでにレビューが投稿されています。レビューを書く場合はマイページのレビュー一覧から編集してください。')
        # 既にレビューが存在する場合は、詳細ページにリダイレクト
        return redirect('flick_seeker:movie_detail', movie_id=movie.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.save()
            
            # ハッシュタグのIDリストを取得し、ReviewHashtagオブジェクトを作成
            selected_hashtags_ids = request.POST.getlist('hashtags')
            for hashtag_id in selected_hashtags_ids:
                hashtag = Hashtag.objects.get(id=hashtag_id)
                ReviewHashtag.objects.create(review=review, hashtag=hashtag)
                
            messages.success(request, 'レビューが正常に投稿されました。')
            return redirect('flick_seeker:movie_detail', movie_id=movie.id)
    else:
        form = ReviewForm()
        
    # genre_hashtags と situation_hashtags をコンテキストに追加
    context = {
        'form': form,
        'movie': movie,
        'genre_hashtags': genre_hashtags,
        'situation_hashtags': situation_hashtags,
    }
    return render(request, 'add_review.html', context)      

@login_required
def edit_review(request, review_id):
    # 特定のレビューを取得
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    # 映画のデータをレビューから取得
    movie = review.movie
    
     # 既存のハッシュタグを取得
    existing_hashtags = review.reviewhashtag_set.all().values_list('hashtag', flat=True)
    
    # ジャンルとシチュエーションのハッシュタグを取得
    genre_hashtags = Hashtag.objects.filter(category='genre').order_by('label')
    situation_hashtags = Hashtag.objects.filter(category='situation').order_by('label')
    
    # POSTリクエストの場合は、フォームを処理
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        
        if 'save' in request.POST:
            if form.is_valid():
                # まず、既存の関連するハッシュタグをすべて削除します。
                ReviewHashtag.objects.filter(review=review).delete()
                
                # フォームを保存
                updated_review = form.save()
            
                # 新しいハッシュタグの関連付けを作成します。
                selected_hashtags_ids = request.POST.getlist('hashtags')
                for hashtag_id in selected_hashtags_ids:
                    hashtag = Hashtag.objects.get(id=hashtag_id)
                    ReviewHashtag.objects.create(review=updated_review, hashtag=hashtag)
                
            # ユーザーに成功メッセージを表示します。
            messages.success(request, 'レビューが更新されました。')
            return redirect('flick_seeker:my_reviews')
                
        elif 'delete' in request.POST:
            # レビューの削除
            review.delete()
            messages.success(request, 'レビューを削除しました。')
            return redirect('flick_seeker:my_reviews')

    # POSTリクエストでない場合は、フォームを初期化
    else:
        form = ReviewForm(instance=review)
        # 既存のハッシュタグを初期選択状態にする
        form.fields['hashtags'].initial = existing_hashtags
         
    # コンテキストとともにテンプレートをレンダリング
    context = {
        'form': form,
        'review': review,
        'movie': movie,
        'genre_hashtags': genre_hashtags,
        'situation_hashtags': situation_hashtags,
        'existing_hashtags': existing_hashtags,
    }
    return render(request, 'edit_review.html', context)

@require_POST
def review_vote(request, review_id, vote_type):
     # ログ出力
    print(f"Vote view called with review_id: {review_id}, vote_type: {vote_type}")
    
    review = get_object_or_404(Review, pk=review_id)
    reaction, created = ReviewReaction.objects.get_or_create(
        review=review,
        user=request.user,
        defaults={'rating_type': vote_type}
    )

    # 投票が既に存在していた場合
    if not created:
        if reaction.rating_type == vote_type:
            # 同じ投票をしていた場合、その投票を取り消す
            reaction.delete()
            review.good_count = F('good_count') - 1 if vote_type == 'good' else F('good_count')
            review.bad_count = F('bad_count') - 1 if vote_type == 'bad' else F('bad_count')
        else:
            # 異なる投票をしていた場合、投票を変更する
            reaction.rating_type = vote_type
            reaction.save()
            review.good_count = F('good_count') + 1 if vote_type == 'good' else F('good_count') - 1
            review.bad_count = F('bad_count') + 1 if vote_type == 'bad' else F('bad_count') - 1
        review.save(update_fields=['good_count', 'bad_count'])
        # 更新されたカウントを取得するためにリフレッシュ
        review.refresh_from_db()
        return JsonResponse({
            'status': 'updated',
            'good_count': review.good_count,
            'bad_count': review.bad_count
        })

    # 新しい投票を作成した場合
    else:
        review.good_count = F('good_count') + 1 if vote_type == 'good' else F('good_count')
        review.bad_count = F('bad_count') + 1 if vote_type == 'bad' else F('bad_count')
        review.save(update_fields=['good_count', 'bad_count'])
        # 更新されたカウントを取得するためにリフレッシュ
        review.refresh_from_db()
        return JsonResponse({
            'status': 'created',
            'good_count': review.good_count,
            'bad_count': review.bad_count
        })

@login_required    
def movie_reviews(request, movie_id):
    # 映画IDに基づいたレビューを取得
    reviews = Review.objects.filter(movie_id=movie_id).order_by('-created_at')

    # テンプレートに渡すコンテキスト
    context = {
        'reviews': reviews,
        'movie_id': movie_id
    }

    # レンダリングするテンプレートを指定
    return render(request, 'all_movie_reviews.html', context)

@login_required       
def all_movie_reviews(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    reviews = Review.objects.filter(movie=movie).prefetch_related(
        Prefetch(
            'reviewhashtag_set', 
            queryset=ReviewHashtag.objects.select_related('hashtag'),
            to_attr='hashtags'
        )
    ).order_by('-created_at')
    return render(request, 'all_movie_reviews.html', {'movie': movie, 'reviews': reviews})       
        
@login_required
@require_POST
def toggle_favorite(request, movie_id):
    """
    ユーザーが映画をお気に入りに追加または削除するビュー。
    存在しない映画IDに対しては404を返す。
    """
    movie = get_object_or_404(Movie, pk=movie_id)
    favorite, created = FavoriteMovie.objects.get_or_create(user=request.user, movie=movie)

    if not created:
        # 既にお気に入りが存在する場合、お気に入りから削除
        favorite.delete()
        is_favorite = False
    else:
        # 新規にお気に入りに追加された場合は、そのまま
        is_favorite = True

    return JsonResponse({
        'status': 'success',
        'is_favorite': is_favorite
    })
    
class PasswordChangeView(BasePasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'password_change_form.html'
    success_url = reverse_lazy('flick_seeker:password_change_done')

class PasswordChangeDoneView(BasePasswordChangeDoneView):
    template_name = 'password_change_done.html'
    
@login_required
def delete_user(request):
    if request.method == 'POST':
        form = UserDeleteConfirmForm(request.user, request.POST)
        if form.is_valid():
            request.user.delete()
            messages.success(request, 'アカウントが正常に削除されました。')
            logout(request)
            return redirect('flick_seeker:top')  
    else:
        form = UserDeleteConfirmForm(request.user)

    return render(request, 'confirm_delete.html', {'form': form})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('flick_seeker:mypage')  
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form})