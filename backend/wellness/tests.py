import json

from django.contrib.auth.models import User
from django.test import Client, TestCase

from .models import AccountProfile, InvitationCode


class InvitationCodeAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user('admin-owner', password='PassWord123')
        self.admin.is_staff = True
        self.admin.save()
        AccountProfile.objects.create(user=self.admin, role=AccountProfile.ROLE_ADMIN)

    def post_json(self, path, payload):
        return self.client.post(path, data=json.dumps(payload), content_type='application/json')

    def test_teacher_registration_requires_teacher_invitation(self):
        response = self.post_json('/api/auth/register/', {
            'username': 'teacher-one',
            'password': 'PassWord123',
            'confirm_password': 'PassWord123',
            'role': '心理老师',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('邀请码', response.json()['detail'])

    def test_admin_can_lock_teacher_invitation_and_register_teacher(self):
        self.client.login(username='admin-owner', password='PassWord123')
        invitation_response = self.post_json('/api/auth/invitations/', {
            'target_role': 'teacher',
            'code': 'Tch@2026!ABcd#1Z',
        })
        self.assertEqual(invitation_response.status_code, 200)
        self.assertTrue(InvitationCode.objects.filter(code='Tch@2026!ABcd#1Z', target_role=AccountProfile.ROLE_TEACHER).exists())
        self.client.logout()

        register_response = self.post_json('/api/auth/register/', {
            'username': 'teacher-two',
            'password': 'PassWord123',
            'confirm_password': 'PassWord123',
            'role': '心理老师',
            'invitation_code': 'Tch@2026!ABcd#1Z',
        })
        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(register_response.json()['user']['role'], AccountProfile.ROLE_TEACHER)
        self.assertIsNotNone(InvitationCode.objects.get(code='Tch@2026!ABcd#1Z').used_at)

        reused_response = self.post_json('/api/auth/register/', {
            'username': 'teacher-three',
            'password': 'PassWord123',
            'confirm_password': 'PassWord123',
            'role': '心理老师',
            'invitation_code': 'Tch@2026!ABcd#1Z',
        })
        self.assertEqual(reused_response.status_code, 400)
        self.assertIn('邀请码无效', reused_response.json()['detail'])

    def test_unlock_invalidates_code_and_relock_restores_one_use(self):
        self.client.login(username='admin-owner', password='PassWord123')
        self.post_json('/api/auth/invitations/', {
            'target_role': 'teacher',
            'code': 'Once@2026!ABcd#2',
        })
        unlock_response = self.post_json('/api/auth/invitations/', {
            'target_role': 'teacher',
            'is_locked': False,
        })
        self.assertEqual(unlock_response.status_code, 200)
        self.client.logout()

        unlocked_register_response = self.post_json('/api/auth/register/', {
            'username': 'teacher-unlocked',
            'password': 'PassWord123',
            'confirm_password': 'PassWord123',
            'role': '心理老师',
            'invitation_code': 'Once@2026!ABcd#2',
        })
        self.assertEqual(unlocked_register_response.status_code, 400)

        self.client.login(username='admin-owner', password='PassWord123')
        relock_response = self.post_json('/api/auth/invitations/', {
            'target_role': 'teacher',
            'code': 'Once@2026!ABcd#2',
        })
        self.assertEqual(relock_response.status_code, 200)
        self.assertIsNone(InvitationCode.objects.get(code='Once@2026!ABcd#2').used_at)
        self.client.logout()

        relocked_register_response = self.post_json('/api/auth/register/', {
            'username': 'teacher-relocked',
            'password': 'PassWord123',
            'confirm_password': 'PassWord123',
            'role': '心理老师',
            'invitation_code': 'Once@2026!ABcd#2',
        })
        self.assertEqual(relocked_register_response.status_code, 201)

    def test_generated_invitation_is_16_random_characters_without_prefix(self):
        self.client.login(username='admin-owner', password='PassWord123')
        response = self.post_json('/api/auth/invitations/', {
            'target_role': 'teacher',
        })
        self.assertEqual(response.status_code, 200)
        code = response.json()['invitation_codes'][0]['code']
        self.assertEqual(len(code), 16)
        self.assertFalse(code.startswith('INV-'))

    def test_manual_invitation_has_no_length_limit(self):
        long_code = 'manual-code-can-be-much-longer-than-sixteen-characters-2026'
        self.client.login(username='admin-owner', password='PassWord123')
        response = self.post_json('/api/auth/invitations/', {
            'target_role': 'teacher',
            'code': long_code,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(InvitationCode.objects.filter(code=long_code).exists())
        self.client.logout()

        register_response = self.post_json('/api/auth/register/', {
            'username': 'teacher-long-code',
            'password': 'PassWord123',
            'confirm_password': 'PassWord123',
            'role': '心理老师',
            'invitation_code': long_code,
        })
        self.assertEqual(register_response.status_code, 201)

    def test_login_rejects_wrong_role_entrance(self):
        response = self.post_json('/api/auth/login/', {
            'username': 'admin-owner',
            'password': 'PassWord123',
            'role': '学生',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('对应身份入口', response.json()['detail'])
