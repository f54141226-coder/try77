# %%
import streamlit as st
import random
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
import secrets

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="成大美食導航 NCKU Foodie", page_icon="🍱", layout="centered")

# --- 📧 寄信功能安全設定 ---
def get_secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return os.environ.get(key, default)

MY_EMAIL = get_secret("MY_EMAIL", "dogee1likego@gmail.com")
APP_PASSWORD = get_secret("APP_PASSWORD", "dmfstlzrbhsqopds")

def send_otp_email(otp_code):
    try:
        msg = MIMEText(f"您好！\n\n您的成大美食 App 管理員驗證碼為：【 {otp_code} 】\n\n請在網頁側邊欄輸入此代碼以啟用管理權限。")
        msg['Subject'] = '【安全驗證】成大美食 App 管理員登入'
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"郵件寄送失敗: {e}")
        return False

# --- 2. 資料庫邏輯 ---
DATA_FILE = "restaurants_v5.csv"

def load_data():
    default_list = [
        {"name": "元味屋", "price": 150, "rating": 4.5, "count": 1},
        {"name": "成大館", "price": 100, "rating": 4.0, "count": 1},
        {"name": "麥當勞", "price": 120, "rating": 4.2, "count": 1}
    ]
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE).to_dict('records')
        except: return default_list
    return default_list

if 'restaurant_db' not in st.session_state:
    st.session_state.restaurant_db = load_data()

# --- 3. 側邊欄：管理員入口 ---
with st.sidebar:
    st.title("🍔 搜尋過濾")
    budget = st.slider("💰 預算上限", 0, 500, 200, 10)
    min_rating = st.slider("⭐ 最低評分要求", 1.0, 5.0, 3.5, 0.1)
    
    st.divider()
    st.subheader("🔐 管理員控制台")
    if st.button("📩 取得電子郵件驗證碼"):
        st.session_state.current_otp = str(secrets.randbelow(900000) + 100000)
        if send_otp_email(st.session_state.current_otp):
            st.success("驗證碼已發送！")
    
    entered_otp = st.text_input("請輸入 6 位數驗證碼", type="password")
    
    if 'current_otp' in st.session_state and entered_otp == st.session_state.current_otp:
        st.warning("🔓 管理員模式已開啟")
        if st.session_state.restaurant_db:
            names = [res['name'] for res in st.session_state.restaurant_db]
            target = st.selectbox("選擇要刪除的餐廳", names)
            if st.button("❌ 確定刪除"):
                st.session_state.restaurant_db = [r for r in st.session_state.restaurant_db if r['name'] != target]
                pd.DataFrame(st.session_state.restaurant_db).to_csv(DATA_FILE, index=False)
                del st.session_state.current_otp
                st.rerun()

# --- 4. 主頁面：抽選功能 ---
st.title("🍴 成大生今天吃什麼？")
st.caption("具備重複檢查與信箱驗證的安全美食地圖")

if st.button("🚀 幫我選一家！", type="primary", use_container_width=True):
    filtered = [r for r in st.session_state.restaurant_db if int(r['price']) <= budget and float(r['rating']) >= min_rating]
    if filtered:
        st.session_state.last_pick = random.choice(filtered)
        st.balloons()
    else:
        st.error("找不到符合條件的餐廳！")

if 'last_pick' in st.session_state and st.session_state.last_pick:
    res = st.session_state.last_pick
    st.success(f"### 🎊 推薦：**{res['name']}**")
    c1, c2, c3 = st.columns(3)
    c1.metric("價位", f"${res['price']}")
    c2.metric("評分", f"⭐ {res['rating']:.1f}")
    c3.metric("次數", f"{int(res['count'])} 次")
    
    with st.expander(f"✨ 我吃完了，我要評價「{res['name']}」"):
        score = st.slider("評價 (1-5)", 1.0, 5.0, 4.0, 0.1)
        if st.button("提交新評分"):
            for item in st.session_state.restaurant_db:
                if item['name'] == res['name']:
                    item['rating'] = round((item['rating'] * item['count'] + score) / (item['count'] + 1), 1)
                    item['count'] += 1
                    break
            pd.DataFrame(st.session_state.restaurant_db).to_csv(DATA_FILE, index=False)
            st.rerun()

# --- 5. 貢獻新餐廳 (優化：防止重複輸入) ---
st.divider()
st.subheader("📝 貢獻新餐廳")
# clear_on_submit=True 確保按下按鈕後輸入框清空
with st.form("add_form", clear_on_submit=True):
    new_name = st.text_input("餐廳名稱 (輸入後按提交)")
    c1, c2 = st.columns(2)
    new_price = c1.number_input("預估價位", value=100, step=10)
    new_rating = c2.slider("初始評分", 1.0, 5.0, 4.0, 0.1)
    
    submitted = st.form_submit_button("✅ 提交餐廳資料", use_container_width=True)
    
    if submitted:
        if not new_name.strip():
            st.error("請輸入餐廳名稱！")
        else:
            # 檢查是否已存在 (不分大小寫與空格)
            existing_names = [r['name'].strip().lower() for r in st.session_state.restaurant_db]
            if new_name.strip().lower() in existing_names:
                st.warning(f"「{new_name}」已經在名單中囉，不需重複新增！")
            else:
                # 新增資料
                new_entry = {
                    "name": new_name.strip(),
                    "price": int(new_price),
                    "rating": float(new_rating),
                    "count": 1
                }
                st.session_state.restaurant_db.append(new_entry)
                # 存入 CSV
                pd.DataFrame(st.session_state.restaurant_db).to_csv(DATA_FILE, index=False)
                st.success(f"成功加入 {new_name}！內容已清空。")
                # 強制重整以刷新下方表格
                st.rerun()

# --- 6. 完整清單 ---
st.divider()
st.subheader("📊 完整校園名單")
if st.session_state.restaurant_db:
    st.dataframe(pd.DataFrame(st.session_state.restaurant_db), use_container_width=True, hide_index=True)


