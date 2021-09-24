"""User model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.u1 = User.signup('u1', 'u1@gmail.com', 'password', None)
        self.u1_id = 1111
        self.u1.id = self.u1_id  

        self.u2 = User.signup('u2', 'u2@gmail.com', 'password', None)
        self.u2_id = 2222
        self.u2.id = self.u2_id  

        self.u3 = User.signup('u3', 'u3@gmail.com', 'password', None)
        self.u3_id = 3333
        self.u3.id = self.u3_id  

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email='test@test.com',
            username='testuser',
            password='HASHED_PASSWORD'
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_follows(self):
        """Check if adding a follower relationship is reflected in the database"""
        
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.followers), 1)

        self.assertEqual(self.u1.following[0].id, self.u2.id)
        self.assertEqual(self.u2.followers[0].id, self.u1.id)

    def test_vaild_signup(self):
        """Check if new user details have succesfully been added to the database"""

        testuser = User.signup('testuser', 'testuser@gmail.com', 'password', None)
        testuser_id = 1212
        testuser.id = testuser_id
        db.session.commit()

        testuser = User.query.get(testuser.id)
        self.assertEqual(testuser.username, 'testuser')
        self.assertEqual(testuser.email, 'testuser@gmail.com')
        self.assertNotEqual(testuser.password, 'password')
        self.assertTrue(testuser.password.startswith('$2b$'))

    def test_invalid_username_signup(self):
        """Check if an error is successfully raised when user submits an invalid username while signing up"""

        invalid = User.signup(None, 'invalid@gmail.com', 'password', None)
        invalid_id = 1212
        invalid.id = invalid_id

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        """Check if an error is successfully raised when user submits an invalid email while signing up"""

        invalid = User.signup('invalid', None, 'password', None)
        invalid_id = 1212
        invalid.id = invalid_id

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()        

    def test_invalid_password_signup(self):
        """Check if an error is successfully raised when user submits an invalid password while signing up"""

        with self.assertRaises(ValueError) as context:
            User.signup('invalid', 'invalid@gmail.com', None, None)

        with self.assertRaises(ValueError) as context:
            User.signup('invalid', 'invalid@gmail.com', '', None)

    def test_valid_authentication(self):
        """Succesfully authenticate a user"""

        u1 = User.authenticate(self.u1.username, 'password')
        self.assertIsNotNone(u1)
        self.assertEqual(u1.id, self.u1.id)

    def test_invalid_username(self):
        """Check if app will not authenticate an invalid user"""

        self.assertFalse(User.authenticate('invalidname', 'password'))

    def test_wrong_password(self):
        """Check if app will not authenticate an valid user with the wrong password"""

        self.assertFalse(User.authenticate(self.u1.username, 'wrongpassword'))