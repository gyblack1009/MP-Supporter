## pyinstaller --noconsole --onefile main.py
import customtkinter as ctk
import webbrowser
import pandas as pd
import threading
import pyperclip
import requests
import json
import time
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ==========================================
# 📌 설정 및 환경 변수
# ==========================================
CURRENT_VERSION = "1.0.0"

# Github Raw URL을 지정하세요. (main.py 코드가 수정되면 자동으로 로컬 코드를 덮어쓰고 재실행됩니다)
VERSION_CHECK_URL = "https://raw.githubusercontent.com/사용자/리포지토리/main/version.json"
UPDATE_CODE_URL = "https://raw.githubusercontent.com/사용자/리포지토리/main/main.py"

SHEET_ID = "1sAuycErpNCvAFq7-9-I6J8D2ONmMmqe2NDh17lxp8TU"
URL_TOTAL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbylPvvwlkhCFXBco3qEzxaXhHnu85Dtb6-4kWkAIEn5hI2e2sFbtvHmKLRH7RPOddETVQ/exec"

ROBLOX_CLIENT_ID = "1681897459105367104"
ROBLOX_CLIENT_SECRET = "RBX-eP19qDEvWE2ZcLYtSyRQgN1xccO1D-KVtU4zjeaWmSDbXZvO-eBjRsbAIy3Fcvbk"
REDIRECT_URI = "http://localhost:8080/oauth/callback"

auth_code_received = None

REPORT_FORMATS = {
    "긴급체포": "{rank} {target}님을 {items}으로 긴급 체포 및 영창 {total}초 수감하며, 본 조치에 대해 이의가 있거나 구제 절차가 필요하신 경우, 국방헬프콜을 통해 이의제기를 하실 수 있습니다.",
    "특전사 출입": "군사경찰 직무수행법 제13조에 의거 특전사 부지 출입 합니다.\n",
    "지작사 출입": "군사경찰 직무수행법 제13조에 의거 지작사 부지 출입 합니다.\n",
    "2사단 출입": "군사경찰 직무수행법 제13조에 의거 2사단 부지 출입 합니다.",
    "즉시체포": "병영규정 제18조 3항, 영내 질서 붕괴 우려로 고지 없이 즉시 체포 및 수감합니다.",
    "형집행 보고서": "담당자 : {manager}\n대상자 : {target}\n형량 : {total}\n사유 : {items}",
    "구금 보고서": "대상자 닉네임 및 계급 : {target} / {rank}\n소속 : {Div}\n형량 : {total}\n사유 : {items}\n누적 횟수 : N"
}

