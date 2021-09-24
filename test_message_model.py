"""User model tests."""

import os
from unittest import TestCase

from models import db, User, Message, Likes

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Tests Models for message"""

    def setUp(self):
        db.drop_all()
        db.create_all()

        u1 = User.signup('testuser', 'testuser@gmail.com', 'password', None)
        self.u1_id = 1212
        u1.id = self.u1_id

        u2 = User.signup('u2', 'u2@gmail.com', 'password', None)
        self.u2_id = 1313
        u2.id = self.u2_id

        db.session.commit()

        self.u1 = User.query.get(self.u1_id)
        self.client = app.test_client()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_message_model(self):
        m = Message(text='msg here', user_id=self.u1_id)

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(self.u1.messages[0].text, 'msg here')

    def test_meassage_likes(self):
        m1 = Message(text='msg here', user_id=self.u1_id)
        m2 = Message(text='test message', user_id=self.u1_id)
        db.session.add_all([m1, m2])
        db.session.commit()

        self.u1.likes.append(m1)
        db.session.commit()

        like = Likes.query.filter(Likes.user_id == self.u1_id).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, m1.id)