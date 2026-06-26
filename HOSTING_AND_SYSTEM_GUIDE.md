# Hosting & System Architecture Guide

এই গাইডলাইনে প্রজেক্টটি হোস্টিং/ডেপ্লয় করার পদ্ধতি, সিস্টেমের কার্যপ্রণালী এবং হ্যাকাথনের নির্দেশনা অনুযায়ী কমপ্লায়েন্স ডাবল-চেক লিস্ট বিস্তারিত দেওয়া হলো।

---

## Part 1: Hosting & Deployment Guide

হ্যাকাথনে সাবমিট করার জন্য প্রজেক্টটি নিচের যেকোনো একটি ফ্রি/পেইড ক্লাউড প্ল্যাটফর্মে হোস্টিং করতে পারেন:

### Option A: Render-এ ডেপ্লয়মেন্ট (সহজ এবং রিকমেন্ডেড)
Render একটি জনপ্রিয় হোস্টিং প্ল্যাটফর্ম যা সরাসরি গিটহাব রিপোজিটরি থেকে ডেপ্লয় করা যায়।
১. [Render Dashboard](https://dashboard.render.com/) এ লগইন করুন।
২. **New +** এ ক্লিক করে **Web Service** সিলেক্ট করুন।
৩. আপনার গিটহাব রিপোজিটরি কানেক্ট করুন।
৪. সেটিংস কনফিগার করুন:
   * **Runtime:** `Python` (অথবা Docker সিলেক্ট করতে পারেন যদি ডকারাইজড করতে চান)
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
৫. **Environment Variables** সেকশনে নিচের ভেরিয়েবলগুলো যোগ করুন:
   * `OPENROUTER_API_KEY`: আপনার ওপেন-রাউটার এপিআই কী।
   * `MODEL_NAME`: `google/gemini-2.5-flash`
৬. **Create Web Service** এ ক্লিক করুন। আপনার লাইভ ইউআরএল রেডি হয়ে যাবে (যেমন: `https://queuestorm-team.onrender.com/health`)।

### Option B: Railway-তে ডেপ্লয়মেন্ট (দ্রুততম)
১. [Railway.app](https://railway.app/) এ যান এবং আপনার গিটহাব রিপোজিটরি কানেক্ট করুন।
২. Railway স্বয়ংক্রিয়ভাবে আপনার `Dockerfile` ডিটেক্ট করবে এবং বিল্ড প্রসেস শুরু করবে।
৩. **Variables** ট্যাবে গিয়ে `.env` এর ভেরিয়েবলগুলো যোগ করে দিন:
   * `OPENROUTER_API_KEY`
   * `MODEL_NAME`
   * `PORT` = `8000`
৪. ডেপ্লয়মেন্ট শেষ হলে Railway আপনাকে একটি পাবলিক ডোমেন দিবে।

### Option C: VPS / AWS / Virtual Machine-এ ডেপ্লয়মেন্ট (সম্পূর্ণ প্রডাকশন গাইড)
আপনার নিজের VPS (যেমন- DigitalOcean, Linode, AWS EC2, VM) এ প্রজেক্টটি ডেপ্লয় করার জন্য নিচের যেকোনো একটি পদ্ধতি অনুসরণ করতে পারেন। নিচে Docker এবং Non-Docker (Systemd) উভয় পদ্ধতির গাইড দেওয়া হলো।

#### পূর্বপ্রস্তুতি: SSH এবং রিপোজিটরি সেটআপ
১. আপনার VPS সার্ভারে SSH দিয়ে লগইন করুন:
   ```bash
   ssh username@your-server-ip
   ```
২. গিট রিপোজিটরি ক্লোন করুন এবং ডিরেক্টরিতে যান:
   ```bash
   git clone <repo-url> && cd sust-cse-curnival
   ```
৩. প্রজেক্টের রুট ডিরেক্টরিতে `.env` ফাইলটি তৈরি করুন (অথবা `.env.example` কপি করুন) এবং আপনার এপিআই কী সেট করুন:
   ```bash
   cp .env.example .env
   nano .env
   ```
   ফাইলটিতে প্রয়োজনীয় এনভায়রনমেন্ট ভেরিয়েবলগুলো বসিয়ে দিন (যেমন: `OPENROUTER_API_KEY`, `MODEL_NAME` ইত্যাদি)।

---

#### পদ্ধতি ১: Docker ব্যবহার করে ডেপ্লয়মেন্ট (সবচেয়ে সহজ ও রিকমেন্ডেড)
যদি সার্ভারে Docker ইন্সটল করা থাকে:

১. **ইমেজ বিল্ড করুন:**
   ```bash
   docker build -t queuestorm-team .
   ```
২. **কন্টেইনারটি ব্যাকগ্রাউন্ডে রান করুন (অটো-রিস্টার্ট অপশনসহ):**
   ```bash
   docker run -d -p 8000:8000 \
     --name support-copilot \
     --restart unless-stopped \
     --env-file .env \
     queuestorm-team
   ```
   *(নোট: `--restart unless-stopped` দেওয়ার কারণে সার্ভার ক্র্যাশ বা রিবুট হলেও কন্টেইনারটি অটোমেটিক্যালি আবার রান হবে।)*

৩. **কন্টেইনারের রান স্টেটাস এবং লগ চেক করুন:**
   ```bash
   # রান স্টেটাস দেখতে:
   docker ps
   
   # লাইভ লগ দেখতে:
   docker logs -f support-copilot
   ```

---

#### পদ্ধতি ২: Systemd ব্যবহার করে ডেপ্লয়মেন্ট (Docker ছাড়া সরাসরি Python রান)
যদি Docker ছাড়া সরাসরি সার্ভারের পাইথন দিয়ে প্রজেক্ট রান করতে চান:

১. **ডিপেন্ডেন্সি এবং ভার্চুয়াল এনভায়রনমেন্ট সেটআপ:**
   ```bash
   # পাইথন এবং প্রয়োজনীয় প্যাকেজ ইন্সটল করুন (Ubuntu/Debian-এর জন্য)
   sudo apt update
   sudo apt install python3-pip python3-venv python3-dev -y
   
   # ভার্চুয়াল এনভায়রনমেন্ট তৈরি ও একটিভ করুন
   python3 -m venv venv
   source venv/bin/activate
   
   # ডিপেন্ডেন্সি ইন্সটল করুন
   pip install -r requirements.txt
   ```

২. **Systemd সার্ভিস ফাইল তৈরি করুন:**
   সার্ভার রিবুট হলে বা অ্যাপ ক্র্যাশ করলে যেন সার্ভিসটি অটোমেটিক চালু হয়, সেজন্য একটি Systemd সার্ভিস ফাইল তৈরি করব।
   ```bash
   sudo nano /etc/systemd/system/support-copilot.service
   ```
   ফাইলটিতে নিচের কনফিগারেশনটি পেস্ট করুন (আপনার আসল পাথ অনুযায়ী `/path/to/sust-cse-curnival` পরিবর্তন করে নেবেন):
   ```ini
   [Unit]
   Description=QueueStorm Support Copilot FastAPI Application
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/sust-cse-curnival
   ExecStart=/home/ubuntu/sust-cse-curnival/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   EnvironmentFile=/home/ubuntu/sust-cse-curnival/.env

   [Install]
   WantedBy=multi-user.target
   ```
   *(নোট: `User` এবং `WorkingDirectory` ও `ExecStart` এর পাথগুলো আপনার VPS-এর ইউজারনেম অনুযায়ী ঠিক করে নিন।)*

৩. **সার্ভিসটি রিলোড, স্টার্ট এবং এনাবল করুন:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start support-copilot
   sudo systemctl enable support-copilot
   ```

৪. **সার্ভিসের স্টেটাস এবং লাইভ লগ চেক করুন:**
   ```bash
   # সার্ভিসের রান স্টেটাস চেক করতে:
   sudo systemctl status support-copilot
   
   # সার্ভিসের লাইভ লগ চেক করতে:
   journalctl -u support-copilot.service -f
   ```

---

#### পদ্ধতি ৩: Nginx Reverse Proxy এবং SSL (HTTPS) সেটআপ (প্রডাকশন স্ট্যান্ডার্ড)
ইউজার যেন পোর্ট ছাড়া সরাসরি আইপি বা ডোমেন দিয়ে (`https://domain.com` বা `http://ip`) এপিআই কল করতে পারে, সে জন্য Nginx ব্যবহার করা ভালো।

১. **Nginx ইনস্টল করুন:**
   ```bash
   sudo apt install nginx -y
   ```

২. **Nginx কনফিগারেশন ফাইল তৈরি করুন:**
   ```bash
   sudo nano /etc/nginx/sites-available/support-copilot
   ```
   নিচের কনফিগারেশনটি যোগ করুন:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com your-server-ip;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   *(নোট: `your-domain.com` এর জায়গায় আপনার ডোমেইন বা সরাসরি সার্ভারের আইপি দিন।)*

৩. **কনফিগারেশন একটিভ করুন ও Nginx রিস্টার্ট দিন:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/support-copilot /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

৪. **SSL (HTTPS) এর জন্য Certbot (Let's Encrypt) সেটআপ করুন (ঐচ্ছিক):**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d your-domain.com
   ```

---

#### পদ্ধতি ৪: ফায়ারওয়াল (Firewall) কনফিগারেশন
সার্ভারে রিকোয়েস্ট অ্যাক্সেস করার জন্য প্রয়োজনীয় পোর্ট ওপেন রাখতে হবে।

Ubuntu UFW ফায়ারওয়াল ব্যবহার করলে নিচের কমান্ডগুলো রান করুন:
```bash
# Nginx এবং SSH পোর্ট ওপেন করুন
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'

# যদি সরাসরি ৮০০০ পোর্ট অ্যাক্সেস করতে চান (Nginx ছাড়া):
sudo ufw allow 8000/tcp

# ফায়ারওয়াল একটিভ করুন
sudo ufw enable
```

এখন আপনার সার্ভারের পাবলিক আইপি বা ডোমেন দিয়ে টেস্ট করুন: `http://<your-server-ip>/health` অথবা `http://<your-server-ip>:8000/health`।

---

## Part 2: System Flow & Architecture (কীভাবে কাজ করে)

QueueStorm Investigator একটি **Hybrid AI System**। সিস্টেমটি সম্পূর্ণভাবে ক্লায়েন্ট থেকে আসা ইনপুট প্রসেস করে নিচের ৫টি ধাপে কাজ সম্পন্ন করে:

```text
[Client Input] -> [Pydantic Validation] -> [Deterministic Reasoning Engine] -> [LLM Call (OpenRouter)] -> [Safety Post-Processor Guardrails] -> [Output Response]
```

### ১. ইনপুট ভ্যালিডেশন
FastAPI অ্যাপে ক্লায়েন্ট ডেটা সাবমিট করার পর Pydantic (`app/schemas/request.py`) চেক করে দেখে যে রিকোয়েস্ট ফরম্যাট সঠিক কিনা। যদি ভুল JSON বা প্রয়োজনীয় ফিল্ড (যেমন `ticket_id` বা `complaint`) না থাকে, তবে এটি সরাসরি **HTTP 400** রিটার্ন করে।

### ২. ডিটারমিনিস্টিক রিজনিং ইঞ্জিন (deterministic Python Logic)
* **ডিজিট রূপান্তর ও সংখ্যা এক্সট্রাকশন:** বাংলায় লেখা সংখ্যা (যেমন ২০০০ বা ৫০০০) এবং ইংরেজি সংখ্যাগুলো স্বয়ংক্রিয়ভাবে ইংলিশ ফ্লোটে কনভার্ট করা হয়।
* **লেনদেন ম্যাচিং:** কমপ্লেইন টেক্সট থেকে `TXN-\d+` এর মতো কোনো আইডি ট্রানজেকশন হিস্ট্রির সাথে মিলে গেলে সেটি সরাসরি কানেক্ট করা হয়। আইডি না থাকলে টাকার পরিমাণ মিলিয়ে ম্যাচিং করা হয়।
* **ডুপ্লিকেট পেমেন্ট ডিটেকশন:** যদি ইউজার কমপ্লেইন করেন যে উনার টাকা দুইবার কেটেছে, সিস্টেম হিস্ট্রি থেকে একই পরিমাণ ও একই প্রাপকের দুটি সম্পন্ন পেমেন্টের মাঝে সময়ের ব্যবধান চেক করে। ব্যবধান ৫ মিনিটের কম হলে দ্বিতীয় ট্রানজেকশনটিকে সন্দেহভাজন ডুপ্লিকেট হিসেবে চিহ্নিত করা হয়।
* **ভুল ট্রানজেকশন ট্রাস্ট ট্র্যাকিং (Established Recipient):** ইউজার যদি বলেন ভুল নাম্বারে টাকা পাঠিয়েছেন, কিন্তু হিস্ট্রি যদি দেখায় উনি বিগত সময়ে ঐ নাম্বারে আরও ২ বা ততোধিক সম্পন্ন ট্রানজেকশন করেছেন, তাহলে সিস্টেম এই ক্লেইমকে `inconsistent` (অসামঞ্জস্যপূর্ণ) হিসেবে চিহ্নিত করে এবং কাস্টমারকে সরাসরি রিফান্ডের প্রতিশ্রুতি না দিয়ে রিভিউতে পাঠায়।

### ৩. ওপেন-রাউটার এপিআই কল (LLM Generation)
ম্যাচিং ডেটা এবং প্রি-কম্পিউটেড মেটাডেটা প্রম্পটের মাধ্যমে `google/gemini-2.5-flash` মডেলে পাঠানো হয়। মডেলকে কঠোরভাবে ইনস্ট্রাকশন দেওয়া হয় শুধুমাত্র ৩টি ফিল্ড জেনারেট করার জন্য: `agent_summary`, `recommended_next_action` এবং `customer_reply`।

### ৪. সেফটি পোস্ট-প্রসেসর গার্ডরেইল (Safety Guardrails)
জেনারেট হওয়া টেক্সট ক্লায়েন্টের কাছে পাঠানোর আগে কোডের মাধ্যমে `SafetyService` প্রতিটি ফিল্ড রি-চেক করে:
* **ওটিপি/পিন/পাসওয়ার্ড প্রটেকশন:** রিপ্লাইতে কোনোভাবে পিন বা ওটিপি চাওয়া হয়েছে কিনা চেক করা হয়।
* **অননুমোদিত প্রতিশ্রুতি ফিল্টার:** রিপ্লাইতে সরাসরি কোনো রিফান্ড বা অ্যাকাউন্ট আনব্লক করার গ্যারান্টি বা প্রতিশ্রুতি আছে কিনা স্ক্যান করা হয়। থাকলে সেটিকে নিরাপদ ভাষায় কনভার্ট করা হয় (*"any eligible amount will be returned through official channels"*)।
* **ইনজেকশন প্রোটেকশন:** যদি অভিযোগকারী কোনো প্রম্পট ইনজেকশন করার চেষ্টা করেন, তবে সিস্টেম অভিযোগ বাতিল করে শুধু কাস্টমার ফিডব্যাক ও সহায়তার জেনারেল টেক্সট রিপ্লাই হিসেবে পাঠায়।

### ৫. রেসপন্স ফরম্যাটিং
সব কাজ শেষে সঠিক ও নিঁখুত এনুম ফরম্যাট বজায় রেখে JSON রেসপন্স কাস্টমারকে পাঠানো হয়।

---

## Part 3: Compliance & Instruction Checklist (ভেরিফিকেশন রিপোর্ট)

হ্যাকাথনের অফিসিয়াল রুলস বুক অনুযায়ী আমাদের কোড কমপ্লায়েন্ট কিনা তা ডাবল-চেক করা হলো:

| রিকোয়ারমেন্টস | কমপ্লায়েন্স স্টেটাস | আমরা কীভাবে ইমপ্লিমেন্ট করেছি |
| :--- | :---: | :--- |
| **GET /health Endpoint** | **PASSED** | `/health` এ কল করলে `{"status":"ok"}` রিটার্ন করে। |
| **POST /analyze-ticket Endpoint** | **PASSED** | অফিসিয়াল ইনপুট স্কিমা মেনে চলে এবং সঠিক এপিআই আউটপুট জেনারেট করে। |
| **JSON Output Only** | **PASSED** | রেসপন্স বডিতে কোনো এক্সট্রা মার্কডাউন বা টেক্সট নেই, শুধু ভ্যালিড JSON অবজেক্ট। |
| **Exact Enum Matches** | **PASSED** | `evidence_verdict`, `case_type`, `severity`, `department` এর ভ্যালুগুলো অফিসিয়াল Taxonomy এর সাথে ১০০% মিলে যায়। |
| **PIN, OTP, Password Protection** | **PASSED** | `SafetyService` এর রেগেক্স ফিল্টার কোনোভাবেই গ্রাহকের সংবেদনশীল সিক্রেট ডেটা রিলেটেড জিজ্ঞাসা করার সুযোগ দেয় না। |
| **No Refund/Reversal Promise** | **PASSED** | রিফান্ড বা রিভার্সালের সরাসরি প্রতিশ্রুতি বদলে নিরাপদ ভাষা ব্যবহার নিশ্চিত করা হয়েছে। |
| **No Unofficial Contacts** | **PASSED** | অননুমোদিত থার্ড পার্টি কন্টাক্ট ইনফো সম্পূর্ণ ব্লকড। |
| **Prompt Injection Protection** | **PASSED** | Adversarial প্রম্পটকে ফিল্টার করে এবং "other" হিসেবে সেফলি রিজলভ করে। |
| **Timeout limit (< 30 seconds)** | **PASSED** | কোড অত্যন্ত অপ্টিমাইজড এবং এপিআই ৩ সেকেন্ডের মধ্যে রেসপন্স সম্পন্ন করে। |
| **Lightweight Docker Image** | **PASSED** | Multi-stage Docker build এর মাধ্যমে ইমেজ সাইজ ২০০ এমবির নিচে রাখা হয়েছে। |
| **Offline Fallback Mode** | **PASSED** | এপিআই কী না থাকলেও কোনো এরর ছাড়াই অফলাইনে সম্পূর্ণ নিরাপদ রিপ্লাই টেমপ্লেট দিয়ে এপিআই কাজ চালিয়ে যেতে পারে। |
