# SAUDIA AUTOMATION — LIVE WORKING FLOW

> **Ye document kya hai?**
> Ye ek "bridge" hai — aap (human) aur AI ke beech.
> Aap simple language mein apna goal likhein, AI isko padhke seedha sahi jagah code update karega.
> Har code change ke baad ye document bhi update hoga — hamesha sync mein rahega.

---

## MASTER FLOW (Poora Process — Ek Nazar Mein)

```mermaid
flowchart TD
    START(["START - Script Shuru"])
    START --> H1{"Phone\nConnected?"}
    H1 -->|Yes| H2{"Brave\nBrowser\nReady?"}
    H1 -->|No| ERR1["STOP\nPhone check karo"]
    H2 -->|Yes| S1["Excel se\nPassenger List\nPadho"]
    H2 -->|No| ERR2["STOP\nBrave start karo"]

    S1 --> LOOP_START(["LOOP START\nHar Passenger\nKe Liye"])

    LOOP_START --> G1{"Gmail\nSwitch\nZaroori?"}
    G1 -->|Haan, naya Gmail| S2["PAUSE\nGmail switch karo\nready.txt banao"]
    G1 -->|Nahi, same Gmail| S3

    S2 --> S3["App Fresh Start\nForce Stop + Relaunch"]

    S3 --> S4["AlFursan Tab\nClick karo"]
    S4 --> S5["Login Button\nClick karo\nTop Right"]

    S5 --> S6["FFN Type karo"]
    S6 --> S6B["Password Type karo"]
    S6B --> S6C["Keyboard Hide"]

    S6C --> S7["Login Submit\nButton Click\nTimestamp Save"]

    S7 --> S8(["OTP FETCH\nGmail Smart Check\nSee Detail Below"])

    S8 -->|Fresh OTP Mila| S9["OTP Type\nPhone Mein\n6 digit char-by-char"]
    S8 -->|Timeout| FAIL1["FAIL\nOTP nahi mila"]

    S9 --> WAIT["5 Sec Wait"]
    WAIT --> S10{"Screen\nKya Dikhi?"}

    S10 -->|Verify Mobile\nNumber| S11["App Restart\nBypass karo"]
    S10 -->|Dashboard\nDirect| S12
    S10 -->|Still OTP\nScreen| FAIL2["FAIL\nOTP galat tha"]

    S11 --> WAIT2["3 Sec Wait"]
    WAIT2 --> S12{"Dashboard\nVerify?"}

    S12 -->|Home/Hi/Miles\ndikha| SUCCESS["SUCCESS\nLogin Ho Gaya!"]
    S12 -->|Nahi dikha| FAIL3["FAIL\nDashboard nahi mila"]

    SUCCESS --> S13["Excel Update\nStatus = Success"]
    S13 --> STOP_OK(["STOP\nScript Ruka\nAs Requested"])

    FAIL1 --> FAIL_HANDLER
    FAIL2 --> FAIL_HANDLER
    FAIL3 --> FAIL_HANDLER["Excel Update\nStatus = Failed"]
    FAIL_HANDLER --> S14["Screenshot\nSave karo"]
    S14 --> LOOP_START

    style START fill:#4CAF50,color:white,stroke:#388E3C,stroke-width:2px
    style STOP_OK fill:#2196F3,color:white,stroke:#1565C0,stroke-width:2px
    style ERR1 fill:#f44336,color:white
    style ERR2 fill:#f44336,color:white
    style FAIL1 fill:#FF5722,color:white
    style FAIL2 fill:#FF5722,color:white
    style FAIL3 fill:#FF5722,color:white
    style SUCCESS fill:#4CAF50,color:white,stroke:#388E3C,stroke-width:3px
    style S8 fill:#9C27B0,color:white,stroke:#7B1FA2,stroke-width:2px
    style S2 fill:#FF9800,color:white
    style S7 fill:#E91E63,color:white
    style S11 fill:#00BCD4,color:white
    style LOOP_START fill:#607D8B,color:white
```

---

## OTP FETCH — Detail Flow (S8 Ka Andar)

```mermaid
flowchart TD
    OTP_START(["OTP Fetch Start"])
    OTP_START --> CDP["Brave se CDP\nConnection banao"]
    CDP --> GMAIL["Gmail Inbox\nNavigate karo"]
    GMAIL --> LOGIN_CHK{"Gmail\nLogged In?"}
    LOGIN_CHK -->|No| GMAIL_ERR["STOP\nGmail login nahi hai"]
    LOGIN_CHK -->|Yes| SEARCH["Search karo:\nis:unread\nsubject:Retrieve AlFursan OTP\nnewer_than:1h"]

    SEARCH --> FOUND{"Email\nMili?"}
    FOUND -->|No| WAIT_RELOAD
    FOUND -->|Yes| OPEN["Email Kholo"]

    OPEN --> TIME_CHECK["Email ka\nTimestamp Nikalo\n.g3 element se"]
    TIME_CHECK --> FRESH{"Timestamp >\nOTP Trigger\nTime?"}

    FRESH -->|FRESH - Nayi Hai| EXTRACT["6 Digit OTP\nRegex se Nikalo"]
    FRESH -->|STALE - Purani Hai| WAIT_RELOAD

    EXTRACT --> DELETE["Email Delete\nTry karo"]
    DELETE --> OTP_SUCCESS(["OTP Return - SUCCESS"])

    WAIT_RELOAD["15 Sec Wait\n+ Page Reload"] --> TIMEOUT{"120 Sec\nHo Gaye?"}
    TIMEOUT -->|No| SEARCH
    TIMEOUT -->|Yes| OTP_FAIL(["Timeout\nOTP nahi mila"])

    style OTP_START fill:#9C27B0,color:white
    style OTP_SUCCESS fill:#4CAF50,color:white
    style OTP_FAIL fill:#f44336,color:white
    style FRESH fill:#FF9800,color:white
    style WAIT_RELOAD fill:#FF9800,color:white
    style GMAIL_ERR fill:#f44336,color:white
    style SEARCH fill:#2196F3,color:white
    style TIME_CHECK fill:#E91E63,color:white
```

