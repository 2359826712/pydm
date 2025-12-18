import win32com.client
try:
    dm = win32com.client.Dispatch('dm.dmsoft')
    print("DM loaded successfully")
    print("Version:", dm.ver())
except Exception as e:
    print("Error loading DM:", e)