AUTO_COPY_SENTENCES = ["특전사 출입", "지작사 출입", "2사단 출입"]

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code_received
        query_components = parse_qs(urlparse(self.path).query)
        if "code" in query_components:
            auth_code_received = query_components["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h3>로블록스 계정 연동 성공! 이 창을 닫고 프로그램으로 돌아가세요.</h3>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

class MilitaryPoliceSupportApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("군사경찰 V2")
        self.geometry("280x420")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.user_roblox_id = "미연동"
        self.df_total = None
        self.law_checkboxes = {}  
        self.law_frames = {}
        self.is_gajung = False    
        self.is_transparent = False

        # 실행 시 자동 코드 업데이트 체크
        self.check_auto_update()
        self.show_login_frame()

    def check_auto_update(self):
        """서버 상의 소스 코드가 수정되었는지 확인 후 자동으로 소스 코드를 업데이트하고 재실행합니다."""
        try:
            # 1. 버전 확인
            res = requests.get(VERSION_CHECK_URL, timeout=3)
            if res.status_code == 200:
                data = res.json()
                latest_version = data.get("version")
                if latest_version and latest_version != CURRENT_VERSION:
                    # 2. 최신 코드 다운로드 후 자기 자신 파일에 덮어쓰기
                    code_res = requests.get(UPDATE_CODE_URL, timeout=5)
                    if code_res.status_code == 200:
                        current_file = os.path.realpath(sys.argv[0])
                        with open(current_file, "w", encoding="utf-8") as f:
                            f.write(code_res.text)
                        # 3. 프로그램 재실행
                        os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print("자동 업데이트 검사 스킵:", e)

    def show_login_frame(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(fill="both", expand=True, padx=10, pady=10)

        title_lbl = ctk.CTkLabel(self.login_frame, text="로블록스 계정 연동", font=ctk.CTkFont(size=14, weight="bold"))
        title_lbl.pack(pady=30)

        self.auth_btn = ctk.CTkButton(self.login_frame, text="🔗 Roblox 로그인", fg_color="#00A2FF", width=200, height=32, font=ctk.CTkFont(size=12, weight="bold"), command=self.start_roblox_oauth)
        self.auth_btn.pack(pady=15)

        self.login_status_lbl = ctk.CTkLabel(self.login_frame, text="", font=ctk.CTkFont(size=10))
        self.login_status_lbl.pack(pady=5)

    def start_roblox_oauth(self):
        self.login_status_lbl.configure(text="🌐 브라우저에서 인가를 진행하세요...", text_color="#58ACFA")
        self.auth_btn.configure(state="disabled")
        threading.Thread(target=self.run_oauth_flow, daemon=True).start()

    def run_oauth_flow(self):
        global auth_code_received
        auth_code_received = None

        auth_url = (
            f"https://apis.roblox.com/oauth/v1/authorize?"
            f"client_id={ROBLOX_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={REDIRECT_URI}&"
            f"scope=openid profile"
        )
        webbrowser.open(auth_url)

        server_address = ('', 8080)
        httpd = HTTPServer(server_address, OAuthCallbackHandler)
        while auth_code_received is None:
            httpd.handle_request()
        httpd.server_close()

        self.fetch_roblox_user_profile(auth_code_received)

    def fetch_roblox_user_profile(self, code):
        token_url = "https://apis.roblox.com/oauth/v1/token"
        payload = {
            "client_id": ROBLOX_CLIENT_ID,
            "client_secret": ROBLOX_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        try:
            res = requests.post(token_url, data=payload, timeout=5)
            access_token = res.json().get("access_token")

            user_info_url = "https://apis.roblox.com/oauth/v1/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            user_data = requests.get(user_info_url, headers=headers, timeout=5).json()

            self.user_roblox_id = user_data.get("preferred_username") or user_data.get("name")
            self.after(0, self.on_login_success)
        except Exception:
            self.after(0, lambda: self.login_status_lbl.configure(text="❌ 연동 실패!", text_color="#A32A2A"))
            self.after(0, lambda: self.auth_btn.configure(state="normal"))

    def on_login_success(self):
        self.login_frame.destroy()
        self.init_main_ui()

    def init_main_ui(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=8, pady=4)

        user_lbl = ctk.CTkLabel(top_frame, text=f"👤 {self.user_roblox_id}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2EA043")
        user_lbl.pack(side="left", padx=2)

        self.tabview = ctk.CTkTabview(self, corner_radius=6)
        self.tabview.pack(padx=6, pady=4, fill="both", expand=True)

        self.tabview.add("법률계산기")
        self.tabview.add("매뉴얼")

        self.init_law_tab()
        self.init_manual_tab()

        threading.Thread(target=self.load_sheet_data, daemon=True).start()

    def init_law_tab(self):
        tab = self.tabview.tab("법률계산기")

        self.main_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=2, pady=2)

        util_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        util_frame.pack(fill="x", pady=2)
        
        self.alpha_btn = ctk.CTkButton(
            util_frame, text="👁️ 반투명 (OFF)", height=24, 
            font=ctk.CTkFont(size=10, weight="bold"), fg_color="#333333", command=self.toggle_transparency
        )
        self.alpha_btn.pack(fill="x")

        self.manager_entry = ctk.CTkEntry(self.main_scroll, height=26, font=ctk.CTkFont(size=10, weight="bold"))
        self.manager_entry.insert(0, f"담당자: {self.user_roblox_id}")
        self.manager_entry.configure(state="disabled", fg_color="#2A2A2A", text_color="#A0A0A0")
        self.manager_entry.pack(fill="x", pady=2)

        self.search_entry = ctk.CTkEntry(self.main_scroll, placeholder_text="🔍 법률 항목 검색...", height=26, font=ctk.CTkFont(size=10))
        self.search_entry.pack(fill="x", pady=2)
        self.search_entry.bind("<KeyRelease>", self.filter_law_items)

        self.law_container = ctk.CTkFrame(self.main_scroll, fg_color="#1E1E1E", corner_radius=6)
        self.law_container.pack(pady=4, fill="x")
        
        self.loading_lbl = ctk.CTkLabel(self.law_container, text="🔄 항목 불러오는 중...", font=ctk.CTkFont(size=10, weight="bold"))
        self.loading_lbl.pack(pady=8)

        doc_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        doc_frame.pack(fill="x", pady=2)
        btn_f = ctk.CTkFont(size=9, weight="bold")
        
        ctk.CTkButton(doc_frame, text="종합매뉴얼", height=22, font=btn_f, command=lambda: self.open_doc("https://docs.google.com/document/d/1ieEW6zZLSeLvQnwc59ePCH5_GJ1N76eH3oJFYJd_8UI/edit?usp=sharing")).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(doc_frame, text="직무법률", height=22, font=btn_f, command=lambda: self.open_doc("https://docs.google.com/document/d/1o-Aj2TlcSHsHXLDJZ_7Q8Ni7uxF9RRTAjPFE2d2A8Xc/edit?usp=sharing")).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(doc_frame, text="영창안내", height=22, font=btn_f, command=lambda: self.open_doc("https://docs.google.com/document/d/1Y0r-A344KYD6OFGWyUxhG5-vn7kmeAsmjF_rjd3K8jY/edit?usp=sharing")).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(doc_frame, text="병영규정", height=22, font=btn_f, command=lambda: self.open_doc("https://docs.google.com/document/d/1OW1SM-JlU8g-tJOFNz4HVcGAm6R8g1xWhFbLh9dbLIk/edit?usp=sharing")).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        doc_frame.grid_columnconfigure((0, 1), weight=1)

        tool_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        tool_frame.pack(fill="x", pady=2)

        self.sentence_combobox = ctk.CTkComboBox(
            tool_frame, values=list(REPORT_FORMATS.keys()), height=24, 
            font=ctk.CTkFont(size=10, weight="bold"), dropdown_font=ctk.CTkFont(size=10, weight="bold"),
            command=self.on_sentence_select
        )
        self.sentence_combobox.set("문장 선택")
        self.sentence_combobox.grid(row=0, column=0, columnspan=2, pady=2, sticky="ew")

        self.rank_combobox = ctk.CTkComboBox(
            tool_frame, values=["훈병", "이병", "일병", "상병", "병장", "하사", "중사", "상사", "원사", "소위", "중위", "대위", "소령", "중령", "대령", "준장", "소장", "중장", "대장"], 
            height=22, font=ctk.CTkFont(size=9, weight="bold"), dropdown_font=ctk.CTkFont(size=9, weight="bold")
        )
        self.rank_combobox.set("계급 선택")
        self.rank_combobox.grid(row=1, column=0, padx=1, pady=2, sticky="ew")

        self.div_combobox = ctk.CTkComboBox(
            tool_frame, values=["특수전사령부", "7여단", "13여단", "특항단", "군사경찰", "7군단", "8사단", "2사단", "3사단", "육군훈련소"], 
            height=22, font=ctk.CTkFont(size=9, weight="bold"), dropdown_font=ctk.CTkFont(size=9, weight="bold")
        )
        self.div_combobox.set("소속 선택")
        self.div_combobox.grid(row=1, column=1, padx=1, pady=2, sticky="ew")
        tool_frame.grid_columnconfigure((0, 1), weight=1)

        self.gajung_btn = ctk.CTkButton(self.main_scroll, text="가중X2 (OFF)", height=22, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#4A4A4A", command=self.toggle_gajung)
        self.gajung_btn.pack(fill="x", pady=2)

        self.target_entry = ctk.CTkEntry(self.main_scroll, placeholder_text="대상자 닉네임 입력", height=26, font=ctk.CTkFont(size=10, weight="bold"))
        self.target_entry.pack(fill="x", pady=2)

        self.copy_btn = ctk.CTkButton(self.main_scroll, text="📋 문장 복사", height=28, font=ctk.CTkFont(size=10, weight="bold"), fg_color="#1E6B37", command=self.copy_sentence)
        self.copy_btn.pack(fill="x", pady=4)

        result_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        result_frame.pack(fill="x", padx=2, pady=2)

        self.total_score_lbl = ctk.CTkLabel(result_frame, text="형량: 0초", font=ctk.CTkFont(size=11, weight="bold"), text_color="#58ACFA")
        self.total_score_lbl.pack(side="left")

        reset_btn = ctk.CTkButton(result_frame, text="초기화", width=50, height=20, font=ctk.CTkFont(size=9, weight="bold"), fg_color="#A32A2A", command=self.reset_all)
        reset_btn.pack(side="right")

    def init_manual_tab(self):
        """매뉴얼 탭의 레이아웃 및 여백 개선"""
        tab = self.tabview.tab("매뉴얼")
        
        self.manual_scroll_frame = ctk.CTkScrollableFrame(tab, width=75, label_text="목차", label_font=ctk.CTkFont(size=9, weight="bold"))
        self.manual_scroll_frame.pack(side="left", fill="y", padx=2, pady=2)
        
        # 텍스트 상자 가독성을 위해 폰트 및 여백 조정
        self.manual_text = ctk.CTkTextbox(
            tab, 
            font=ctk.CTkFont(family="Consolas", size=10), 
            wrap="word", 
            activate_scrollbars=True
        )
        self.manual_text.pack(side="right", fill="both", expand=True, padx=4, pady=2)

    def toggle_transparency(self):
        self.is_transparent = not self.is_transparent
        if self.is_transparent:
            self.attributes("-alpha", 0.65)
            self.alpha_btn.configure(text="👁️ 반투명 (ON)", fg_color="#2B7A78")
        else:
            self.attributes("-alpha", 1.0)
            self.alpha_btn.configure(text="👁️ 반투명 (OFF)", fg_color="#333333")

    def filter_law_items(self, event=None):
        query = self.search_entry.get().strip().lower()
        for name, frame in self.law_frames.items():
            if query in name.lower():
                frame.pack(fill="x", pady=2, padx=4)
            else:
                frame.pack_forget()

    def open_doc(self, url):
        webbrowser.open(url)

    def on_sentence_select(self, choice):
        if choice in AUTO_COPY_SENTENCES:
            sentence = REPORT_FORMATS[choice]
            pyperclip.copy(sentence)
            self.copy_btn.configure(text=f"✅ {choice} 복사완료!")
            self.sentence_combobox.set("문장 선택")
            self.after(1500, lambda: self.copy_btn.configure(text="📋 문장 복사"))

    def calculate_total(self):
        selected_seconds = [seconds for name, (cb, var, seconds) in self.law_checkboxes.items() if var.get() == 1]
        
        if not selected_seconds:
            self.total_score_lbl.configure(text="형량: 0초")
            return

        total_seconds = 0
        if len(selected_seconds) == 1:
            total_seconds = selected_seconds[0]
        elif len(selected_seconds) >= 2:
            max_sec = max(selected_seconds)
            total_seconds = int(max_sec * 1.5)

        if self.is_gajung:
            total_seconds *= 2

        if total_seconds < 180:
            total_seconds = 180
        elif total_seconds > 3600:
            total_seconds = 3600

        minutes = total_seconds // 60
        if minutes > 0:
            self.total_score_lbl.configure(text=f"형량: {total_seconds}초({minutes}분)")
        else:
            self.total_score_lbl.configure(text=f"형량: {total_seconds}초")

    def toggle_gajung(self):
        self.is_gajung = not self.is_gajung
        if self.is_gajung:
            self.gajung_btn.configure(text="가중X2 (ON)", fg_color="#D96B00")
        else:
            self.gajung_btn.configure(text="가중X2 (OFF)", fg_color="#4A4A4A")
        self.calculate_total()

    def send_to_sheet_history(self, manager, target, items, total):
        if not GAS_WEB_APP_URL or "YOUR_GOOGLE" in GAS_WEB_APP_URL:
            return

        payload = {
            "manager": manager,
            "target": target,
            "items": items,
            "total": total
        }

        def _send():
            try:
                requests.post(GAS_WEB_APP_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, timeout=5)
            except Exception as e:
                print("시트 기록 실패:", e)

        threading.Thread(target=_send, daemon=True).start()

    def copy_sentence(self):
        manager = self.user_roblox_id
        target = self.target_entry.get() or "미입력"
        rank = self.rank_combobox.get()
        if rank == "계급 선택": rank = "계급미정"
        div = self.div_combobox.get()
        if div == "소속 선택": div = "소속미정"
        
        action_type = self.sentence_combobox.get()
        if action_type not in REPORT_FORMATS:
            self.copy_btn.configure(text="❌ 문장 선택 필요")
            self.after(1500, lambda: self.copy_btn.configure(text="📋 문장 복사"))
            return

        checked_items = [name for name, (cb, var, sec) in self.law_checkboxes.items() if var.get() == 1]
        items_str = ", ".join(checked_items) if checked_items else "없음"
        
        raw_score_text = self.total_score_lbl.cget("text")
        just_seconds = raw_score_text.replace("형량: ", "").split("초")[0].strip()

        base_format = REPORT_FORMATS[action_type]
        sentence = base_format.format(manager=manager, rank=rank, target=target, items=items_str, total=just_seconds, Div=div)
        
        pyperclip.copy(sentence)
        self.copy_btn.configure(text="✅ 복사 완료!")
        self.after(1500, lambda: self.copy_btn.configure(text="📋 문장 복사"))

        self.send_to_sheet_history(manager, target, items_str, f"{just_seconds}초")

    def load_sheet_data(self):
        try:
            self.df_total = pd.read_csv(URL_TOTAL_SHEET)
            self.df_total.columns = self.df_total.columns.str.strip()
            self.after(0, self.create_law_checkboxes)
            self.after(0, self.update_other_tabs)
        except Exception as e:
            print("시트 로드 오류:", e)

    def create_law_checkboxes(self):
        if self.df_total is None: return
        self.loading_lbl.destroy()
        df_law = self.df_total[self.df_total.iloc[:, 0] == "법률계산기"]

        for _, row in df_law.iterrows():
            name = str(row.iloc[1])    
            try: seconds = int(row.iloc[2])
            except: seconds = 0
            
            display_text = f"{seconds}초"

            row_frame = ctk.CTkFrame(self.law_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=2, padx=4)

            var = ctk.IntVar()
            cb = ctk.CTkCheckBox(row_frame, text=name, variable=var, command=self.calculate_total, font=ctk.CTkFont(size=9, weight="bold"), checkbox_width=12, checkbox_height=12)
            cb.pack(side="left")

            lbl = ctk.CTkLabel(row_frame, text=display_text, text_color="#A0A0A0", font=ctk.CTkFont(size=9, weight="bold"))
            lbl.pack(side="right")

            self.law_checkboxes[name] = (cb, var, seconds)
            self.law_frames[name] = row_frame

    def reset_all(self):
        for name, (cb, var, sec) in self.law_checkboxes.items():
            var.set(0)
        self.target_entry.delete(0, "end")
        self.search_entry.delete(0, "end")
        self.filter_law_items()
        self.rank_combobox.set("계급 선택")
        self.div_combobox.set("소속 선택")
        self.sentence_combobox.set("문장 선택")
        self.is_gajung = False
        self.gajung_btn.configure(text="가중X2 (OFF)", fg_color="#4A4A4A")
        self.calculate_total()

    def update_other_tabs(self):
        if self.df_total is None: return
        df_m = self.df_total[self.df_total.iloc[:, 0] == "매뉴얼"]
        if not df_m.empty:
            for widget in self.manual_scroll_frame.winfo_children(): widget.destroy()
            for _, row in df_m.iterrows():
                name = str(row.iloc[1])
                btn = ctk.CTkButton(self.manual_scroll_frame, text=name, height=20, font=ctk.CTkFont(size=8, weight="bold"), command=lambda n=name: self.on_manual_select(n))
                btn.pack(fill="x", pady=1)
            self.on_manual_select(str(df_m.iloc[0, 1]))

    def on_manual_select(self, choice):
        row = self.df_total[(self.df_total.iloc[:, 0] == "매뉴얼") & (self.df_total.iloc[:, 1] == choice)]
        if not row.empty:
            detail = str(row.iloc[0, 3]).replace("\\n", "\n")
            self.manual_text.delete("1.0", "end")
            self.manual_text.insert("1.0", f"📖 {choice}\n\n{detail}")

if __name__ == "__main__":
    app = MilitaryPoliceSupportApp()
    app.mainloop()
