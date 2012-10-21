import win32file
import win32con

ACTIONS = {
	1 : "Created",
	2 : "Deleted",
	3 : "Updated",
	4 : "RenamedFrom",
	5 : "RenamedTo"
}

def watch_path(watched_path, callback):

	# based on API usage examples
	# http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html

	try:
		FILE_LIST_DIRECTORY = 0x0001
		folder_handle = win32file.CreateFile (
			watched_path
			, FILE_LIST_DIRECTORY
			, win32con.FILE_SHARE_READ | 
			  win32con.FILE_SHARE_WRITE | 
			  win32con.FILE_SHARE_DELETE
			, None
			, win32con.OPEN_EXISTING
			, win32con.FILE_FLAG_BACKUP_SEMANTICS
			, None
		)
	except:
		# either it does not exist by this time, or some other issue... blah.
		callback( [(watched_path, '', ACTIONS[2])] )
		return

	callback( [
		(watched_path, fn, ACTIONS.get(action, "Unknown"))
		for action, fn 
		in win32file.ReadDirectoryChangesW(
			folder_handle
			, 1024
			, True
			, win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
			  win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
			  win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
			  win32con.FILE_NOTIFY_CHANGE_SIZE |
			  win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
			  win32con.FILE_NOTIFY_CHANGE_SECURITY
			, None
			, None
		)
	] )