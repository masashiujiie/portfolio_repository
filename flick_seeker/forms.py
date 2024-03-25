from django import forms  # Djangoのフォーム機能をインポート
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, UserChangeForm
from django.contrib.auth import get_user_model  # 現在使用中のユーザーモデルを取得する関数をインポート
from django.core.exceptions import ValidationError  # フォームのバリデーションエラーを処理するための例外クラスをインポート
from django.utils.translation import gettext_lazy as _  # 国際化（多言語対応）のための翻訳機能をインポート
from .models import Movie, Review, Hashtag, User
import datetime

User = get_user_model()  # 現在アクティブなユーザーモデルを取得

class CustomUserCreationForm(UserCreationForm):
    # カスタムユーザー作成フォーム。UserCreationFormを拡張してカスタマイズ
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')  # メールアドレスフィールドを定義。ヘルプテキスト付き
    username = forms.CharField(max_length=150, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')  # ユーザー名フィールドを定義。ヘルプテキスト付き
    
    class Meta:
        model = User  # このフォームが使用するモデル
        fields = ('username','email', 'password1', 'password2')  # フォームで使用するフィールド
        
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'ユーザー名'
        self.fields['email'].widget.attrs['placeholder'] = 'メールアドレス'
        self.fields['password1'].widget.attrs['placeholder'] = 'パスワード'
        self.fields['password2'].widget.attrs['placeholder'] = 'パスワード（確認）'
        
class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)

class MovieForm(forms.ModelForm):
    release_year = forms.CharField(label='公開年', widget=forms.TextInput(attrs={'placeholder': '例: 2020'}), required=False)
    
    class Meta:
        model = Movie
        fields = ['title', 'plot', 'director', 'cast', 'release_year', 'thumbnail']  # 必要に応じてフィールドを調整
        labels = {
            'title': 'タイトル',
            'plot': 'あらすじ',
            'director': '監督',
            'cast': '出演者',
            'thumbnail': '映画のカバー画像',
        }
        widgets = {
            'title': forms.TextInput(attrs={'required': True}),
        }
    
    def clean_release_year(self):
        release_year = self.cleaned_data.get('release_year')

        # 年が数値であるかを検証
        try:
            release_year = int(release_year)
        except ValueError:
            raise ValidationError('公開年は数値で入力してください。')

        # 年が妥当な範囲内であるかを検証（例: 1900年から現在の年まで）
        if release_year < 1900 or release_year > datetime.date.today().year:
            raise ValidationError('無効な公開年です。')

        return release_year
    
class ReviewForm(forms.ModelForm):
    # ハッシュタグを複数選択するためのフィールド
    hashtags = forms.ModelMultipleChoiceField(
        queryset=Hashtag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Review
        fields = ['title', 'rating', 'spoiler', 'comment', 'hashtags']
        widgets = {
            'rating': forms.NumberInput(attrs={'step': 0.5, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 4}),
            'spoiler': forms.CheckboxInput(),  # ネタバレフィールドのwidgetをカスタマイズ
        }
        
    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        
class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_new_password1(self):
        old_password = self.cleaned_data.get('old_password')
        new_password1 = self.cleaned_data.get('new_password1')
        if old_password and new_password1:
            if old_password == new_password1:
                raise ValidationError(_('同じパスワードは設定できません。別のパスワードを設定してください。'), code='password_no_change')
        return new_password1
    
class UserDeleteConfirmForm(forms.Form):
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserDeleteConfirmForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user.check_password(password):
            raise forms.ValidationError('パスワードが間違っています。')
        return password
    
class CustomUserChangeForm(UserChangeForm):
    password = None  # パスワードフィールドをフォームから除外

    class Meta:
        model = User
        fields = ('username', 'email', 'profile_image', 'bio')  # 編集可能なフィールド
        widgets = {
            'profile_image': forms.FileInput(),     
        }