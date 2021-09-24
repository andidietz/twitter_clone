"""User View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    
    def setUp(self):
        """Set up tests to test User views"""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username='testusername', email='test@gmail.com', password='testpassword', image_url=None)
        self.testuser_id = 1111
        self.testuser.id = self.testuser_id

        self.u1 = User.signup(username='u1', email='u1@gmail.com', password='password', image_url=None)
        self.u1_id = 1212
        self.u1.id = self.u1_id  
        self.u2 = User.signup(username='u2', email='u2@gmail.com', password='password', image_url=None)
        self.u2_id = 1313
        self.u2.id = self.u2_id  
        self.u3 = User.signup(username='u3', email='u3@gmail.com', password='password', image_url=None)
        self.u4 = User.signup(username='u4', email='u4@gmail.com', password='password', image_url=None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()

        return resp

    def test_users_list(self):
        """Successfully show list of users"""
        with self.client as c:
            resp = c.get('/users')

            self.assertIn('@testusername', str(resp.data))
            self.assertIn('@u1', str(resp.data))
            self.assertIn('@u2', str(resp.data))
    
    def test_users_search(self):
        """Successfully search and list of requested users"""

        with self.client as c:
            resp = c.get('/users?q=1')

            self.assertIn('@u1', str(resp.data))

            self.assertNotIn(self.testuser.username, str(resp.data))
    
    def test_user_show(self):
        """Successfully show user details"""

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}')

            self.assertEqual(resp.status_code, 200)

            self.assertIn('@testusername', str(resp.data))

    def setup_likes(self):
        """Helper function that sets up test messages and add one to testuser's likes"""

        m1 = Message(text='TestuserMessage', user_id=self.testuser_id)
        m2 = Message(id=2222, text='Message1', user_id=self.u1_id)
        m3 = Message(id=3333, text='Message2', user_id=self.u2_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        like = Likes(user_id=self.testuser_id, message_id=2222)
        db.session.add(like)
        db.session.commit()

    def test_add_like(self):
        """Successfully add a message to testuser's likes"""

        m = Message(id=4444, text='add test message', user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post('/messages/4444/like', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==4444).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        """Successfully remove a message to testuser's likes"""

        self.setup_likes()

        m = Message.query.filter(Message.text=='Message2').one()
        self.assertNotEqual(m.user_id, self.testuser_id)

        like = Likes.query.filter(Likes.user_id==self.testuser_id and Likes.message_id==m.id).one()
        self.assertIsNotNone(like)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.post(f'/messages/{m.id}/like', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    def setup_followers(self):
        """Helper function that sets up followers and following relationships"""

        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()
    
    def test_show_following(self):
        """Successfully show who is following testuser"""
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f'/users/{self.testuser_id}/following')
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', str(resp.data))
            self.assertIn('@u2', str(resp.data))
            self.assertNotIn('@u3', str(resp.data))


    def test_show_followers(self):
        """Successfully show testuser's followers"""

        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f'/users/{self.testuser_id}/followers')
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', str(resp.data))
            self.assertNotIn('@u2', str(resp.data))


    def test_auathorized_following_page_access(self):
        """Try and fail to access following page due to no user_id in session"""
        
        self.setup_followers()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}/following', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
            self.assertNotIn('@u1', str(resp.data))

    
    def test_auathorized_followers_page_access(self):
        """Try and fail to access followers page due to no user_id in session"""

        self.setup_followers()
        
        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}/followers', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
            self.assertNotIn('@u1', str(resp.data))