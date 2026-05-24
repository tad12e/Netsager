import requests

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.text import slugify
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser


def serialize_user(user):
	return {
		'id': user.id,
		'email': user.email,
		'username': user.username,
		'first_name': user.first_name,
		'last_name': user.last_name,
		'avatar': user.avatar.url if user.avatar else None,
		'is_staff': user.is_staff,
		'date_joined': user.date_joined.isoformat() if user.date_joined else None,
	}


def build_auth_response(user, http_status=status.HTTP_200_OK):
	token, _ = Token.objects.get_or_create(user=user)
	return Response(
		{
			'token': token.key,
			'user': serialize_user(user),
		},
		status=http_status,
	)


def unique_username(base_username):
	candidate = slugify(base_username)[:150] or 'user'
	original = candidate
	suffix = 1

	while CustomUser.objects.filter(username=candidate).exists():
		suffix += 1
		trimmed = original[: max(0, 150 - len(str(suffix)) - 1)]
		candidate = f'{trimmed}-{suffix}'

	return candidate


def get_google_profile(id_token):
	if not settings.GOOGLE_CLIENT_ID:
		raise ValueError('GOOGLE_CLIENT_ID is not configured.')

	response = requests.get(
		'https://oauth2.googleapis.com/tokeninfo',
		params={'id_token': id_token},
		timeout=10,
	)
	response.raise_for_status()
	profile = response.json()

	if profile.get('aud') != settings.GOOGLE_CLIENT_ID:
		raise ValueError('Google token was issued for a different client.')

	if str(profile.get('email_verified', '')).lower() != 'true':
		raise ValueError('Google account email is not verified.')

	return profile


class RegisterView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		email = (request.data.get('email') or '').strip().lower()
		username = (request.data.get('username') or '').strip()
		password = request.data.get('password') or ''
		first_name = (request.data.get('first_name') or '').strip()
		last_name = (request.data.get('last_name') or '').strip()

		if not email or not username or not password:
			return Response(
				{'detail': 'Email, username, and password are required.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			validate_password(password)
		except ValidationError as exc:
			return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

		if CustomUser.objects.filter(email=email).exists():
			return Response({'detail': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

		if CustomUser.objects.filter(username=username).exists():
			return Response({'detail': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			with transaction.atomic():
				user = CustomUser.objects.create_user(
					email=email,
					username=username,
					password=password,
					first_name=first_name,
					last_name=last_name,
				)
		except IntegrityError:
			return Response({'detail': 'Could not create the user.'}, status=status.HTTP_400_BAD_REQUEST)

		login(request, user)
		return build_auth_response(user, http_status=status.HTTP_201_CREATED)


class LoginView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		email = (request.data.get('email') or '').strip().lower()
		password = request.data.get('password') or ''

		if not email or not password:
			return Response(
				{'detail': 'Email and password are required.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		user = authenticate(request, email=email, password=password)
		if user is None:
			return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

		login(request, user)
		return build_auth_response(user)


class GoogleLoginView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		id_token = request.data.get('credential') or request.data.get('id_token')

		if not id_token:
			return Response({'detail': 'Google credential is required.'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			profile = get_google_profile(id_token)
		except ValueError as exc:
			return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
		except requests.RequestException:
			return Response({'detail': 'Unable to verify the Google token.'}, status=status.HTTP_400_BAD_REQUEST)

		email = (profile.get('email') or '').strip().lower()
		if not email:
			return Response({'detail': 'Google profile did not return an email.'}, status=status.HTTP_400_BAD_REQUEST)

		first_name = (profile.get('given_name') or '').strip()
		last_name = (profile.get('family_name') or '').strip()
		display_name = (profile.get('name') or email.split('@')[0]).strip()

		user, created = CustomUser.objects.get_or_create(
			email=email,
			defaults={
				'username': unique_username(display_name),
				'first_name': first_name,
				'last_name': last_name,
			},
		)

		if created:
			user.set_unusable_password()
			user.save(update_fields=['password'])
		else:
			updates = []
			if first_name and user.first_name != first_name:
				user.first_name = first_name
				updates.append('first_name')
			if last_name and user.last_name != last_name:
				user.last_name = last_name
				updates.append('last_name')
			if not user.username:
				user.username = unique_username(display_name)
				updates.append('username')
			if updates:
				user.save(update_fields=updates)

		login(request, user)
		return build_auth_response(user)


class MeView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		return Response({'user': serialize_user(request.user)})


class LogoutView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		Token.objects.filter(user=request.user).delete()
		logout(request)
		return Response({'detail': 'Logged out successfully.'})
