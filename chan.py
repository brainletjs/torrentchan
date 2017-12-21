from flask import Flask
#use markup later to escape html in strings that come from users
from flask import Markup
from flask import request
from flask import send_file, render_template
from io import BytesIO
from captcha.image import ImageCaptcha
import json
from time import gmtime, strftime
from random import randint
import os

#REMOVE IN PRODUCTION FOR TESTING ONLY
if __name__ == '__main__':
      app.run(host='0.0.0.0', port=80,threaded=True)

#remove the static url path varible when we go to production
app = Flask(__name__, static_url_path='/static/')

#---------------classes for main data structures
class Post(object):
	"""each post is its own little torrent, this contains all the data to dl it"""
	def __init__(self, id, magnet, pster):
		self.post_id = id
		self.post_magnet_uri = magnet
		self.reputation = 0
		#post time is a string
		self.post_time = strftime("%Y-%m-%d+%H:%M:%S", gmtime())
		#the poster's ip address
		self.poster = pster


class Thread(Post):
	"""a thread is a post that has an array of other posts related to that thread in it"""
	def __init__(self, thr_id, magnet, title_param, pster):
		super(Thread, self).__init__(thr_id, magnet, pster)
		self.title = title_param
		self.thread_id = thr_id
		#the array of posts in this thread
		self.posts = []

	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class Captcha(object):
	def __init__(self, image, answer):
		self.image = image
		self.answer = answer
		self.active = True
	def isActive(self):
		return self.active
	def checkAnswer(self, response):
		self.active = False
		return self.answer == response
#---------------end classes-----------

#list that will hold all the threads on the chan in memory NOT USED ANYMORE
#global_threads = []

#dict of boards in the chan, that each have an array like global_threads
boards = {'a':[], 'tech':[], 'b':[], 'meta':[], 'pol':[]}

#list of active captcha objects
global_captchas = []

#list of all allowed posters
allowed_posters = ['127.0.0.1']

#a list of ip addresses that have been banned.
banned_posters = []

#a hardcoded thread for testing

#testPost = Post(1, 'magnet::this is another magnet link')
#testPost2 = Post(2, 'magnet::this is another another magnet link')

#testThread.posts.append(testPost)
#testThread.posts.append(testPost2)


#global_threads.append(testThread)
#testThread.title = "this not a test"
#testThread.thread_id = 5
#global_threads.append(testThread)
#----------------end test data-------------

#global post counter to be used for ids
#CHANGE THIS BACK TO 0 AT SOME POINT

#uhh right now post counts are shared between all boards
post_count = {'a':0, 'tech':0, 'b':0, 'meta':0, 'pol':0}

def get_thread_by_id(thread_id_to_find, board_letter):
#please forgive me, this method is fucking awful, 
#fix the algroithm and make it binary search asap
	return next((thread for thread in boards[board_letter] if thread.post_id==thread_id_to_find), None)

#-----------------application routes -------------------
#since this is served statically it needs to be removed once nginix is setup
@app.route('/<string:board_letter>/')
def index(board_letter):
	if board_letter in boards:
		return app.send_static_file('client.html')

@app.route('/')
def landing():
	return app.send_static_file('index.html')

@app.route('/<string:board_letter>/admin', methods=['GET','POST'])
def admin(board_letter):
	if(request.method == 'GET'):
		if(request.remote_addr == '127.0.0.1'):
			#now we know the admin is on the server (yeah I know this is bad)
			return render_template('admin.html', boardData=boards[board_letter] )
	elif(request.method == 'POST'):
		if(request.remote_addr == '127.0.0.1'):
			#getting a request from the admin panel
			print request.form['deletePost']

	return "you are not allowed"
	


#HUGE SECURITY PROBLEM, REMOVE WHEN GOING TO PRODUCTION
'''@app.route('/static/<string:static_file>')
def temp_static_files(static_file):
	return app.send_static_file(static_file)
'''

@app.route("/<string:board_letter>/catalog")
def catalog(board_letter):
    return json.dumps(boards[board_letter], default=lambda o: o.__dict__, sort_keys=True, indent=4)


#NEEDS TO BE UPDATED TO WORK WITH BOARDS
#isnt actually used right now so i didnt bother
#returns contents of a thread
# @app.route("/<string:board_letter>/thread/<int:thread_id>")
# def show_thread(thread_id):
# 	if get_thread_by_id(thread_id) == None:
# 		return 'there was a problem finding thread#' + str(thread_id)
# 	else:
# 		return get_thread_by_id(thread_id).toJSON()

#this route takes POST requests and adds a post to a thread
@app.route("/<string:board_letter>/post/<int:thread_id>", methods=['GET','POST'])
def create_post(thread_id, board_letter):
	global allowed_posters
	#error = None
	if request.method == 'POST':
		#make sure we were sent the right data
		if request.form['magnet']:
			if request.remote_addr in allowed_posters:
				if get_thread_by_id(thread_id, board_letter) == None:
					return 'there was a problem finding thread#' + str(thread_id)
				else:
					#calculate the new id
					global post_count
					post_count[board_letter] = post_count[board_letter] + 1
					#create a new post and append to the 
					new_post = Post(post_count[board_letter], request.form['magnet'], request.remote_addr)
					#sometimes i really love these one liners you can make in python
					get_thread_by_id(thread_id, board_letter).posts.append(new_post)
			else:
				#if we're here then the poster isnt in the posters list
				return 'poster IP not authorized'
	else:
		return 'wrong kinda request bro.'

	return str(post_count[board_letter])


