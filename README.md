# Sipa: Kanto Clicker 🇵🇭
### *Eskinita Rhythm & Precision Arcade*

[![Play in Browser](https://img.shields.io/badge/🎮_Play_Live-GitHub_Pages-FFCC00?style=for-the-badge&logo=github&logoColor=black)](https://regieorojr09-collab.github.io/sipa-kanto-clicker/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pygame-CE 2.5+](https://img.shields.io/badge/Pygame--CE-2.5.8-E10098?style=for-the-badge&logo=pygame&logoColor=white)](https://pyga.me/)
[![WebAssembly](https://img.shields.io/badge/WebAssembly-Pygbag-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)](https://pygame-web.github.io/)
[![CI/CD Deployment](https://img.shields.io/badge/Deploy-GitHub_Pages_Workflow-2EA44F?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/regieorojr09-collab/sipa-kanto-clicker/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

> **Play Instantly with Zero Installation:** [https://regieorojr09-collab.github.io/sipa-kanto-clicker/](https://regieorojr09-collab.github.io/sipa-kanto-clicker/)  
> *Fully compatible with modern desktop browsers (Chrome, Edge, Firefox) including Incognito & Private browsing windows.*

---

## 📖 About the Game

**Sipa: Kanto Clicker** is a vibrant, browser-playable 2D arcade rhythm game inspired by **Sipa** — the historic traditional Philippine national street sport (*Laro ng Lahi*). In neighborhoods across the Philippines, children and street ballers gather on asphalt street corners (*kanto*) and narrow alleys (*eskinita*) to kick a lead washer adorned with colorful plastic straw tassels, keeping it airborne using feet, knees, and elbows.

Blending the rhythm and precision mechanics of classic arcade circle-clickers (*Osu!*, *Elite Beat Agents*) with the rich nostalgia and humor of Philippine street culture, you test your reflexes against **Taya**, the neighborhood challenger standing on the sideline. Keep your kicks in rhythm, maintain your combo streak, survive escalating wind, speed, and chaos modifiers as Taya's **Pikon Meter** surges toward rage mode, and claim your street title as **Hari ng Kanto**!

### 🌟 Cultural Highlights
- **Authentic Kanto Atmosphere:** Dynamic parallax-scrolling scenery featuring a vibrant sari-sari store with hanging snack sachets, utility poles with crisscrossing wires, a parked Philippine tricycle, and chalk-drawn court lines.
- **Iconic Street Avatar:** Play as *Ikaw!* dressed in authentic Filipino street attire — white sando (tank top), red basketball shorts with a gold stripe, and trusty chinelas (flip-flops).
- **Authentic Street Animations:** 7 procedurally animated player states including **Paa** (inside foot kick for low hits), **Tuhod** (knee bump for mid-height hits), **Siko** (downward elbow rebound for high hits), and miss stumbles.
- **Sideline Banter:** Taya reacts in real-time with authentic Tagalog voice-callout balloons, cheering, taunting, and trembling in rage as your combo grows.

---

## 🕹️ Controls Reference

Play using either **Mouse**, **Keyboard**, or a hybrid setup. A responsive custom crosshair cursor assists with precision aiming.

| Action | Mouse | Keyboard |
| :--- | :--- | :--- |
| **Kick / Hit Target** | **Left Click** on Approach Ring | **`Z`** or **`X`** key |
| **Pause / Unpause Game** | Click **PAUSE** Button (top-left) | **`ESC`** key |
| **Resume (while paused)** | Click **ITULOY (Resume)** | **`ESC`** or **`SPACE`** |
| **Restart Round (paused)** | Click **UMULIT (Restart)** | **`R`** key |
| **Quit to Title (paused)** | Click **LUMABAS (Quit)** | **`Q`** key |
| **Select Difficulty (Title)** | Click Difficulty Tab | **`1`**, **`2`**, **`3`**, or **`4`** key |
| **Start / Unlock Audio** | Click **▶ CLICK TO PLAY** | **`SPACE`**, **`ENTER`**, **`Z`**, or **`X`** |
| **Play Again (Results)** | Click **ULITIN (Play Again)** | **`SPACE`** or **`ENTER`** |
| **Return to Menu (Results)** | Click **MENU** | **`ESC`** or **`Q`** |

> **Pro-Tip:** In high-speed modes and during *Dalawa* (Double Target) spawns, alternate pressing **`Z`** and **`X`** while aiming with the mouse for maximum accuracy and speed!

---

## 🎯 Gameplay Mechanics & Rules

Each round consists of **15 serves** launched by Taya from the sideline. As each sipa arcs across the court and descends toward the chalk kick zone, an approach ring converges toward the target center. Time your kick at the exact moment of overlap!

### ⏱️ Hit Timing & Judgments

Hits are evaluated in milliseconds (ms) of deviation from the perfect concentric ring overlap:

| Judgment | Timing Window | Base Points | Visual & Sound Effects |
| :---: | :---: | :---: | :--- |
| **Swak!** | **±25 ms** | **300 pts** | Perfect hit! Golden shockwave ripples, particle starbursts, crisp metallic clink + deep shoe thud. |
| **Puwede** | **±70 ms** | **100 pts** | Acceptable hit. Cyan circular rings and moderate particle burst. |
| **Daplis** | **±120 ms** | **50 pts** | Barely grazed. Weak puff of dust; Taya mocks your technique. |
| **Bagsak!** | **> 120 ms / Miss** | **0 pts** | Dropped! Sipa hits the asphalt with a hollow bounce, combo resets to 0, red screen shake. |

---

### 🧮 Dynamic Scoring Formula

Score rewards consistency and precision under pressure:

$$\text{Points} = \text{BasePoints} \times \left(1 + \frac{\min(\text{Combo}, 100)}{25}\right) \times \text{DifficultyMultiplier}$$

- Maintaining combos multiplies your point yield exponentially up to a 100-streak ($5.0\times$ combo multiplier).
- A 50-combo *Swak!* on **Mahirap** yields significantly more points than single hits on easy modes!

---

### 😡 The Pikon Meter (Taya's Rage Gauge)

The **Pikon Meter** is an interactive annoyance gauge displayed at the top of the screen tracking Taya's frustration. The better you play, the angrier Taya becomes:

- **+5.0%** for each *Swak!* hit
- **+3.0%** for each *Puwede* hit
- **+1.0%** for each *Daplis* hit
- **1.5× multiplier** on Pikon gains when your combo is **10 or higher**
- **-15.0%** drop immediately on a miss (*Bagsak!*)
- Natural decay of **2% per second** during pauses or after 3 seconds of inactivity

#### Pikon Gauge Status Tiers
| Range | Color | Mood | Challenger Behavior |
| :---: | :---: | :---: | :--- |
| **0% – 29%** | **Emerald Green** | Calm / Observing | Taya stands with crossed arms, watching casually. |
| **30% – 49%** | **Sunshine Yellow** | Annoyed | Taya starts muttering street callouts (*"Tira na!"*, *"Salo!"*). |
| **50% – 79%** | **Tricycle Orange** | Frustrated | Taya gestures excitedly, quickening serves. |
| **80% – 100%** | **Pulsing Crimson** | **PIKON RAGE!** | Taya trembles with clenched fists, shouts rage dialogue (*"Pikon na 'ko ah!"*), BGM tempo surges to 152 BPM! |

---

### ⚡ Dynamic Gameplay Modifiers

As the Pikon Meter climbs, Taya triggers street modifiers that alter physics and timing in real-time:

1. 💨 **Hangin (Lateral Wind — $\ge 30\%$ Pikon):** Strong wind pushes the sipa sideways, curving its trajectory and testing your spatial prediction.
2. ⏩ **Bilis (Speed Up — $\ge 50\%$ Pikon):** Approach rings contract 20% faster, shrinking your reaction window.
3. ✌️ **Dalawa (Double Target — $\ge 65\%$ Pikon):** A secondary bonus quick-ring spawns alongside the main target. Hit both for massive points!
4. 🔥 **Pikon Rage ($\ge 80\%$ Pikon):** Rings shrink 30% faster, wind gusts intensify, and music shifts to high-octane tempo.
5. 🌀 **Loko-Loko (Chaos Jitter — $\ge 95\%$ Pikon):** Targets spawn with chaotic spatial displacement away from standard landing predictions.

---

## 🏆 Street Ranks & Grading System

Your final round performance is evaluated based on **Overall Accuracy %**, awarded on a festive jeepney-style badge with diamond studs and banderitas:

| Grade | Accuracy | Street Title | Cultural Meaning |
| :---: | :---: | :---: | :--- |
| **S** | **$\ge 95\%$** | **Hari ng Kanto** | *King of the Street Corner* — Legendary street precision with celebratory gold sparkles! |
| **A** | **$\ge 85\%$** | **Beterano** | *Seasoned Veteran* — Master of the eskinita with sparkling accents. |
| **B** | **$\ge 75\%$** | **Marunong** | *Skilled Player* — Knows the rhythm and holds their own. |
| **C** | **$\ge 60\%$** | **Bagito** | *Newbie / Beginner* — Still learning the kick timing. |
| **F** | **$< 60\%$** | **Kulelat** | *Dead Last* — Missed too many serves; Taya laughs you off the court! |

---

## 🎚️ Difficulty Tiers

Select your challenge on the Title Screen or switch via number keys `1`–`4`:

| Difficulty | Score Mult | Approach Rate (AR) | Pikon Rate | Starting Modifiers |
| :--- | :---: | :---: | :---: | :--- |
| **Madali** (Easy) | **1.0×** | AR 5.0 (Relaxed) | 0.8× (Slow) | None (Standard practice) |
| **Sakto** (Normal) | **1.5×** | AR 6.0 (Standard) | 1.0× (Normal) | Standard progression |
| **Mahirap** (Hard) | **2.5×** | AR 7.5 (Fast) | 1.3× (Fast) | Constant *Hangin* (Wind) active immediately |
| **Pikon Mode** (Extreme) | **4.0×** | AR 9.0 (Blazing) | 1.6× (Aggressive) | All modifiers active from Serve 1! |

---

## 📚 Filipino Street Word Glossary

*Sipa: Kanto Clicker* authentically celebrates Filipino street terminology:

| Filipino Word | Pronunciation | English Meaning | In-Game Context |
| :--- | :--- | :--- | :--- |
| **Sipa** | *SEE-pah* | Kick / The traditional game | The sport and game title |
| **Kanto** | *KAHN-toh* | Street corner | The neighborhood venue |
| **Eskinita** | *es-kee-NEE-tah* | Narrow alley | Street court backdrop |
| **Sari-sari** | *SAH-ree SAH-ree* | Variety corner store | Iconic background building |
| **Taya** | *TAH-yah* | "It" / Challenger | Sideline opponent / server |
| **Swak!** | *SWAHK* | Perfect fit / Bullseye | Perfect timing judgment (±25ms) |
| **Puwede** | *poo-WEH-deh* | Acceptable / Will do | Good timing judgment (±70ms) |
| **Daplis** | *DAHP-lis* | Grazed / Barely touched | OK timing judgment (±120ms) |
| **Bagsak!** | *bahg-SAHK* | Dropped / Failed | Miss judgment (>120ms) |
| **Pikon** | *pee-KOHN* | Easily irritated / Sore loser | Rage meter and extreme difficulty |
| **Madali** | *mah-DAH-lee* | Easy | Beginner difficulty tier |
| **Sakto** | *sahk-TOH* | Just right / Exact | Normal difficulty tier |
| **Mahirap** | *mah-hee-RAHP* | Difficult / Hard | Hard difficulty tier |
| **Hangin** | *HAHNG-in* | Wind | Lateral drift modifier |
| **Bilis** | *BIH-lis* | Speed / Fast | Fast-approach modifier |
| **Dalawa** | *dah-LAH-wah* | Two / Double | Double approach ring modifier |
| **Loko-Loko** | *LOH-koh LOH-koh* | Crazy / Chaotic | Spatial jitter modifier |
| **Paa** | *PAH-ah* | Foot | Inside-foot kick animation |
| **Tuhod** | *TOO-hod* | Knee | Knee-bump animation |
| **Siko** | *SEE-koh* | Elbow | Elbow-rebound animation |
| **Hari** | *HAH-ree* | King | Rank S (*Hari ng Kanto*) |
| **Beterano** | *beh-teh-RAH-noh* | Veteran | Rank A title |
| **Marunong** | *mah-ROO-nong* | Skilled / Capable | Rank B title |
| **Bagito** | *bah-GEE-toh* | Newcomer / Rookie | Rank C title |
| **Kulelat** | *koo-LEH-lat* | Dead last / Bottom | Rank F title |
| **Simulan** | *see-MOO-lan* | Start / Begin | Start button text |
| **Hinto** | *HIN-toh* | Stop / Pause | Pause menu title |
| **Ituloy** | *ee-TOO-loy* | Continue / Resume | Resume option |
| **Umulit** | *oo-MOO-lit* | Restart / Repeat | Restart round option |
| **Lumabas** | *loo-MAH-bahs* | Exit / Leave | Quit to menu option |
| **Tira** | *TEE-rah* | Serve / Launch | Taya callout |
| **Salo** | *SAH-loh* | Catch / Receive | Taya serve callout |
| **Chinelas** | *chee-NEH-lahs* | Flip-flops / Slippers | Avatar footwear |
| **Sando** | *SAHN-doh* | Tank top / Undershirt | Avatar jersey |

---

## 🏗️ Technical Architecture & Stack

*Sipa: Kanto Clicker* is engineered with zero external asset dependencies, ensuring ultra-fast loading and cross-platform resilience:

```
sipa-kanto-clicker/
├── core/
│   ├── engine.py          # Fixed 1280x720 canvas scaler & letterbox viewport manager
│   ├── events.py          # Pub/Sub EventBus architecture
│   └── settings.py        # Display, color palettes, and global constants
├── entities/
│   ├── avatar.py          # Procedural 7-state player character & kick animations
│   ├── sipa.py            # Physics projectile with parabolas, shadow & particle tassels
│   └── taya.py            # Sideline AI opponent, speech balloons & rage gestures
├── scenes/
│   ├── scene_manager.py   # State-machine scene stack with smooth alpha transitions
│   ├── title_scene.py     # Attract screen, difficulty selector & WebAudio unlock
│   ├── play_scene.py      # Core gameplay loop, HUD orchestrator & serve director
│   └── results_scene.py   # Accuracy breakdown, street rank & celebratory VFX
├── systems/
│   ├── audio.py           # Pure Python procedural PCM synthesizer (BGM, SFX, cheers)
│   ├── difficulty.py      # AR scaling, wind physics & modifier state-machine
│   ├── hit_system.py      # Circle geometry & millisecond timing judgment engine
│   └── scoring.py         # Dynamic multiplier calculator & rank grader
├── ui/
│   ├── fx.py              # Floating text, shockwave ripples & particle emitters
│   ├── hud.py             # Accuracy meter, Pikon gauge & modifier tags
│   ├── menus.py           # PauseOverlay, Button widgets & dialogs
│   └── scenery.py         # Parallax street backdrop, sari-sari store & tricycle
├── .github/workflows/
│   └── deploy.yml         # Automated GitHub Actions deployment pipeline
├── default.tmpl           # Custom Pygbag template with Incognito fallback & cache control
├── pygbag.ini             # Pygbag packaging exclusions
└── main.py                # Asynchronous WebAssembly entry point
```

### Highlights:
- **Zero External Media Assets:** 100% of visual assets (characters, sari-sari store, tricycle, sipa tassels, chalk courts) are procedurally drawn with Pygame 2D routines.
- **Pure Python Audio Synthesis:** All sounds (metallic washer clink, shoe thuds, miss stumbles, crowd cheers, arpeggiated chimes, and 120/152 BPM looping chiptune BGM tracks) are synthesized mathematically at runtime from raw 16-bit PCM arrays using `pygame.mixer.Sound(buffer=data)`.
- **Responsive Resolution Letterboxing:** The game calculates in a fixed $1280 \times 720$ logical space, dynamically letterboxing or pillarboxing onto any browser viewport or window resolution while accurately transforming mouse clicks.
- **Asynchronous WebAssembly Loop:** `await asyncio.sleep(0)` yields control back to the browser on every frame, eliminating UI thread locking.
- **Browser & Incognito Resilience:** In-memory fallback mock prevents crashes under strict third-party storage restrictions or private browsing.

---

## 💻 Local Setup & Development

### Prerequisites
- Python 3.11, 3.12, or 3.14
- `pip` package manager

### 1. Installation
Clone the repository and install required packages:
```bash
git clone https://github.com/regieorojr09-collab/sipa-kanto-clicker.git
cd sipa-kanto-clicker

# Install dependencies
pip install pygame-ce pygbag
```

### 2. Run Desktop Version
Launch the native desktop window ($1280 \times 720$):
```bash
python main.py
```

### 3. Run WebAssembly Test Server Locally
Test the in-browser WebAssembly build locally with live reloading:
```bash
python -m pygbag .
```
Then open [http://localhost:8000](http://localhost:8000) in your web browser.

### 4. Build Static Web Distribution
Compile the standalone WebAssembly package into `build/web/`:
```bash
# Windows
build_web.bat

# Linux / macOS
chmod +x build_web.sh
./build_web.sh

# Or directly via Python
python -m pygbag --build .
```

---

## 🚀 GitHub Pages Deployment Setup

Automated deployment is powered by GitHub Actions ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)).

To ensure your GitHub repository automatically deploys:

1. Open your repository on GitHub:  
   `https://github.com/regieorojr09-collab/sipa-kanto-clicker`
2. Click **Settings** (top navigation tab).
3. In the left sidebar under *Code and automation*, click **Pages**.
4. Under **Build and deployment > Source**, select:  
   👉 **`GitHub Actions`** *(do NOT select "Deploy from a branch")*.
5. (Optional) Under **Settings > Actions > General > Workflow permissions**, confirm that permissions are set to allow workflows to submit deployments.
6. Push a commit to the `main` branch (or run manually via **Actions > Build & Deploy to GitHub Pages > Run workflow**).
7. Once the workflow completes, the game will be live at:  
   👉 **`https://regieorojr09-collab.github.io/sipa-kanto-clicker/`**

---

## 📜 License & Credits

- **Game Design & Code:** Antigravity AI & Regie Oro Jr.
- **Inspiration:** The timeless street games of the Philippines (*Laro ng Lahi*).
- **License:** Released under the [MIT License](LICENSE).

*Salamat sa paglalaro! Keep the sipa airborne!* 🇵🇭
