import json, time, uuid, urllib.request, urllib.error, urllib.parse, ssl, certifi, os
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.image import Image as KivyImage
from kivy.uix.video import Video
from kivy.uix.camera import Camera
from kivy.uix.popup import Popup

FIREBASE_API_KEY = "PUT_YOUR_NEW_KEY_HERE"
PROJECT_ID = "cybergram-67"
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/" + PROJECT_ID + "/databases/(default)/documents"

def get_ctx():
    try: return ssl.create_default_context(cafile=certifi.where())
    except: return ssl._create_unverified_context()
CTX = get_ctx()

def req(url, data=None, token=None, method=None):
    h={"Content-Type":"application/json"}
    if token: h["Authorization"]="Bearer "+token
    body=json.dumps(data).encode() if data is not None else None
    r=urllib.request.Request(url, data=body, headers=h, method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(r, timeout=25, context=CTX) as res:
            t=res.read().decode(); return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        m=e.read().decode()
        try: m=json.loads(m)["error"]["message"]
        except: pass
        raise Exception(m)

def auth(action,email,pw):
    return req(AUTH_URL+action+"?key="+urllib.parse.quote(FIREBASE_API_KEY), {"email":email,"password":pw,"returnSecureToken":True})
def save(path, fields, token):
    return req(FIRESTORE_URL+"/"+path, {"fields":fields}, token=token, method="PATCH")
def get(path, token):
    return req(FIRESTORE_URL+"/"+path, token=token)
def S(v): return {"stringValue":str(v)}
def I(v): return {"integerValue":str(int(v))}
def F(doc,name): return doc.get("fields",{}).get(name,{}).get("stringValue","")
def FI(doc,name):
    try: return int(doc.get("fields",{}).get(name,{}).get("integerValue","0"))
    except: return 0

class CG(App):
    def build(self):
        self.token=None; self.uid=None; self.email=None; self.username=None; self.avatar=""; self.following=set(); self.camera=None; self.last_photo_path=None; self.chat_with_uid=None; self.chat_with_name=None
        from kivy.core.window import Window
        Window.clearcolor=(1,1,1,1); Window.softinput_mode="below_target"
        self.root=BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        self.show_login(); return self.root
    def clear(self): self.root.clear_widgets()
    def head(self,t,s=26): return Label(text=t,font_size=dp(s),bold=True,color=(0.15,0.4,0.95,1),size_hint_y=None,height=dp(50))
    def inp(self,h,pw=False): return TextInput(hint_text=h,password=pw,multiline=False,size_hint_y=None,height=dp(48),padding=[dp(12),dp(12)],background_color=(0.92,0.92,0.95,1),foreground_color=(0,0,0,1),hint_text_color=(0.5,0.5,0.5,1))
    def btn(self,t,cb,color=(0.15,0.4,0.95,1)):
        b=Button(text=t,size_hint_y=None,height=dp(48),background_normal="",background_color=color,color=(1,1,1,1),bold=True); b.bind(on_release=cb); return b
    def msg(self):
        self.message=Label(text="Welcome to CyberGram!",size_hint_y=None,height=dp(50),color=(0.9,0.5,0.1,1)); return self.message
    def show_msg(self,t):
        try: self.message.text=t
        except: pass

    # --- AUTH ---
    def show_login(self):
        self.clear(); self.root.add_widget(self.head("CYBERGRAM"))
        self.e=self.inp("Email"); self.p=self.inp("Password",True)
        self.root.add_widget(self.e); self.root.add_widget(self.p)
        self.root.add_widget(self.btn("LOGIN",self.login)); self.root.add_widget(self.btn("CREATE ACCOUNT",self.show_reg))
        self.root.add_widget(self.msg())
    def show_reg(self,*a):
        self.clear(); self.root.add_widget(self.head("CREATE ACCOUNT"))
        self.e=self.inp("Email"); self.p=self.inp("Password (6+)",True); self.u=self.inp("Username - dot allowed")
        self.root.add_widget(self.e); self.root.add_widget(self.p); self.root.add_widget(self.u)
        self.root.add_widget(self.btn("REGISTER",self.register)); self.root.add_widget(self.btn("BACK",lambda x:self.show_login())); self.root.add_widget(self.msg())
    def register(self,*a):
        email=self.e.text.strip().lower(); pw=self.p.text; un=self.u.text.strip()
        if not email or not pw or not un: self.show_msg("Fill all fields"); return
        if len(pw)<6: self.show_msg("Password 6+"); return
        if not un.replace("_","").replace(".","").isalnum(): self.show_msg("Invalid username"); return
        try:
            self.show_msg("Creating...")
            r=auth("signUp",email,pw); self.token=r["idToken"]; self.uid=r["localId"]; self.email=email
            save("usernames/"+un.lower(), {"username":S(un),"uid":S(self.uid)}, self.token)
            save("profiles/"+self.uid, {"username":S(un),"email":S(email),"uid":S(self.uid),"avatar":S(""),"bio":S("Hi, I'm on CyberGram!"),"createdAt":S(str(int(time.time())))}, self.token)
            self.username=un; self.show_main()
        except Exception as e: self.show_msg("Error: "+str(e))
    def login(self,*a):
        email=self.e.text.strip().lower(); pw=self.p.text
        try:
            self.show_msg("Logging in..."); r=auth("signInWithPassword",email,pw)
            self.token=r["idToken"]; self.uid=r["localId"]; self.email=email
            prof=get("profiles/"+self.uid, self.token); self.username=F(prof,"username"); self.avatar=F(prof,"avatar")
            self.load_following(); self.show_main()
        except Exception as e: self.show_msg("Login error: "+str(e))
    def load_following(self):
        try:
            d=get("follows/"+self.uid, self.token); lst=F(d,"list")
            self.following=set(lst.split(",") if lst else [])
        except: self.following=set()

    # --- MAIN TABS ---
    def show_main(self):
        self.clear()
        from kivy.core.window import Window
        tabs=TabbedPanel(do_default_tab=False, tab_width=Window.width/7)
        t1=TabbedPanelItem(text="Feed"); t1.content=self.feed_screen(); tabs.add_widget(t1)
        t2=TabbedPanelItem(text="Search"); t2.content=self.search_screen(); tabs.add_widget(t2)
        t3=TabbedPanelItem(text="+ Post"); t3.content=self.post_screen(); tabs.add_widget(t3)
        t4=TabbedPanelItem(text="Reels"); t4.content=self.reels_screen(); tabs.add_widget(t4)
        t_cam=TabbedPanelItem(text="Camera"); t_cam.content=self.camera_screen(); tabs.add_widget(t_cam)
        t_dm=TabbedPanelItem(text="DM"); t_dm.content=self.dm_screen(); tabs.add_widget(t_dm)
        t5=TabbedPanelItem(text="Profile"); t5.content=self.profile_screen(); tabs.add_widget(t5)
        self.root.add_widget(tabs); self.root.add_widget(self.msg()); self.show_msg("Welcome @"+str(self.username)+" 🔥")

    # --- FEED + STORIES ---
    def feed_screen(self):
        lay=BoxLayout(orientation="vertical", spacing=dp(8))
        lay.add_widget(Label(text="STORIES - Tap to view", size_hint_y=None, height=dp(30), color=(0.9,0.5,0.1,1)))
        sb=BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(5))
        sb.add_widget(self.btn("+ Add Story", self.add_story, (0.8,0.3,0.8,1)))
        sb.add_widget(self.btn("View Stories", self.view_stories, (0.3,0.6,1,1)))
        lay.add_widget(sb)
        lay.add_widget(self.btn("REFRESH FEED", lambda x: self.show_main()))
        self.feed_box=BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None); self.feed_box.bind(minimum_height=self.feed_box.setter("height"))
        sc=ScrollView(); sc.add_widget(self.feed_box); lay.add_widget(sc)
        self.load_feed(); return lay
    def load_feed(self):
        try:
            d=get("posts?pageSize=50", self.token); docs=d.get("documents",[])
            docs.sort(key=lambda x: int(F(x,"createdAt") or "0"), reverse=True)
            self.feed_box.clear_widgets()
            if not docs: self.feed_box.add_widget(Label(text="No posts yet! Be first 🔥", size_hint_y=None, height=dp(60), color=(0,0,0,1)))
            for doc in docs:
                pid=doc["name"].split("/")[-1]; un=F(doc,"username"); content=F(doc,"content"); img=F(doc,"imageUrl"); likes=FI(doc,"likes")
                box=BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(230))
                box.add_widget(Label(text="@"+un+"  ❤️ "+str(likes), size_hint_y=None, height=dp(30), color=(0,0,0,1)))
                box.add_widget(Label(text=content, size_hint_y=None, height=dp(60), color=(0,0,0,1)))
                if img: box.add_widget(Label(text="🖼️ "+img[:80], size_hint_y=None, height=dp(25), color=(0.2,0.5,0.9,1)))
                row=BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(45), spacing=dp(5))
                def make_like(pid=pid):
                    def f(*a): self.like_post(pid)
                    return f
                def make_com(pid=pid):
                    def f(*a): self.open_comments(pid)
                    return f
                row.add_widget(self.btn("❤️ Like", make_like(), (0.9,0.2,0.4,1)))
                row.add_widget(self.btn("💬 Comments", make_com(), (0.3,0.6,1,1)))
                box.add_widget(row); self.feed_box.add_widget(box)
        except Exception as e: self.show_msg("Feed: "+str(e))
    def like_post(self, pid):
        try:
            doc=get("posts/"+pid, self.token); likes=FI(doc,"likes")+1
            save("posts/"+pid, {"likes":I(likes)}, self.token); self.show_msg("Liked ❤️"); self.load_feed()
        except Exception as e: self.show_msg(str(e))
    def open_comments(self, pid):
        box=BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        ti=self.inp("Write comment..."); box.add_widget(ti)
        def send(*a):
            try:
                cid=uuid.uuid4().hex
                save("comments/"+cid, {"postId":S(pid),"username":S(self.username),"content":S(ti.text),"createdAt":S(str(int(time.time())))}, self.token)
                pop.dismiss(); self.show_msg("Comment posted 💬"); self.show_comments(pid)
            except Exception as e: self.show_msg(str(e))
        box.add_widget(self.btn("POST COMMENT", send)); box.add_widget(self.btn("VIEW ALL COMMENTS", lambda x: self.show_comments(pid)))
        pop=Popup(title="Comments", content=box, size_hint=(0.9,0.6)); pop.open()
    def show_comments(self, pid):
        try:
            d=get("comments?pageSize=100", self.token); txt=""
            for doc in d.get("documents",[]):
                if F(doc,"postId")==pid: txt+="@"+F(doc,"username")+": "+F(doc,"content")+"\n"
            if not txt: txt="No comments yet"
            box=BoxLayout(orientation="vertical"); box.add_widget(Label(text=txt, color=(0,0,0,1))); box.add_widget(self.btn("CLOSE", lambda x: pop.dismiss()))
            pop=Popup(title="All Comments", content=box, size_hint=(0.9,0.7)); pop.open()
        except Exception as e: self.show_msg(str(e))

    # --- STORIES ---
    def add_story(self,*a):
        try:
            sid=uuid.uuid4().hex
            save("stories/"+sid, {"username":S(self.username),"uid":S(self.uid),"content":S("🔥 New Story from @"+self.username),"createdAt":S(str(int(time.time()))),"expires":S(str(int(time.time())+86400))}, self.token)
            self.show_msg("Story posted! Expires in 24h ✨")
        except Exception as e: self.show_msg(str(e))
    def view_stories(self,*a):
        try:
            d=get("stories?pageSize=50", self.token); txt=""; now=int(time.time())
            for doc in d.get("documents",[]):
                if int(F(doc,"expires") or "0")>now: txt+="@"+F(doc,"username")+": "+F(doc,"content")+"\n"
            if not txt: txt="No active stories"
            box=BoxLayout(orientation="vertical"); box.add_widget(Label(text=txt, color=(0,0,0,1))); box.add_widget(self.btn("CLOSE", lambda x: pop.dismiss()))
            pop=Popup(title="Stories", content=box, size_hint=(0.9,0.7)); pop.open()
        except Exception as e: self.show_msg(str(e))

    # --- SEARCH + FOLLOW ---
    def search_screen(self):
        lay=BoxLayout(orientation="vertical", spacing=dp(8))
        self.search_inp=self.inp("Search username..."); lay.add_widget(self.search_inp)
        lay.add_widget(self.btn("SEARCH", self.do_search))
        self.search_box=BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None); self.search_box.bind(minimum_height=self.search_box.setter("height"))
        sc=ScrollView(); sc.add_widget(self.search_box); lay.add_widget(sc); return lay
    def do_search(self,*a):
        q=self.search_inp.text.strip().lower(); self.search_box.clear_widgets()
        if not q: return
        try:
            d=get("profiles?pageSize=100", self.token); found=False
            for doc in d.get("documents",[]):
                un=F(doc,"username")
                if q in un.lower():
                    found=True; uid=F(doc,"uid")
                    row=BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(5))
                    row.add_widget(Label(text="@"+un, color=(0,0,0,1)))
                    is_f = uid in self.following
                    def make_follow(uid=uid, is_f=is_f):
                        def f(*a): self.toggle_follow(uid, is_f)
                        return f
                    row.add_widget(self.btn("Unfollow" if is_f else "Follow", make_follow(), (0.9,0.2,0.4,1) if is_f else (0.15,0.6,0.2,1)))
                    self.search_box.add_widget(row)
            if not found: self.search_box.add_widget(Label(text="No user found", color=(0,0,0,1)))
        except Exception as e: self.show_msg(str(e))
    def toggle_follow(self, target_uid, was_following):
        if was_following: self.following.discard(target_uid)
        else: self.following.add(target_uid)
        try:
            save("follows/"+self.uid, {"list":S(",".join(self.following))}, self.token)
            self.show_msg("Unfollowed" if was_following else "Following ✅"); self.do_search()
        except Exception as e: self.show_msg(str(e))

    # --- POST + REELS ---
    def post_screen(self):
        lay=BoxLayout(orientation="vertical", spacing=dp(8))
        self.post_inp=self.inp("What's happening? Caption..."); self.img_inp=self.inp("Image URL (optional)")
        lay.add_widget(self.post_inp); lay.add_widget(self.img_inp)
        lay.add_widget(self.btn("📸 SHARE POST", self.create_post))
        lay.add_widget(Label(text="Tip: Use Camera tab to take photo, or paste image link here", color=(0.4,0.4,0.4,1), size_hint_y=None, height=dp(30)))
        lay.add_widget(Label(text="--- REELS ---", bold=True, color=(0.9,0.5,0.1,1), size_hint_y=None, height=dp(30)))
        self.reel_inp=self.inp("Reel Video URL (mp4 link)"); self.reel_cap=self.inp("Reel Caption")
        lay.add_widget(self.reel_inp); lay.add_widget(self.reel_cap)
        lay.add_widget(self.btn("🎬 POST REEL", self.create_reel, (0.8,0.2,0.6,1)))
        return lay
    def create_post(self,*a):
        content=self.post_inp.text.strip()
        if not content: self.show_msg("Write something"); return
        try:
            pid=uuid.uuid4().hex
            save("posts/"+pid, {"uid":S(self.uid),"username":S(self.username),"content":S(content),"imageUrl":S(self.img_inp.text.strip()),"likes":I(0),"createdAt":S(str(int(time.time())))}, self.token)
            self.post_inp.text=""; self.img_inp.text=""; self.show_msg("Post shared ✅"); self.show_main()
        except Exception as e: self.show_msg(str(e))
    def create_reel(self,*a):
        url=self.reel_inp.text.strip(); cap=self.reel_cap.text.strip()
        if not url: self.show_msg("Paste video URL"); return
        try:
            rid=uuid.uuid4().hex
            save("reels/"+rid, {"uid":S(self.uid),"username":S(self.username),"videoUrl":S(url),"caption":S(cap),"likes":I(0),"createdAt":S(str(int(time.time())))}, self.token)
            self.show_msg("Reel posted 🎬"); self.show_main()
        except Exception as e: self.show_msg(str(e))
    def reels_screen(self):
        lay=BoxLayout(orientation="vertical", spacing=dp(8))
        lay.add_widget(self.btn("REFRESH REELS", lambda x: self.show_main()))
        self.reels_box=BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None); self.reels_box.bind(minimum_height=self.reels_box.setter("height"))
        sc=ScrollView(); sc.add_widget(self.reels_box); lay.add_widget(sc); self.load_reels(); return lay
    def load_reels(self):
        try:
            d=get("reels?pageSize=50", self.token); docs=d.get("documents",[])
            docs.sort(key=lambda x: int(F(x,"createdAt") or "0"), reverse=True)
            self.reels_box.clear_widgets()
            if not docs: self.reels_box.add_widget(Label(text="No Reels yet! Post first 🎬", size_hint_y=None, height=dp(60), color=(0,0,0,1)))
            for doc in docs:
                rid=doc["name"].split("/")[-1]; un=F(doc,"username"); cap=F(doc,"caption"); url=F(doc,"videoUrl"); likes=FI(doc,"likes")
                box=BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(280))
                box.add_widget(Label(text="@"+un+"  ❤️ "+str(likes), size_hint_y=None, height=dp(30), color=(0,0,0,1)))
                box.add_widget(Label(text=cap, size_hint_y=None, height=dp(40), color=(0,0,0,1)))
                box.add_widget(Label(text="🎬 Video: "+url[:70], size_hint_y=None, height=dp(30), color=(0.2,0.5,0.9,1)))
                try:
                    v=Video(source=url, size_hint_y=None, height=dp(150), state="play", options={"eos":"loop"}); box.add_widget(v)
                except: pass
                def make_like(rid=rid):
                    def f(*a): self.like_reel(rid)
                    return f
                box.add_widget(self.btn("❤️ Like Reel", make_like(), (0.8,0.2,0.6,1)))
                self.reels_box.add_widget(box)
        except Exception as e: self.show_msg("Reels: "+str(e))
    def like_reel(self, rid):
        try:
            doc=get("reels/"+rid, self.token); likes=FI(doc,"likes")+1
            save("reels/"+rid, {"likes":I(likes)}, self.token); self.show_msg("Reel Liked ❤️"); self.load_reels()
        except Exception as e: self.show_msg(str(e))

    # --- CAMERA ---
    def camera_screen(self):
        lay=BoxLayout(orientation="vertical", spacing=dp(8))
        lay.add_widget(Label(text="📸 Take Photo", bold=True, color=(0,0,0,1), size_hint_y=None, height=dp(40)))
        try:
            self.camera=Camera(play=True, resolution=(640,480), size_hint_y=None, height=dp(300))
            lay.add_widget(self.camera)
        except Exception as e:
            lay.add_widget(Label(text="Camera not available: "+str(e), color=(0,0,0,1))); self.camera=None
        self.cap_input=self.inp("Caption for this photo...")
        lay.add_widget(self.cap_input)
        lay.add_widget(self.btn("📸 CAPTURE PHOTO", self.capture_photo, (0.9,0.5,0.1,1)))
        lay.add_widget(self.btn("📸 CAPTURE + POST", self.capture_and_post, (0.15,0.6,0.2,1)))
        self.captured_label=Label(text="No photo yet", color=(0.4,0.4,0.4,1), size_hint_y=None, height=dp(30))
        lay.add_widget(self.captured_label)
        self.photo_preview=KivyImage(size_hint_y=None, height=dp(200))
        lay.add_widget(self.photo_preview)
        lay.add_widget(self.btn("USE LAST PHOTO AS POST", self.post_last_photo))
        return lay
    def capture_photo(self,*a):
        if not self.camera: self.show_msg("Camera not available"); return
        try:
            filename="cybergram_photo.png"; path=os.path.join(os.getcwd(), filename)
            self.camera.export_to_png(path); self.last_photo_path=path
            self.captured_label.text="Saved: "+filename
            self.photo_preview.source=path; self.photo_preview.reload()
            self.show_msg("Photo captured! 📸")
        except Exception as e: self.show_msg("Camera error: "+str(e))
    def capture_and_post(self,*a):
        self.capture_photo()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.post_last_photo(), 0.5)
    def post_last_photo(self,*a):
        caption=self.cap_input.text.strip() if hasattr(self,'cap_input') else ""
        if not caption: caption="📸 New photo from CyberGram!"
        if not self.last_photo_path: self.show_msg("Take a photo first!"); return
        try:
            pid=uuid.uuid4().hex
            save("posts/"+pid, {"uid":S(self.uid),"username":S(self.username),"content":S(caption),"imageUrl":S("📸 Photo: "+str(self.last_photo_path)),"likes":I(0),"createdAt":S(str(int(time.time())))}, self.token)
            self.show_msg("Photo posted! ✅ Check Feed"); self.cap_input.text=""
        except Exception as e: self.show_msg("Post error: "+str(e))

    # --- DM / CHAT ---
    def dm_screen(self):
        lay=BoxLayout(orientation="vertical", spacing=dp(8))
        lay.add_widget(Label(text="💬 Direct Messages", bold=True, color=(0,0,0,1), size_hint_y=None, height=dp(40)))
        lay.add_widget(Label(text="Search user, then tap CHAT", color=(0.4,0.4,0.4,1), size_hint_y=None, height=dp(30)))
        self.dm_search_inp=self.inp("Type username to DM...")
        lay.add_widget(self.dm_search_inp)
        lay.add_widget(self.btn("FIND USER TO DM", self.find_dm_user))
        self.dm_list_box=BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        self.dm_list_box.bind(minimum_height=self.dm_list_box.setter("height"))
        sc=ScrollView(); sc.add_widget(self.dm_list_box); lay.add_widget(sc)
        lay.add_widget(self.btn("REFRESH MY CHATS", lambda x: self.load_my_chats()))
        self.load_my_chats()
        return lay
    def find_dm_user(self,*a):
        q=self.dm_search_inp.text.strip().lower()
        if not q: return
        try:
            d=get("profiles?pageSize=100", self.token)
            self.dm_list_box.clear_widgets()
            found=False
            for doc in d.get("documents",[]):
                un=F(doc,"username"); uid=F(doc,"uid")
                if q in un.lower() and uid != self.uid:
                    found=True
                    row=BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(5))
                    row.add_widget(Label(text="@"+un, color=(0,0,0,1)))
                    def make_chat(uid=uid, un=un):
                        def f(*a): self.open_chat(uid, un)
                        return f
                    row.add_widget(self.btn("💬 CHAT", make_chat(), (0.8,0.2,0.6,1)))
                    self.dm_list_box.add_widget(row)
            if not found:
                self.dm_list_box.add_widget(Label(text="No user found", color=(0,0,0,1)))
        except Exception as e: self.show_msg(str(e))
    def get_chat_id(self, other_uid):
        ids=sorted([self.uid, other_uid]); return ids[0]+"_"+ids[1]
    def load_my_chats(self):
        try:
            d=get("messages?pageSize=100", self.token)
            users={}
            for doc in d.get("documents",[]):
                sender=F(doc,"senderId"); receiver=F(doc,"receiverId"); senderName=F(doc,"senderName")
                if sender==self.uid: users[receiver]=F(doc,"receiverName")
                elif receiver==self.uid: users[sender]=senderName
            self.dm_list_box.clear_widgets()
            if not users:
                self.dm_list_box.add_widget(Label(text="No chats yet. Search user above to start!", color=(0,0,0,1)))
            for uid, name in users.items():
                row=BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(5))
                row.add_widget(Label(text="@"+name, color=(0,0,0,1)))
                def make_chat(uid=uid, un=name):
                    def f(*a): self.open_chat(uid, un)
                    return f
                row.add_widget(self.btn("OPEN CHAT", make_chat(), (0.3,0.6,1,1)))
                self.dm_list_box.add_widget(row)
        except Exception as e: self.show_msg(str(e))
    def open_chat(self, other_uid, other_name):
        self.chat_with_uid=other_uid; self.chat_with_name=other_name
        box=BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        box.add_widget(Label(text="Chat with @"+other_name, bold=True, color=(0,0,0,1), size_hint_y=None, height=dp(35)))
        self.chat_box=BoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None)
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        sc=ScrollView(); sc.add_widget(self.chat_box); box.add_widget(sc)
        box.add_widget(self.btn("REFRESH", lambda x: self.load_chat_messages()))
        self.chat_inp=self.inp("Type message...")
        box.add_widget(self.chat_inp)
        box.add_widget(self.btn("SEND 💬", self.send_dm, (0.15,0.6,0.2,1)))
        box.add_widget(self.btn("CLOSE", lambda x: pop.dismiss()))
        pop=Popup(title="DM - @"+other_name, content=box, size_hint=(0.95,0.85))
        self.chat_popup=pop; pop.open()
        self.load_chat_messages()
    def load_chat_messages(self):
        try:
            d=get("messages?pageSize=200", self.token)
            chat_id=self.get_chat_id(self.chat_with_uid)
            msgs=[]
            for doc in d.get("documents",[]):
                if F(doc,"chatId")==chat_id:
                    msgs.append((int(F(doc,"createdAt") or "0"), F(doc,"senderName"), F(doc,"content")))
            msgs.sort()
            self.chat_box.clear_widgets()
            if not msgs:
                self.chat_box.add_widget(Label(text="No messages yet. Say Hi! 👋", size_hint_y=None, height=dp(40), color=(0,0,0,1)))
            for _, sender, content in msgs:
                who="You" if sender==self.username else "@"+sender
                self.chat_box.add_widget(Label(text=who+": "+content, size_hint_y=None, height=dp(40), color=(0,0,0,1)))
        except Exception as e: self.show_msg(str(e))
    def send_dm(self,*a):
        txt=self.chat_inp.text.strip()
        if not txt: return
        try:
            mid=uuid.uuid4().hex; chat_id=self.get_chat_id(self.chat_with_uid)
            save("messages/"+mid, {"chatId":S(chat_id),"senderId":S(self.uid),"senderName":S(self.username),"receiverId":S(self.chat_with_uid),"receiverName":S(self.chat_with_name),"content":S(txt),"createdAt":S(str(int(time.time())))}, self.token)
            self.chat_inp.text=""; self.load_chat_messages()
        except Exception as e: self.show_msg(str(e))

    # --- PROFILE ---
    def profile_screen(self):
        lay=BoxLayout(orientation="vertical", spacing=dp(8))
        lay.add_widget(Label(text="@"+str(self.username), font_size=dp(24), bold=True, color=(0,0,0,1), size_hint_y=None, height=dp(40)))
        lay.add_widget(Label(text="Following: "+str(len(self.following))+" | Bio: Hi, I'm on CyberGram!", color=(0.4,0.4,0.4,1), size_hint_y=None, height=dp(30)))
        self.bio_inp=self.inp("New Bio"); lay.add_widget(self.bio_inp)
        lay.add_widget(self.btn("UPDATE BIO", self.update_bio))
        lay.add_widget(self.btn("MY POSTS - Refresh", lambda x: self.show_main()))
        lay.add_widget(self.btn("LOG OUT", lambda x: self.show_login(), (0.9,0.2,0.2,1)))
        return lay
    def update_bio(self,*a):
        try:
            save("profiles/"+self.uid, {"bio":S(self.bio_inp.text)}, self.token); self.show_msg("Bio updated ✅")
        except Exception as e: self.show_msg(str(e))

if __name__=="__main__": CG().run()