#this route does jack shit now that we just get the whole thread
#also it doesnt work right for some reason. 
#DEPRCATED AND BROKEN
@app.route("/<string:board_letter>/posts/<int:thread_id>/<int:post_id>", methods=['GET'])	
def get_post(board_letter, thread_id, post_id):
	if request.method == "GET":
		if 0 <= post_id:
			#WORKING ON THIS
			#this is fucking nasty, fix it pls actually wait it even worse now that I fixed the thread problem
			#just use the funtion to get the thread
			thread = get_thread_internal(board_letter, thread_id)
			print thread
			if not thread:
				return "thread not found"
			else:
				print thread.posts
				for post in thread.posts:
					#can remove the print statement for production 
					print(post.post_id)

					if post_id == post.post_id:
						return json.dumps( post, default=lambda o: o.__dict__, sort_keys=True, indent=4)
					else:
						return 'post not found'
			
		return 'post id failure'
	return 'request failure'


#this route makes a new thread
@app.route('/<string:board_letter>/post/thread/', methods=['GET','POST'])
def create_thread(board_letter):
	global allowed_posters
	if request.method == 'POST':
		if request.form['magnet'] and request.form['title']:
			if request.remote_addr in allowed_posters:
				if len(boards[board_letter]) > 300 : 
					boards[board_letter].pop(0)
				#calculate the new id
				global post_count
				post_count[board_letter] = post_count[board_letter] + 1
				#create a new post and append to the 
				new_thread = Thread(post_count[board_letter], request.form['magnet'], request.form['title'], request.remote_addr)
				boards[board_letter].append(new_thread)
			else:
				#if we're in here this means that the poster isnt in the allowed posters list
				return 'poster IP not authorized'
	else:
		return 'wrong kinda request bro.'

	return str(post_count[board_letter])


#gets a single threads json, used to update threads on the page individually
#if internal is true its just a request from the get_post function
@app.route('/<string:board_letter>/thread/<int:thread_id>', methods=['GET'])
def get_thread(board_letter, thread_id):
	if request.method == "GET":
		if 0 <= thread_id < post_count[board_letter]+1:
			for thread in boards[board_letter]:
				print thread.thread_id
				
				if thread_id == thread.thread_id:
					return json.dumps( thread, default=lambda o: o.__dict__, sort_keys=True, indent=4)
		return "wrong post number"

#UPDATE AS THE ABOVE IS UPDATED!!!
def get_thread_internal(board_letter, thread_id):
	if 0 <= thread_id < post_count[board_letter]+1:
		for thread in boards[board_letter]:
			print thread.thread_id
			
			if thread_id == thread.thread_id:
				return thread
	return False


#this route gets or posts captcha
@app.route('/captcha/', methods=['GET','POST'])
def manage_captcha():
	global global_captchas
	global allowed_posters
	if request.method == 'POST':
		if request.form['captchanum'] and request.form['answer']:
			#these next two lines are nasty, maybe use a varible? MAKE A FUCKING VARIBLE
			if int(request.form['captchanum']) <= len(global_captchas):
				if global_captchas[int(request.form['captchanum'])-1].isActive() and global_captchas[int(request.form['captchanum'])-1].checkAnswer(request.form['answer']):
					allowed_posters.append(request.remote_addr)
					#print(str(request.remote_addr) + ' added to allowed_posters')
					#remove the file from the array of active captchas and delete the file.
					global_captchas.remove(global_captchas[int(request.form['captchanum'])-1])
					os.remove('static/' + str(int(request.form['captchanum'])-1) + '.png')
					return "Success, you may now go back and post"
				else:
					return "there was an error, please try again"
			else:
				return "there was an error with the captcha, please try again " + str(request.form['captchanum']) + " "+  str(len(global_captchas)) 
	elif request.method == 'GET':
		random = str(randint(1000,9999))
		image = ImageCaptcha(fonts=['/usr/share/fonts/TTF/DejaVuSans.ttf', '/usr/share/fonts/TTF/DejaVuSerif.ttf'])
		data = image.generate(random)
		#assert isinstance(data, BytesIO)
		#ok maybe making this filename is inefficent
		name = str(len(global_captchas)+1)
		#put the new file in the templates folder so the template can use it (i feel like this is bad)
		image.write(random, 'static/' + name + '.png')
		global_captchas.append(Captcha('static/' + name + '.png', random))
		#return send_file(str(len(global_captchas)) + '.png')
		return render_template('captcha.html', name=str(len(global_captchas)) )
	else:
		return "WUT U DID SOMETHING WRONG"