---

## LOGIN FORM — Detail Flow (S5-S7 Ka Andar)

```mermaid
flowchart LR
    FORM_START(["Login Form\nOpen Hua"]) --> POLL_FIELDS["Poll karo\n2 EditText\nmilne tak\nMax 8 sec"]
    POLL_FIELDS --> FFN["FFN Field\nTap + Type\nADB Char-by-char"]
    FFN --> PASS["Password Field\nTap + Type\nADB Char-by-char"]
    PASS --> KB_HIDE["ESCAPE Key\nKeyboard Hide"]
    KB_HIDE --> FIND_BTN["Login Button\nDhundho"]
    FIND_BTN --> BTN_CHK{"Exact Match:\ncontent_desc\n= Login Button?"}
    BTN_CHK -->|Yes| CLICK_BTN["Click karo"]
    BTN_CHK -->|No| FUZZY["Fuzzy Search\nGmail/Apple\nexclude karke"]
    FUZZY --> CLICK_BTN
    CLICK_BTN --> TIMESTAMP["Timestamp\nSave karo\ndatetime.now"]
    TIMESTAMP --> FORM_END(["OTP Screen\nAayegi Ab"])

    style FORM_START fill:#2196F3,color:white
    style FORM_END fill:#9C27B0,color:white
    style TIMESTAMP fill:#E91E63,color:white
    style CLICK_BTN fill:#4CAF50,color:white
```

---

## VERIFY BYPASS — Detail Flow (S10-S12 Ka Andar)

```mermaid
flowchart TD
    OTP_DONE(["OTP Type\nHo Gaya"]) --> WAIT_5["5 Sec Wait"]
    WAIT_5 --> DUMP["Screen Dump\nLo"]
    DUMP --> CHECK{"Screen Mein\nKya Dikha?"}

    CHECK -->|verify mobile number| PATH_A["OTP Accept Hua!\nLekin Verify Screen\nBlock Kar Rahi Hai"]
    CHECK -->|verification / otp| PATH_B["Abhi Bhi\nOTP Screen\nOTP Galat Tha"]
    CHECK -->|Kuch Aur| PATH_C["Unknown Screen\nDashboard Check\nTry Karo"]

    PATH_A --> RESTART["Force Stop\n+ Relaunch\n+ 3 Sec Wait"]
    RESTART --> DASH_CHECK{"Dashboard\nKeywords\nMilein?"}
    DASH_CHECK -->|Hi/Home/Miles| WIN(["SUCCESS!"])
    DASH_CHECK -->|Nahi| LOSE(["FAIL"])

    PATH_C --> DASH_CHECK2{"Dashboard\nKeywords?"}
    DASH_CHECK2 -->|Yes| WIN
    DASH_CHECK2 -->|No| LOSE

    PATH_B --> LOSE

    style OTP_DONE fill:#9C27B0,color:white
    style WIN fill:#4CAF50,color:white,stroke:#388E3C,stroke-width:3px
    style LOSE fill:#f44336,color:white
    style PATH_A fill:#00BCD4,color:white
    style RESTART fill:#FF9800,color:white
```

---

## Step - Code Mapping (Quick Reference)

| Step | Kya Hota Hai | Code File | Line Numbers |
|------|-------------|-----------|--------------|
| S0 | Phone + Browser health check | main.py | 67-81 |
| S1 | Excel se passenger list | main.py | 83-95 |
| S2 | Gmail switch + ready.txt wait | main.py | 113-125 |
| S3 | App restart (force stop + launch) | phone_control.py | 179-188 |
| S4 | AlFursan tab find + click | phone_control.py | 212-231 |
| S5 | Login button find + click | phone_control.py | 233-251 |
| S6 | FFN + Password type | phone_control.py | 253-280 |
| S7 | Login submit + timestamp save | phone_control.py | 282-329 |
| S8 | OTP fetch (Gmail smart check) | gmail_otp.py | 57-210 |
| S9 | OTP type in phone | phone_control.py | 134-165 |
| S10 | Screen check after OTP | main.py | 149-186 |
| S11 | App restart (verify bypass) | main.py | 153-158 |
| S12 | Dashboard verify | main.py | 39-60 |
| S13 | Excel update + stop | main.py | 162-168 |
| S14 | Error handler + screenshot | main.py | 191-199 |

---

## Change Request Guide

Aapko code ki koi tension nahi leni hai. Bas neeche diye format mein apni baat likhein:

**Type 1:** Step ke beech kuch add karna hai
> "S7 ke baad ek popup aata hai, usko dismiss karna hai"

**Type 2:** Goal batana hai
> "Goal: Dashboard se miles ka number chahiye Excel mein"

**Type 3:** Existing step modify karna hai
> "S6 mein password ke baad 1 second wait kaafi hai"

---

## Sync Rule

Ye document hamesha code ke saath sync mein rahega.
Har approved code change ke baad:
1. Code update hoga
2. FLOW.md ka relevant step update hoga
3. Mermaid graphs update honge
4. Step - Code mapping table update hogi

---

*Last Updated: 2026-07-05 | Version: 2.1 | Status: LIVE and VERIFIED*
