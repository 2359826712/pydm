import win32com.client

dm = win32com.client.Dispatch('dm.dmsoft')  #调用大漠插件,获取大漠对象

print(dm.ver())#输出版本号

ret = dm.RegEx("aa3284965360fb57d3f81ef4ce8379669bd756f91f5" , "" , "121.204.249.29|121.204.253.161|125.77.165.62|125.77.165.131")
if ret == -1:
    print("失败")
else:
    print(ret)

window_hwd = dm.FindWindowByProcess("PioneerGame.exe","","")
dm.BindWindow(window_hwd,"normal","normal","normal",0)
all_text = dm.FindStr(1327,699,1460,733,"开始","ffbc13-000000|090c19-000000",1.0)
print(all_text)