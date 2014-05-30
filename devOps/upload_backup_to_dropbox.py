import datetime
import os, traceback, datetime

try:
	from dropbox import client as dropbox_client
	from dropbox import rest, session
except ImportError:
	print "Dropbox module not installed\nInstall it with:\n\tpip install dropbox"
	exit()

def main():

	try:
		PGPASSWORD= os.environ['PGPASSWORD']
	except KeyError, e:
		print "The environment variable PGPASSWORD is not set"
		return

	try:
		PGUSER= os.environ['PGUSER']
	except KeyError, e:
		print "The environment variable PGUSER is not set"
		return

	try:
		PGDATABASE= os.environ['PGDATABASE']
	except KeyError, e:
		print "The environment variable PGDATABASE is not set"
		return




	command = "export PGPASSWORD=%s\npg_dump --username=%s -h localhost %s" % (PGPASSWORD, PGUSER, PGDATABASE)
	command += ' > '+str(datetime.date.today())
	os.system(command)
	command = "gzip "+str(datetime.date.today())
	os.system(command)


	try:
		DROPBOX_APP_KEY = os.environ['DROPBOX_APP_KEY']
	except KeyError, e:
		print "The environment variable DROPBOX_APP_KEY is not set"
		return

	try:
		DROPBOX_APP_SECRET = os.environ['DROPBOX_APP_SECRET']
	except KeyError, e:
		print "The environment variable DROPBOX_APP_SECRET is not set"
		return

	try:
		DROPBOX_ACCESS_KEY = os.environ['DROPBOX_ACCESS_KEY']
	except KeyError, e:
		print "The environment variable DROPBOX_ACCESS_KEY is not set"
		return

	try:
		DROPBOX_ACCESS_SECRET = os.environ['DROPBOX_ACCESS_SECRET']
	except KeyError, e:
		print "The environment variable DROPBOX_ACCESS_SECRET is not set"
		return

	try:
		DB_BACKUP_ERROR_NOTIFY= os.environ['DB_BACKUP_ERROR_NOTIFY']
	except KeyError, e:
		print "The environment variable DROPBOX_ACCESS_SECRET is not set"
		return


	try:
		if len(DROPBOX_APP_KEY) and len(DROPBOX_APP_SECRET):
			# ready to go
			pass
		else:
			print "app_key and app_secret not provided\n\nCreate a app at https://www.dropbox.com/developers/apps/create and insert the app_key and app_secret in client_secrets.json\nAnd try again"
			raw_input()
			client_secrets = json.loads(open("client_secrets.json").read())
	except KeyError, e:
		raise e

	sess = session.DropboxSession(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, "dropbox") # created the session object

	try:
		if len(DROPBOX_ACCESS_KEY) and len(DROPBOX_ACCESS_SECRET):
			# authorized
			pass
		else:
			request_token = sess.obtain_request_token() # obtain the request token
			url = sess.build_authorize_url(request_token)
			# Make the user sign in and authorize this token
			print "url:", url
			print "Please visit this website and press the 'Allow' button, then hit 'Enter' here."
			raw_input()
			# This will fail if the user didn't visit the above URL and hit 'Allow'
			access_token = sess.obtain_access_token(request_token)
			print "access_key --> " + access_token.key
			print "access_secret --> " + access_token.secret
			print "\nEnter the access_key and access_secret into environment variables"
			print "named DROPBOX_ACCESS_KEY and DROPBOX_ACCESS_SECRET"
			return
	except KeyError, e:
		raise e

	# pass the key and the secret
	sess.set_token(client_secrets.get("access_key"),client_secrets.get("access_secret"))
	# create the client object
	client = dropbox_client.DropboxClient(sess)

	try:
		with open(datetime.datetime.today().strftime("%Y%m%d") + "-db-backup"): pass #check existance of while
		print "Uploading started..."
		print client.put_file("/db_backup/" + datetime.datetime.today().strftime("%Y%m%d") + "-db-backup", open(datetime.datetime.today().strftime("%Y%m%d") + "-db-backup"))
		print "Uploading completed..."

		print "Removing yesterday's backup"
		yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)
		command = "rm "+str(yesterday)+".gz"
		os.system(command)
		print "Done removing"
	except IOError:
		content = traceback.format_exc()
		subject = "Kikar: Error on upload of DB backup to Dropbox"
		addresses = DB_BACKUP_ERROR_NOTIFY
		command = "echo \""+content+"\" | mail -s \""+subject+"\" +\""+addresses+"\""
		os.system(command)
		print "DB backup file does not exists"
	return



if __name__ == '__main__':
	main()
