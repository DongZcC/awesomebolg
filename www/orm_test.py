from orm import *
import asyncio
import unittest

__author__ = 'Dong'


class test_orm(unittest.TestCase):


    def setUp(self):
        global loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(create_pool(loop,user='root',password='root',db='learnpy',port=3306))
        global u
        u = User(id=1234, name='dzc', email='3586738178@qq.com', passwd='123', image=' ')

    def tearDown(self):
        loop.run_until_complete(destory_pool())
        loop.close()

    # def test_add(self):
    #     loop.run_until_complete(u.save())

    def test_update(self):
        u.name = 'dzc2'
        loop.run_until_complete(u.update())

    # def test_delete(self):
    #     loop.run_until_complete(u.remove())


if __name__ == '__main__':
    unittest.main()