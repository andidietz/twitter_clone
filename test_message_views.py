"""Message View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username='testuser',
                                    email='test@test.com',
                                    password='testuser',
                                    image_url=None)

        self.u1 = User.signup(username='u1', email='u1@gmail.com', password='password', image_url=None)
        self.u1_id = 1212

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/messages/new', data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, 'Hello')


    def test_add_no_session(self):
        """Try and fail to add message when no user in session"""

        with self.client as c:
            resp = c.post(f'/messages/new', data={"text": "Msg Here"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
        
    def test_add_invalid_user(self):
        """Try and fail to add message to a user that does not exist"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 88888888888

            resp = c.post(f'/messages/new', data={"text": "Msg Here"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

    def test_message_show(self):
        """Successfully show message"""

        m = Message(id=1111, text='msg content', user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message.query.get(1111)

            resp = c.get(f'/messages/{m.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))
    
    def test_invalid_message_show(self):
        """Try and fail to show message that does not exist"""
    
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messsage/22222222')

            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):
        """Succesfully delete a message"""

        m = Message(id=1111, text='msg content', user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/messages/1111/delete')

            self.assertEqual(resp.status_code, 302)

            m = Message.query.get(1111)
            self.assertIsNone(m)

    def test_unauthorized_message_delete(self):
        """Try and fail to delete another user's message"""

        m = Message(id=1111, text='msg content', user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1212

            resp = c.post('/messages/1111/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

            m = Message.query.get(1111)
            self.assertIsNotNone(m)

    def test_message_delete_no_session(self):
        """Try and fail to delete message due to no user id in session"""

        m = Message(id=1111, text='msg content', user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.post('/messages/1111/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

            m = Message.query.get(1111)
            self.assertIsNotNone(m)

        
    